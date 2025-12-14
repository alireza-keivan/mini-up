# apps/wallet/urls.py

from django.urls import path
from django.views.generic import RedirectView
from .views import (
    WalletDashboardView,
    WalletDepositView,
    WalletTransactionsView,
    WalletDepositVerifyView,
    WalletBalanceAPIView,
)

app_name = 'wallet'

urlpatterns = [
    # صفحات اصلی کیف پول
    path('', WalletDashboardView.as_view(), name='dashboard'),
    path('deposit/', WalletDepositView.as_view(), name='deposit'),
    path('transactions/', WalletTransactionsView.as_view(), name='transactions'),
    
    # پردازش شارژ - keep these for payment gateway callbacks
    path('deposit/verify/', WalletDepositVerifyView.as_view(), name='deposit_verify'),
    
    # API
    path('api/balance/', WalletBalanceAPIView.as_view(), name='api_balance'),
]
