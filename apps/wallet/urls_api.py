# apps/wallet/urls_api.py

from django.urls import path
from . import api_views

app_name = "wallet_api"

urlpatterns = [
    # ═══════════════════════════════════════════════════════════════════════════
    # WALLET INFO
    # ═══════════════════════════════════════════════════════════════════════════
    
    # اطلاعات کامل کیف پول
    # GET /wallet/api/v1/
    path("", api_views.WalletDetailAPIView.as_view(), name="detail"),
    
    # موجودی کیف پول (سبک)
    # GET /wallet/api/v1/balance/
    path("balance/", api_views.WalletBalanceAPIView.as_view(), name="balance"),
    
    # آمار کیف پول (۳۰ روزه)
    # GET /wallet/api/v1/stats/
    path("stats/", api_views.WalletStatsAPIView.as_view(), name="stats"),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TRANSACTIONS (تراکنش‌ها)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # لیست تراکنش‌ها
    # GET /wallet/api/v1/transactions/?type=deposit&limit=20&offset=0
    path("transactions/", api_views.WalletTransactionsAPIView.as_view(), name="transactions"),
    
    # جزئیات یک تراکنش
    # GET /wallet/api/v1/transactions/<uuid>/
    path("transactions/<uuid:pk>/", api_views.WalletTransactionDetailAPIView.as_view(), name="transaction_detail"),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DEPOSIT (شارژ کیف پول)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # ایجاد درخواست شارژ
    # POST /wallet/api/v1/deposit/create/
    path("deposit/create/", api_views.WalletDepositCreateAPIView.as_view(), name="deposit_create"),
    
    # تأیید پرداخت شارژ
    # POST /wallet/api/v1/deposit/verify/
    path("deposit/verify/", api_views.WalletDepositVerifyAPIView.as_view(), name="deposit_verify"),
    
    # تاریخچه درخواست‌های شارژ
    # GET /wallet/api/v1/deposits/
    path("deposits/", api_views.WalletDepositsHistoryAPIView.as_view(), name="deposits_history"),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TRANSFER (انتقال وجه)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # انتقال به کاربر دیگر
    # POST /wallet/api/v1/transfer/
    path("transfer/", api_views.WalletTransferAPIView.as_view(), name="transfer"),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # WITHDRAW (برداشت)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # درخواست برداشت به حساب بانکی
    # POST /wallet/api/v1/withdraw/
    path("withdraw/", api_views.WalletWithdrawAPIView.as_view(), name="withdraw"),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PAYMENT (بررسی پرداخت)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # بررسی امکان پرداخت با کیف پول
    # POST /wallet/api/v1/payment/check/
    path("payment/check/", api_views.WalletPaymentCheckAPIView.as_view(), name="payment_check"),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GIFT CODE (کد هدیه)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # استفاده از کد هدیه
    # POST /wallet/api/v1/redeem/
    path("redeem/", api_views.WalletRedeemGiftCodeAPIView.as_view(), name="redeem_gift"),
]
