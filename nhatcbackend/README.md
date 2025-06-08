# Banking API

A comprehensive Django REST API for a simple banking application with JWT authentication, account management, and fund transfers.

## Features

- 🔐 **User Authentication**: JWT-based authentication system
- 💳 **Account Management**: Support for Cheque and Saving account types  
- 💸 **Fund Transfers**: Secure money transfers between accounts
- 📊 **Transaction History**: Complete transaction tracking and history
- 📚 **API Documentation**: Interactive Swagger/OpenAPI documentation

## Account Types

- **Cheque Account**: Standard checking account for daily transactions
- **Saving Account**: Savings account for long-term deposits

## Quick Start

### 1. Setup

```bash
# Install dependencies
pip install django djangorestframework djangorestframework-simplejwt drf-yasg django-cors-headers

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start the server
python manage.py runserver
```

### 2. API Documentation

Once the server is running, visit:
- **Swagger UI**: http://127.0.0.1:8000/swagger/
- **ReDoc**: http://127.0.0.1:8000/redoc/

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register/` | Register a new user |
| POST | `/api/token/` | Obtain JWT access token |
| POST | `/api/token/refresh/` | Refresh JWT token |

### Accounts

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/accounts/` | List user's accounts | ✅ |
| POST | `/api/accounts/` | Create new account | ✅ |
| GET | `/api/accounts/{id}/` | Get account details | ✅ |
| PUT | `/api/accounts/{id}/` | Update account | ✅ |
| DELETE | `/api/accounts/{id}/` | Delete account | ✅ |

### Transactions

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/transactions/` | List user's transactions | ✅ |
| POST | `/api/transfer/` | Transfer funds between accounts | ✅ |

## Usage Examples

### 1. Register a User

```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "securepassword123"
  }'
```

### 2. Get Access Token

```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "securepassword123"
  }'
```

### 3. Create an Account

```bash
curl -X POST http://127.0.0.1:8000/api/accounts/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "account_type": "cheque",
    "balance": "1000.00"
  }'
```

### 4. Transfer Funds

```bash
curl -X POST http://127.0.0.1:8000/api/transfer/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "from_account_number": "12345678",
    "to_account_number": "87654321",
    "amount": "100.00",
    "description": "Payment for services"
  }'
```

## Data Models

### User
- Extends Django's AbstractUser
- Related to multiple accounts

### Account
```python
{
  "id": 1,
  "account_number": "12345678",  # Auto-generated
  "account_type": "cheque",      # "cheque" or "saving"
  "balance": "1000.00"
}
```

### Transaction
```python
{
  "id": 1,
  "from_account": {...},
  "to_account": {...},
  "amount": "100.00",
  "transaction_type": "transfer",
  "description": "Payment description",
  "created_at": "2024-01-01T12:00:00Z"
}
```

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Account Ownership**: Users can only access their own accounts
- **Atomic Transactions**: Fund transfers are atomic (all-or-nothing)
- **Input Validation**: Comprehensive validation on all endpoints
- **Balance Verification**: Prevents overdrafts

## Error Handling

The API returns appropriate HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

Error responses include detailed messages:
```json
{
  "error": "Insufficient balance"
}
```

## Testing

Run the included test script:

```bash
python api_test.py
```

This script will:
1. Register a new user
2. Obtain JWT tokens
3. Create cheque and saving accounts
4. Perform a fund transfer
5. Display transaction history

## Development

### Admin Interface

Access the Django admin at http://127.0.0.1:8000/admin/ to:
- Manage users and accounts
- View transaction history
- Monitor system activity

### Database

The application uses SQLite by default. For production, configure PostgreSQL or MySQL in `settings.py`.

### Environment Variables

For production deployment, set these environment variables:
- `SECRET_KEY`: Django secret key
- `DEBUG`: Set to `False`
- `ALLOWED_HOSTS`: Your domain names
- `DATABASE_URL`: Database connection string

## API Response Examples

### Successful Fund Transfer
```json
{
  "message": "Transfer completed successfully",
  "transaction_id": 123,
  "from_account": "12345678",
  "to_account": "87654321",
  "amount": "100.00",
  "new_balance": "900.00"
}
```

### Account List
```json
[
  {
    "id": 1,
    "account_number": "12345678",
    "account_type": "cheque",
    "account_type_display": "Cheque",
    "balance": "1000.00"
  },
  {
    "id": 2,
    "account_number": "87654321",
    "account_type": "saving",
    "account_type_display": "Saving",
    "balance": "2000.00"
  }
]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
