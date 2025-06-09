from rest_framework import serializers
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
from .models import User, Account, Transaction, UserTransferAccount, UserTransferAccount

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="Email address associated with your account"
    )
    
    def validate_email(self, value):
        """Check if user with this email exists"""
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No account found with this email address")
        return value
    
    def save(self):
        """Generate new password and send via email"""
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate secure temporary password
        temp_password = user.generate_temp_password()
        
        # Update user's password
        user.set_password(temp_password)
        user.save()
        
        # Send email with new password
        subject = f"{settings.EMAIL_SUBJECT_PREFIX}Password Reset"
        message = f"""
Hello {user.username},

Your password has been reset successfully. Your new password is:

{temp_password}

If you did not request this password reset, please contact support immediately.

Best regards,
Banking API Team
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return {
                'email': email,
                'message': 'New password sent to your email address'
            }
        except Exception as e:
            # Log the error in production
            raise serializers.ValidationError(f"Failed to send email: {str(e)}")

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'account_number', 'account_type', 'balance']
        read_only_fields = ['account_number']  # Account number is auto-generated
    
    def validate_balance(self, value):
        """Validate balance field"""
        if value is not None:
            # Check if balance is negative
            if value < Decimal('0.00'):
                raise serializers.ValidationError("Account balance cannot be negative.")
            
            # Check maximum balance limit (10 million)
            if value > Decimal('10000000.00'):
                raise serializers.ValidationError("Account balance cannot exceed $10,000,000.00.")
            
            # Check decimal places (should be exactly 2)
            if value.as_tuple().exponent < -2:
                raise serializers.ValidationError("Balance cannot have more than 2 decimal places.")
        
        return value
    
    def validate(self, attrs):
        """Additional validation"""
        # For new accounts, ensure balance is reasonable for the account type
        if not self.instance:  # Creating a new account
            balance = attrs.get('balance', Decimal('0.00'))
            account_type = attrs.get('account_type', 'cheque')
            
            # Savings accounts might have minimum balance requirements
            if account_type == 'saving' and balance > Decimal('0.00') and balance < Decimal('100.00'):
                raise serializers.ValidationError({
                    'balance': 'Savings accounts typically require a minimum balance of $100.00.'
                })
        
        return attrs
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add human-readable account type
        data['account_type_display'] = instance.get_account_type_display()
        return data

class TransactionSerializer(serializers.ModelSerializer):
    from_account_number = serializers.CharField(write_only=True, required=False)
    to_account_number = serializers.CharField(write_only=True, required=False)
    from_account = AccountSerializer(read_only=True)
    to_account = AccountSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'from_account', 'to_account', 'from_account_number', 'to_account_number', 
                 'amount', 'transaction_type', 'description', 'created_at']
        read_only_fields = ['created_at']

class FundTransferSerializer(serializers.Serializer):
    from_account_number = serializers.CharField(
        max_length=8,
        help_text="8-digit account number of the sender account"
    )
    to_account_number = serializers.CharField(
        max_length=8,
        help_text="8-digit account number of the recipient account"
    )
    amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=0.01,
        help_text="Amount to transfer (minimum 0.01)"
    )
    description = serializers.CharField(
        max_length=255, 
        required=False, 
        allow_blank=True,
        help_text="Optional description for the transfer"
    )
    
    def validate(self, data):
        if data['from_account_number'] == data['to_account_number']:
            raise serializers.ValidationError("Cannot transfer to the same account")
        return data
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value

class UserSerializer(serializers.ModelSerializer):
    accounts = AccountSerializer(many=True, read_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'accounts', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'help_text': 'Unique username for the user'},
            'email': {'help_text': 'Email address for password reset and notifications'}
        }

    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class AddTransferAccountSerializer(serializers.Serializer):
    """Serializer for adding an account to user's transfer list"""
    account_number = serializers.CharField(
        max_length=8,
        help_text="8-digit account number to add to transfer list"
    )
    
    def validate_account_number(self, value):
        """Validate that the account exists"""
        try:
            Account.objects.get(account_number=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account not found")
        return value

class ExternalAccountSerializer(serializers.ModelSerializer):
    """Serializer for external accounts - only shows safe information"""
    account_owner_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Account
        fields = ['id', 'account_number', 'account_owner_username']

class TransferAccountSerializer(serializers.ModelSerializer):
    """Serializer for displaying transfer accounts"""
    account = ExternalAccountSerializer(read_only=True)
    account_owner_username = serializers.CharField(source='account.user.username', read_only=True)
    
    class Meta:
        model = UserTransferAccount
        fields = ['id', 'account', 'account_owner_username', 'added_at']
        read_only_fields = ['added_at']

class TransferAccountListSerializer(serializers.Serializer):
    """Serializer for the complete transfer account list including user's own accounts"""
    user_accounts = AccountSerializer(many=True, read_only=True)
    transfer_accounts = TransferAccountSerializer(many=True, read_only=True)
