from django.contrib.auth.models import AbstractUser
from django.db import models
import random

class User(AbstractUser):
    pass

def generate_account_number():
    return str(random.randint(10000000, 99999999))

class Account(models.Model):
    user = models.ForeignKey(User, related_name='accounts', on_delete=models.CASCADE)
    account_number = models.CharField(max_length=8, unique=True, default=generate_account_number)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f'{self.user.username} - {self.account_number}'
