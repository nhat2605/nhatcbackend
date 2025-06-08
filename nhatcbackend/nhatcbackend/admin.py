from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin  # Import BaseUserAdmin
from .models import User, Account, Transaction

class AccountInline(admin.TabularInline):
    model = Account
    extra = 1  # Number of empty forms to display

class UserAdmin(BaseUserAdmin):  # Inherit from BaseUserAdmin
    inlines = [AccountInline]

class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'user', 'account_type', 'balance')
    list_filter = ('account_type',)
    search_fields = ('account_number', 'user__username')

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction_type', 'from_account', 'to_account', 'amount', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('from_account__account_number', 'to_account__account_number', 'description')
    readonly_fields = ('created_at',)

admin.site.register(User, UserAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Transaction, TransactionAdmin)
