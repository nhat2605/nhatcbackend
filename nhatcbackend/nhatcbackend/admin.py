from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin  # Import BaseUserAdmin
from .models import User, Account

class AccountInline(admin.TabularInline):
    model = Account
    extra = 1  # Number of empty forms to display

class UserAdmin(BaseUserAdmin):  # Inherit from BaseUserAdmin
    inlines = [AccountInline]

class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'user', 'balance')
    search_fields = ('account_number', 'user__username')

admin.site.register(User, UserAdmin)
admin.site.register(Account, AccountAdmin)
