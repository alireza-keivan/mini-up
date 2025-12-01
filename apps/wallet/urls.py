# apps/wallet/urls.py

from django.urls import path
from .views import (
    WalletDashboardView,
    WalletDepositView,
    WalletTransactionsView,
    WalletDepositCreateView,
    WalletDepositVerifyView,
    WalletBalanceAPIView,
)

app_name = 'wallet'

urlpatterns = [
    # صفحات HTML
    path('', WalletDashboardView.as_view(), name='dashboard'),
    path('deposit/', WalletDepositView.as_view(), name='deposit'),
    path('transactions/', WalletTransactionsView.as_view(), name='transactions'),
    
    # پردازش شارژ
    path('deposit/create/', WalletDepositCreateView.as_view(), name='deposit_create'),
    path('deposit/verify/', WalletDepositVerifyView.as_view(), name='deposit_verify'),
    
    # API
    path('api/balance/', WalletBalanceAPIView.as_view(), name='api_balance'),
]
