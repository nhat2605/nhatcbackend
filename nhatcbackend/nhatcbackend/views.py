from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction, models
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import User, Account, Transaction
from .serializers import UserSerializer, AccountSerializer, FundTransferSerializer, TransactionSerializer, PasswordResetSerializer, AddTransferAccountSerializer, TransferAccountSerializer, TransferAccountListSerializer, UserTransferAccount, ExternalAccountSerializer

# Custom responses for better documentation
user_response_examples = {
    "application/json": {
        "id": 1,
        "username": "john_doe",
        "accounts": [
            {
                "id": 1,
                "account_number": "12345678",
                "account_type": "cheque",
                "balance": "1000.00"
            }
        ]
    }
}

account_response_examples = {
    "application/json": {
        "id": 1,
        "account_number": "12345678",
        "account_type": "cheque",
        "account_type_display": "Cheque",
        "balance": "1000.00"
    }
}

class UserCreateView(generics.CreateAPIView):
    """
    Create a new user account.
    
    This endpoint allows anyone to register a new user account.
    After registration, use the /api/token/ endpoint to obtain JWT tokens.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]  # Allow any user to register

class AccountListView(generics.ListCreateAPIView):
    """
    List user's accounts or create a new account.
    
    GET: Returns all accounts belonging to the authenticated user.
    POST: Creates a new account for the authenticated user.
    
    Account types available: 'cheque' or 'saving'
    
    **Balance Validation:**
    - Balance cannot be negative
    - Balance cannot exceed $10,000,000.00
    - Balance must have exactly 2 decimal places
    - Savings accounts require minimum $100.00 if setting initial balance
    """
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except ValidationError as e:
            # Convert Django ValidationError to DRF ValidationError
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))

class AccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific account.
    
    Users can only access their own accounts.
    
    **Balance Validation (for updates):**
    - Balance cannot be negative
    - Balance cannot exceed $10,000,000.00
    - Balance must have exactly 2 decimal places
    """
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        try:
            serializer.save()
        except ValidationError as e:
            # Convert Django ValidationError to DRF ValidationError
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))

class TransactionListView(generics.ListAPIView):
    """
    List all transactions for the authenticated user.
    
    Returns transactions where the user is either the sender or recipient.
    Transactions are ordered by creation date (newest first).
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_accounts = Account.objects.filter(user=self.request.user)
        return Transaction.objects.filter(
            models.Q(from_account__in=user_accounts) | 
            models.Q(to_account__in=user_accounts)
        ).order_by('-created_at')

@swagger_auto_schema(
    method='post',
    operation_description="""
    Transfer funds between accounts.
    
    This endpoint allows authenticated users to transfer money from their own account 
    to other accounts in the system. The transfer is atomic and will either complete 
    fully or not at all.
    
    **Requirements:**
    - User must be authenticated
    - Source account must belong to the authenticated user
    - Source account must have sufficient balance
    - Destination account must exist
    - Amount must be greater than 0
    
    **Account Type Restrictions:**
    - **Cheque Account**: Can transfer to any account (own or others)
    - **Savings Account**: Can ONLY transfer to your own cheque accounts
    
    **Process:**
    1. Validates the transfer request
    2. Checks account ownership and account type restrictions
    3. Checks account balance
    4. Performs atomic transfer (debit source, credit destination)
    5. Creates transaction record
    6. Returns transfer details
    """,
    request_body=FundTransferSerializer,
    security=[{'Bearer': []}],  # Require Bearer token authentication
    responses={
        200: openapi.Response(
            description="Transfer completed successfully",
            examples={
                "application/json": {
                    "message": "Transfer completed successfully",
                    "transaction_id": 123,
                    "from_account": "12345678",
                    "to_account": "87654321",
                    "amount": "100.00",
                    "new_balance": "900.00"
                }
            }
        ),
        400: openapi.Response(
            description="Bad request - validation errors, insufficient balance, or account type restrictions",
            examples={
                "application/json": {
                    "error": "Insufficient balance"
                }
            }
        ),
        401: openapi.Response(
            description="Authentication required",
            examples={
                "application/json": {
                    "detail": "Authentication credentials were not provided."
                }
            }
        ),
        404: openapi.Response(
            description="Account not found",
            examples={
                "application/json": {
                    "error": "Destination account not found"
                }
            }
        ),
        500: openapi.Response(
            description="Internal server error",
            examples={
                "application/json": {
                    "error": "Transfer failed: Database error"
                }
            }
        )
    },
    tags=['Transfers']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def fund_transfer(request):
    serializer = FundTransferSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    from_account_number = serializer.validated_data['from_account_number']
    to_account_number = serializer.validated_data['to_account_number']
    amount = serializer.validated_data['amount']
    description = serializer.validated_data.get('description', '')
    
    try:
        # Get the from account (must belong to the authenticated user)
        from_account = get_object_or_404(
            Account, 
            account_number=from_account_number, 
            user=request.user
        )
        
        # Get the to account (can belong to any user)
        try:
            to_account = Account.objects.get(account_number=to_account_number)
        except Account.DoesNotExist:
            return Response(
                {'error': 'Destination account not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Business rule: Savings accounts can only transfer to user's own cheque accounts
        if from_account.account_type == 'saving':
            # Check if destination is user's own cheque account
            if to_account.user != request.user:
                return Response(
                    {'error': 'Savings account funds can only be transferred to your own accounts'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            if to_account.account_type != 'cheque':
                return Response(
                    {'error': 'Savings account funds can only be transferred to your own cheque accounts'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check if user has sufficient balance
        if from_account.balance < amount:
            return Response(
                {'error': 'Insufficient balance'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Perform the transfer using database transaction
        with transaction.atomic():
            # Update balances
            from_account.balance -= amount
            to_account.balance += amount
            
            from_account.save()
            to_account.save()
            
            # Create transaction record
            transfer_transaction = Transaction.objects.create(
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                transaction_type='transfer',
                description=description or f'Transfer from {from_account_number} to {to_account_number}'
            )
        
        return Response({
            'message': 'Transfer completed successfully',
            'transaction_id': transfer_transaction.id,
            'from_account': from_account_number,
            'to_account': to_account_number,
            'amount': amount,
            'new_balance': from_account.balance
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Transfer failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="""
    Reset user password via email.
    
    This endpoint allows users to reset their password by providing their email address.
    A secure temporary password will be generated and sent to the user's email.
    
    **Process:**
    1. Validates the email address
    2. Checks if a user account exists with this email
    3. Generates a secure temporary password (12 characters with mixed case, numbers, and symbols)
    4. Updates the user's password in the database
    5. Sends the new password via email
    
    **Security Features:**
    - Uses cryptographically secure random password generation
    - Passwords contain uppercase, lowercase, numbers, and special characters
    - Email is sent from a secure system address
    - Old password is immediately invalidated
    
    **Note:** For development, emails are printed to the console. In production, configure SMTP settings.
    """,
    request_body=PasswordResetSerializer,
    responses={
        200: openapi.Response(
            description="Password reset email sent successfully",
            examples={
                "application/json": {
                    "message": "New password sent to your email address",
                    "email": "user@example.com"
                }
            }
        ),
        400: openapi.Response(
            description="Invalid email or user not found",
            examples={
                "application/json": {
                    "email": ["No account found with this email address"]
                }
            }
        ),
        500: openapi.Response(
            description="Email sending failed",
            examples={
                "application/json": {
                    "error": "Failed to send email: SMTP error"
                }
            }
        )
    },
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset(request):
    """
    Reset password via email
    """
    serializer = PasswordResetSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_description="""
    Get all accounts the user can transfer to.
    
    This endpoint returns a list of all accounts the user can transfer funds to,
    including their own accounts and any accounts they've added to their transfer list.
    
    **Returns:**
    - `user_accounts`: All accounts belonging to the authenticated user
    - `transfer_accounts`: All external accounts the user has added to their transfer list
    
    This provides a complete view of all available transfer destinations for the user.
    """,
    responses={
        200: openapi.Response(
            description="List of transfer accounts retrieved successfully",
            examples={
                "application/json": {
                    "user_accounts": [
                        {
                            "id": 1,
                            "account_number": "12345678",
                            "account_type": "cheque",
                            "account_type_display": "Cheque",
                            "balance": "1000.00"
                        }
                    ],
                    "transfer_accounts": [
                        {
                            "id": 1,
                            "account": {
                                "id": 2,
                                "account_number": "87654321",
                                "account_owner_username": "jane_doe"
                            },
                            "account_owner_username": "jane_doe",
                            "added_at": "2024-01-01T12:00:00Z"
                        }
                    ]
                }
            }
        ),
        401: openapi.Response(
            description="Authentication required",
            examples={
                "application/json": {
                    "detail": "Authentication credentials were not provided."
                }
            }
        )
    },
    tags=['Transfer Accounts']
)
@swagger_auto_schema(
    method='post',
    operation_description="""
    Add an account to the user's transfer list.
    
    This endpoint allows users to add an external account to their list of accounts
    they can transfer funds to. The account must exist in the system.
    
    **Requirements:**
    - Account number must be valid and exist in the system
    - User cannot add their own accounts (they're automatically available)
    - Duplicate entries are prevented
    
    **Process:**
    1. Validates the account number exists
    2. Checks the account doesn't belong to the current user
    3. Adds the account to the user's transfer list
    4. Returns confirmation
    """,
    request_body=AddTransferAccountSerializer,
    responses={
        201: openapi.Response(
            description="Account added to transfer list successfully",
            examples={
                "application/json": {
                    "message": "Account added to transfer list successfully",
                    "account_number": "87654321",
                    "account_owner": "jane_doe"
                }
            }
        ),
        400: openapi.Response(
            description="Bad request - validation errors or account already in list",
            examples={
                "application/json": {
                    "error": "Account not found"
                }
            }
        ),
        401: openapi.Response(
            description="Authentication required",
            examples={
                "application/json": {
                    "detail": "Authentication credentials were not provided."
                }
            }
        )
    },
    tags=['Transfer Accounts']
)
@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def transfer_accounts(request):
    """
    GET: List all accounts the user can transfer to
    POST: Add an account to the user's transfer list
    """
    if request.method == 'GET':
        # Get user's own accounts
        user_accounts = Account.objects.filter(user=request.user)
        
        # Get accounts user has added to transfer list
        transfer_accounts = UserTransferAccount.objects.filter(user=request.user)
        
        response_data = {
            'user_accounts': AccountSerializer(user_accounts, many=True).data,
            'transfer_accounts': TransferAccountSerializer(transfer_accounts, many=True).data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = AddTransferAccountSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        account_number = serializer.validated_data['account_number']
        
        try:
            # Get the account to add
            account = Account.objects.get(account_number=account_number)
            
            # Check if user is trying to add their own account
            if account.user == request.user:
                return Response(
                    {'error': 'You cannot add your own account to the transfer list'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if account is already in the transfer list
            if UserTransferAccount.objects.filter(user=request.user, account=account).exists():
                return Response(
                    {'error': 'Account is already in your transfer list'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Add account to transfer list
            UserTransferAccount.objects.create(user=request.user, account=account)
            
            return Response({
                'message': 'Account added to transfer list successfully',
                'account_number': account_number,
                'account_owner': account.user.username
            }, status=status.HTTP_201_CREATED)
            
        except Account.DoesNotExist:
            return Response(
                {'error': 'Account not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to add account: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
