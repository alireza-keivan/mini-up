# apps/wallet/urls.py

from django.urls import path
from django.views.generic import RedirectView
from .views import (
    WalletDashboardView,
    WalletDepositView,
    WalletTransactionsView,
    WalletDepositVerifyView,
    WalletBalanceAPIView,
    SetupPinView,
    ChangePinView,
    RemovePinView,
    VerifyPinView,
    GetPinStatusView,
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
    
    # PIN Management API
    path('api/pin/setup/', SetupPinView.as_view(), name='api_pin_setup'),
    path('api/pin/change/', ChangePinView.as_view(), name='api_pin_change'),
    path('api/pin/remove/', RemovePinView.as_view(), name='api_pin_remove'),
    path('api/pin/verify/', VerifyPinView.as_view(), name='api_pin_verify'),
    path('api/pin/status/', GetPinStatusView.as_view(), name='api_pin_status'),
]
