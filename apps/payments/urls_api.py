# apps/payments/urls_api.py

"""
Payment API URL Configuration
=============================
RESTful API endpoints for payment operations
"""

from django.urls import path
from . import api_views

app_name = 'payments_api'

urlpatterns = [
    # ═══════════════════════════════════════════════════════════════════════════
    # GATEWAY ENDPOINTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    # GET: لیست درگاه‌های فعال
    path(
        'gateways/',
        api_views.AvailableGatewaysAPIView.as_view(),
        name='gateway_list'
    ),
    
    # GET: درگاه پیش‌فرض
    path(
        'gateways/default/',
        api_views.DefaultGatewayAPIView.as_view(),
        name='gateway_default'
    ),
    
    # GET: جزئیات یک درگاه خاص
    path(
        'gateways/<str:gateway_type>/',
        api_views.GatewayDetailAPIView.as_view(),
        name='gateway_detail'
    ),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PAYMENT INITIATION ENDPOINTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    # POST: شروع پرداخت عمومی
    path(
        'initiate/',
        api_views.PaymentInitiateAPIView.as_view(),
        name='initiate'
    ),
    
    # POST: پرداخت یک سفارش خاص
    path(
        'orders/<uuid:order_id>/pay/',
        api_views.OrderPaymentInitiateAPIView.as_view(),
        name='order_pay'
    ),
    
    # POST: شارژ کیف پول
    path(
        'wallet/deposit/',
        api_views.WalletDepositInitiateAPIView.as_view(),
        name='wallet_deposit'
    ),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PAYMENT VERIFICATION ENDPOINTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    # GET/POST: Callback تأیید پرداخت از درگاه
    path(
        'verify/',
        api_views.PaymentVerifyAPIView.as_view(),
        name='verify'
    ),
    
    # POST: تأیید دستی تراکنش (برای موارد خاص)
    path(
        'verify/<uuid:transaction_id>/',
        api_views.PaymentVerifyAPIView.as_view(),
        name='verify_transaction'
    ),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TRANSACTION ENDPOINTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    # GET: لیست تراکنش‌های کاربر
    path(
        'transactions/',
        api_views.TransactionHistoryAPIView.as_view(),
        name='transaction_list'
    ),
    
    # GET: جزئیات یک تراکنش
    path(
        'transactions/<uuid:transaction_id>/',
        api_views.TransactionDetailAPIView.as_view(),
        name='transaction_detail'
    ),
    
    # GET: وضعیت یک تراکنش (polling)
    path(
        'transactions/<uuid:transaction_id>/status/',
        api_views.TransactionStatusAPIView.as_view(),
        name='transaction_status'
    ),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # REFUND ENDPOINTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    # POST: درخواست بازگشت وجه
    path(
        'refund/',
        api_views.RefundRequestAPIView.as_view(),
        name='refund_request'
    ),
    
    # GET: وضعیت درخواست بازگشت وجه
    path(
        'refund/<uuid:refund_id>/status/',
        api_views.RefundStatusAPIView.as_view(),
        name='refund_status'
    ),
]
