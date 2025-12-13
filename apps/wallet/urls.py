# apps/wallet/urls.py

from django.urls import path
from django.views.generic import RedirectView
from .views import (
    WalletDepositVerifyView,
    WalletBalanceAPIView,
)

app_name = 'wallet'

urlpatterns = [
    # Redirect old wallet pages to dashboard
    path('', RedirectView.as_view(pattern_name='accounts:dashboard', permanent=False), name='dashboard'),
    path('deposit/', RedirectView.as_view(pattern_name='accounts:dashboard', permanent=False), name='deposit'),
    path('transactions/', RedirectView.as_view(pattern_name='accounts:dashboard', permanent=False), name='transactions'),
    
    # پردازش شارژ - keep these for payment gateway callbacks
    path('deposit/verify/', WalletDepositVerifyView.as_view(), name='deposit_verify'),
    
    # API
    path('api/balance/', WalletBalanceAPIView.as_view(), name='api_balance'),
]
