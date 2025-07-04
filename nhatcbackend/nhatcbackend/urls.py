"""
URL configuration for nhatcbackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from .views import UserCreateView, AccountListView, AccountDetailView, TransactionListView, fund_transfer, password_reset, transfer_accounts

schema_view = get_schema_view(
   openapi.Info(
      title="Banking API",
      default_version='v1',
      description="""
      # Simple Banking Application API

      This API provides comprehensive banking functionality including:

      ## Features
      - **User Registration & Authentication**: JWT-based authentication system
      - **Account Management**: Support for two account types (Cheque & Saving)
      - **Fund Transfers**: Secure money transfers between accounts
      - **Transaction History**: Complete transaction tracking and history

      ## Account Types
      - **Cheque Account**: Standard checking account for daily transactions
      - **Saving Account**: Savings account for long-term deposits

      ## Authentication
      Most endpoints require JWT authentication. Use the `/api/token/` endpoint to obtain access tokens.
      
      ### How to use authentication in Swagger:
      1. Click the **Authorize** button (🔒) at the top right
      2. Enter your JWT token in the format: `Bearer your_access_token_here`
      3. Click **Authorize** to apply the token to all requests
      4. The token will be automatically included in the Authorization header

      ## Error Handling
      The API returns appropriate HTTP status codes and detailed error messages for all operations.
      """,
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@example.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   authentication_classes=[],  # Disable authentication for schema endpoint
)

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('rest_framework.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', UserCreateView.as_view(), name='register'),
    path('api/password-reset/', password_reset, name='password-reset'),
    path('api/accounts/', AccountListView.as_view(), name='account-list'),
    path('api/accounts/<int:pk>/', AccountDetailView.as_view(), name='account-detail'),
    path('api/transactions/', TransactionListView.as_view(), name='transaction-list'),
    path('api/transfer/', fund_transfer, name='fund-transfer'),
    path('api/transfer-accounts/', transfer_accounts, name='transfer-accounts'),
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('sentry-debug/', trigger_error),
]
