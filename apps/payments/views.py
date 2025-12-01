# apps/payments/views.py

from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from .models import Transaction, PaymentGateway
from .services import ZarinPalService
from apps.orders.models import Order


class PaymentRequestView(LoginRequiredMixin, View):
    """
    شروع پرداخت - کاربر به درگاه می‌ره
    """
    
    def post(self, request, order_id):
        # گرفتن سفارش کاربر
        order = get_object_or_404(
            Order, 
            id=order_id, 
            user=request.user,
            status='pending_payment'
        )
        
        # بررسی اینکه قبلاً پرداخت نشده باشه
        if order.status == 'paid':
            messages.warning(request, 'این سفارش قبلاً پرداخت شده است.')
            return redirect('orders:detail', order_id=order.id)
        
        # گرفتن درگاه فعال
        try:
            gateway = PaymentGateway.objects.get(
                gateway_type='zarinpal',
                is_active=True
            )
        except PaymentGateway.DoesNotExist:
            messages.error(request, 'درگاه پرداخت در دسترس نیست.')
            return redirect('orders:checkout')
        
        # ساخت رکورد تراکنش (هنوز pending)
        transaction = Transaction.objects.create(
            user=request.user,
            order=order,
            amount=order.final_amount,
            gateway=gateway,
            status='pending',
            description=f"پرداخت سفارش {order.order_number}"
        )
        
        # درخواست از زرین‌پال
        zarinpal = ZarinPalService(sandbox=settings.DEBUG)
        result = zarinpal.request_payment(
            amount=order.final_amount,
            description=f"خرید از {settings.SITE_NAME} - سفارش {order.order_number}",
            callback_url=request.build_absolute_uri(f'/payments/verify/'),
            mobile=request.user.phone,
            email=getattr(request.user, 'email', None)
        )
        
        if result["success"]:
            # ذخیره authority
            transaction.authority = result["authority"]
            transaction.save()
            
            # 🚀 کاربر به سایت زرین‌پال می‌ره
            return redirect(result["payment_url"])
        else:
            transaction.status = 'failed'
            transaction.save()
            messages.error(request, f'خطا در اتصال به درگاه: {result["error"]}')
            return redirect('orders:checkout')


class PaymentVerifyView(View):
    """
    تأیید پرداخت - کاربر از درگاه برگشته
    
    زرین‌پال این پارامترها رو می‌فرسته:
    - Authority: کد یکتای تراکنش
    - Status: OK یا NOK
    """
    
    def get(self, request):
        authority = request.GET.get('Authority')
        status = request.GET.get('Status')
        
        if not authority:
            messages.error(request, 'پارامترهای پرداخت نامعتبر است.')
            return redirect('home')
        
        # پیدا کردن تراکنش
        try:
            transaction = Transaction.objects.select_related('order', 'gateway').get(
                authority=authority
            )
        except Transaction.DoesNotExist:
            messages.error(request, 'تراکنش یافت نشد.')
            return redirect('home')
        
        order = transaction.order
        
        # بررسی تکراری نبودن verify
        if transaction.status == 'completed':
            messages.info(request, 'این تراکنش قبلاً تأیید شده است.')
            return redirect('orders:detail', order_id=order.id)
        
        # اگه کاربر انصراف داده
        if status != 'OK':
            transaction.status = 'cancelled'
            transaction.save()
            messages.warning(request, 'پرداخت توسط شما لغو شد.')
            return render(request, 'payments/cancelled.html', {
                'transaction': transaction,
                'order': order
            })
        
        # تأیید نهایی از زرین‌پال
        zarinpal = ZarinPalService(sandbox=settings.DEBUG)
        result = zarinpal.verify_payment(
            authority=authority,
            amount=transaction.amount
        )
        
        if result["success"]:
            # ✅ پرداخت موفق
            transaction.status = 'completed'
            transaction.ref_id = result["ref_id"]
            transaction.card_pan = result.get("card_pan")
            transaction.verified_at = timezone.now()
            transaction.save()
            
            # تغییر وضعیت سفارش
            order.status = 'paid'
            order.paid_at = timezone.now()
            order.save()
            
            # تحویل خودکار محصولات دیجیتال
            self._deliver_digital_products(order)
            
            messages.success(request, 'پرداخت با موفقیت انجام شد!')
            return render(request, 'payments/success.html', {
                'transaction': transaction,
                'order': order
            })
        else:
            # ❌ پرداخت ناموفق
            transaction.status = 'failed'
            transaction.save()
            messages.error(request, f'پرداخت ناموفق: {result.get("error", "خطای نامشخص")}')
            return render(request, 'payments/failed.html', {
                'transaction': transaction,
                'order': order,
                'error': result.get("error")
            })
    
    def _deliver_digital_products(self, order):
        """
        تحویل خودکار محصولات دیجیتال
        مثل: کدهای گیفت کارت، اکانت‌ها، و...
        """
        from apps.products.models import ProductStock
        
        for item in order.items.all():
            product = item.product
            
            # فقط محصولات دیجیتال
            if not product.is_digital:
                continue
            
            # گرفتن موجودی فروخته نشده
            stocks = ProductStock.objects.filter(
                product=product,
                is_sold=False
            )[:item.quantity]
            
            delivered_items = []
            for stock in stocks:
                stock.is_sold = True
                stock.sold_at = timezone.now()
                stock.order_item = item
                stock.save()
                delivered_items.append(stock)
            
            # ذخیره اطلاعات تحویل در آیتم سفارش
            if delivered_items:
                item.delivered_data = {
                    'stocks': [s.id for s in delivered_items],
                    'delivered_at': timezone.now().isoformat()
                }
                item.is_delivered = True
                item.save()


class PaymentStatusView(LoginRequiredMixin, View):
    """
    نمایش وضعیت پرداخت
    """
    
    def get(self, request, transaction_id):
        transaction = get_object_or_404(
            Transaction,
            id=transaction_id,
            user=request.user
        )
        
        return render(request, 'payments/status.html', {
            'transaction': transaction
        })
