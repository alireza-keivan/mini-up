# apps/payments/urls.py

"""
Payment URL Configuration - HTML Views
======================================
مسیرهای صفحات HTML برای پرداخت
"""

from django.urls import path, include
from . import views

app_name = 'payments'

urlpatterns = [
    # ─────────────────────────────────────────────────────────────────────────
    # صفحات اصلی پرداخت
    # ─────────────────────────────────────────────────────────────────────────
    
    # صفحه انتخاب درگاه و شروع پرداخت
    path(
        'checkout/',
        views.PaymentCheckoutView.as_view(),
        name='checkout'
    ),
    
    # صفحه انتظار پرداخت (قبل از redirect به درگاه)
    path(
        'processing/<uuid:transaction_id>/',
        views.PaymentProcessingView.as_view(),
        name='processing'
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # Callback از درگاه‌ها
    # ─────────────────────────────────────────────────────────────────────────
    
    # Callback عمومی (برای همه درگاه‌ها)
    path(
        'verify/',
        views.PaymentVerifyCallbackView.as_view(),
        name='verify_callback'
    ),
    
    # Callback اختصاصی هر درگاه (اختیاری)
    path(
        'callback/zarinpal/',
        views.ZarinpalCallbackView.as_view(),
        name='callback_zarinpal'
    ),
    path(
        'callback/idpay/',
        views.IDPayCallbackView.as_view(),
        name='callback_idpay'
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # صفحات نتیجه پرداخت
    # ─────────────────────────────────────────────────────────────────────────
    
    # پرداخت موفق
    path(
        'success/<uuid:transaction_id>/',
        views.PaymentSuccessView.as_view(),
        name='success'
    ),
    
    # پرداخت ناموفق
    path(
        'failed/<uuid:transaction_id>/',
        views.PaymentFailedView.as_view(),
        name='failed'
    ),
    
    # لغو پرداخت توسط کاربر
    path(
        'cancelled/',
        views.PaymentCancelledView.as_view(),
        name='cancelled'
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # تاریخچه و جزئیات تراکنش
    # ─────────────────────────────────────────────────────────────────────────
    
    # لیست تراکنش‌های کاربر
    path(
        'transactions/',
        views.TransactionListView.as_view(),
        name='transaction_list'
    ),
    
    # جزئیات یک تراکنش
    path(
        'transactions/<uuid:transaction_id>/',
        views.TransactionDetailView.as_view(),
        name='transaction_detail'
    ),
    
    # رسید پرداخت (قابل چاپ)
    path(
        'transactions/<uuid:transaction_id>/receipt/',
        views.TransactionReceiptView.as_view(),
        name='transaction_receipt'
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # شارژ کیف پول
    # ─────────────────────────────────────────────────────────────────────────
    
    # صفحه شارژ کیف پول
    path(
        'wallet/deposit/',
        views.WalletDepositView.as_view(),
        name='wallet_deposit'
    ),
    
    # ─────────────────────────────────────────────────────────────────────────
    # API Routes (include از فایل جداگانه)
    # ─────────────────────────────────────────────────────────────────────────
    
    path('api/v1/', include('apps.payments.urls_api')),
]
