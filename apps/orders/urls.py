# apps/orders/urls.py

from django.urls import path
from django.views.generic import RedirectView
from . import api_views
from apps.accounts.views import OrdersView

app_name = 'orders'

urlpatterns = [
    # ═══════════════════════════════════════════════════════════════════════════
    # CART URLs
    # ═══════════════════════════════════════════════════════════════════════════
    
    # سبد خرید - مشاهده و خالی کردن
    path('cart/', api_views.CartAPIView.as_view(), name='cart'),
    
    # افزودن به سبد
    path('cart/add/', api_views.CartAddItemAPIView.as_view(), name='cart_add'),
    
    # مدیریت آیتم سبد (بروزرسانی تعداد / حذف)
    path('cart/item/<int:item_id>/', api_views.CartItemAPIView.as_view(), name='cart_item'),
    
    # اعتبارسنجی سبد قبل از پرداخت
    path('cart/validate/', api_views.CartValidateAPIView.as_view(), name='cart_validate'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CHECKOUT URLs
    # ═══════════════════════════════════════════════════════════════════════════
    
    # پیش‌نمایش سفارش (محاسبه مبالغ)
    path('checkout/preview/', api_views.CheckoutPreviewAPIView.as_view(), name='checkout_preview'),
    
    # ثبت نهایی سفارش
    path('checkout/', api_views.CheckoutAPIView.as_view(), name='checkout'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ORDER URLs
    # ═══════════════════════════════════════════════════════════════════════════
    
    # لیست سفارشات کاربر
    path('', OrdersView.as_view(), name='order_list'),
    path('history/', OrdersView.as_view(), name='history'),
    
    # جزئیات سفارش - keep for order details page
    path('<int:order_id>/', api_views.OrderDetailAPIView.as_view(), name='order_detail'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PAYMENT URLs
    # ═══════════════════════════════════════════════════════════════════════════
    
    # تأیید پرداخت (callback از درگاه)
    path('payment/verify/', api_views.PaymentVerifyAPIView.as_view(), name='payment_verify'),
]
