from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from decimal import Decimal
import random
import secrets
import string

class User(AbstractUser):
    email = models.EmailField(unique=True, null=False, blank=False)
    
    def generate_temp_password(self):
        """Generate a secure temporary password"""
        # Generate a 12-character password with letters, digits, and special characters
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        # Ensure it has at least one of each type
        password = (
            secrets.choice(string.ascii_lowercase) +
            secrets.choice(string.ascii_uppercase) +
            secrets.choice(string.digits) +
            secrets.choice("!@#$%^&*") +
            password[4:]  # Fill the rest
        )
        
        # Shuffle the password
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        return ''.join(password_list)

def generate_account_number():
    """Generate a unique 8-digit account number"""
    return str(random.randint(10000000, 99999999))

class Account(models.Model):
    ACCOUNT_TYPES = [
        ('cheque', 'Cheque'),
        ('saving', 'Saving'),
    ]
    
    user = models.ForeignKey(User, related_name='accounts', on_delete=models.CASCADE)
    account_number = models.CharField(max_length=8, unique=True, default=generate_account_number)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default='cheque')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f'{self.user.username} - {self.account_number} ({self.account_type})'

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('transfer', 'Transfer'),
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
    ]
    
    from_account = models.ForeignKey(Account, related_name='outgoing_transactions', on_delete=models.CASCADE, null=True, blank=True)
    to_account = models.ForeignKey(Account, related_name='incoming_transactions', on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.transaction_type == 'transfer':
            return f'Transfer: {self.from_account.account_number} -> {self.to_account.account_number} (${self.amount})'
        return f'{self.transaction_type.title()}: ${self.amount}'
    
    def clean(self):
        if self.transaction_type == 'transfer':
            if not self.from_account or not self.to_account:
                raise ValidationError('Transfer requires both from and to accounts')
            if self.from_account == self.to_account:
                raise ValidationError('Cannot transfer to the same account')
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)