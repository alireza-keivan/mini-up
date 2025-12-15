# apps/orders/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Order, OrderStatusHistory


@receiver(pre_save, sender=Order)
def track_order_status_change(sender, instance, **kwargs):
    """
    ردیابی تغییر وضعیت سفارش قبل از ذخیره
    
    این سیگنال وضعیت قبلی را ذخیره می‌کند تا در post_save بتوانیم
    تاریخچه تغییر وضعیت را ثبت کنیم.
    """
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Order)
def create_order_status_history(sender, instance, created, **kwargs):
    """
    ثبت تاریخچه تغییر وضعیت سفارش
    
    - در ایجاد اولیه: ثبت وضعیت pending
    - در بروزرسانی: ثبت تغییر وضعیت اگر تغییر کرده باشد
    """
    if created:
        # سفارش جدید - ثبت وضعیت اولیه
        OrderStatusHistory.objects.create(
            order=instance,
            old_status='',
            new_status=instance.status,
            note='سفارش ایجاد شد',
            changed_at=timezone.now()
        )
    else:
        # بررسی تغییر وضعیت
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            OrderStatusHistory.objects.create(
                order=instance,
                old_status=old_status,
                new_status=instance.status,
                note=_get_status_change_note(old_status, instance.status),
                changed_at=timezone.now()
            )


def _get_status_change_note(old_status, new_status):
    """
    تولید متن توضیحات برای تغییر وضعیت
    """
    status_notes = {
        Order.Status.PENDING: 'در انتظار پرداخت',
        Order.Status.PAID: 'پرداخت تأیید شد',
        Order.Status.PROCESSING: 'در حال پردازش',
        Order.Status.SHIPPED: 'ارسال شد',
        Order.Status.DELIVERED: 'تحویل داده شد',
        Order.Status.COMPLETED: 'تکمیل شد',
        Order.Status.CANCELLED: 'لغو شد',
        Order.Status.REFUNDED: 'مسترد شد',
        Order.Status.FAILED: 'ناموفق',
    }
    
    new_note = status_notes.get(new_status, new_status)
    return f'تغییر وضعیت به: {new_note}'


@receiver(post_save, sender=Order)
def handle_order_completion(sender, instance, created, **kwargs):
    """
    اقدامات پس از تکمیل سفارش
    
    - ارسال نوتیفیکیشن
    - بروزرسانی آمار کاربر
    - ثبت کش‌بک (در صورت وجود)
    """
    if created:
        return
    
    old_status = getattr(instance, '_old_status', None)
    
    # اگر وضعیت به COMPLETED تغییر کرد
    if old_status != Order.Status.COMPLETED and instance.status == Order.Status.COMPLETED:
        _process_order_completion(instance)
    
    # اگر وضعیت به CANCELLED تغییر کرد
    if old_status != Order.Status.CANCELLED and instance.status == Order.Status.CANCELLED:
        _process_order_cancellation(instance)


def _process_order_completion(order):
    """
    پردازش تکمیل سفارش
    """
    # بروزرسانی آمار کاربر
    user = order.user
    if hasattr(user, 'profile'):
        profile = user.profile
        profile.total_orders = (profile.total_orders or 0) + 1
        profile.total_spent = (profile.total_spent or 0) + order.total_amount
        profile.save(update_fields=['total_orders', 'total_spent'])
    
    # ارسال نوتیفیکیشن تکمیل سفارش
    try:
        from apps.content.services import NotificationService
        NotificationService.notify_order_status_changed(order, 'completed')
    except Exception as e:
        print(f"Failed to send order completion notification: {e}")
    
    # TODO: ثبت کش‌بک در صورت فعال بودن
    # CashbackService.process_order_cashback(order)


def _process_order_cancellation(order):
    """
    پردازش لغو سفارش
    
    - بازگشت موجودی محصولات
    - استرداد کیف پول (در صورت استفاده)
    """
    # بازگشت موجودی
    for item in order.items.all():
        if item.variant:
            item.variant.stock += item.quantity
            item.variant.save(update_fields=['stock'])
        elif hasattr(item.product, 'stock'):
            item.product.stock += item.quantity
            item.product.save(update_fields=['stock'])
    
    # استرداد مبلغ کیف پول
    if order.wallet_amount_used and order.wallet_amount_used > 0:
        try:
            from apps.wallet.services import WalletService
            wallet = order.user.wallet
            WalletService.refund(
                wallet=wallet,
                amount=order.wallet_amount_used,
                order=order,
                description=f'استرداد بابت لغو سفارش {order.order_number}'
            )
        except Exception:
            pass  # Log error in production
    
    # TODO: ارسال نوتیفیکیشن لغو سفارش
    # NotificationService.send_order_cancelled(order)


@receiver(post_save, sender=Order)
def send_order_notifications(sender, instance, created, **kwargs):
    """
    ارسال نوتیفیکیشن‌های مرتبط با سفارش
    """
    if created:
        # نوتیفیکیشن ثبت سفارش جدید
        _send_new_order_notification(instance)
        return
    
    old_status = getattr(instance, '_old_status', None)
    if not old_status or old_status == instance.status:
        return
    
    # نوتیفیکیشن بر اساس وضعیت جدید
    notification_map = {
        Order.Status.PAID: _send_payment_confirmed_notification,
        Order.Status.PROCESSING: _send_processing_notification,
        Order.Status.SHIPPED: _send_shipped_notification,
        Order.Status.DELIVERED: _send_delivered_notification,
    }
    
    handler = notification_map.get(instance.status)
    if handler:
        handler(instance)


def _send_new_order_notification(order):
    """ارسال نوتیفیکیشن سفارش جدید"""
    try:
        from apps.content.services import NotificationService
        NotificationService.notify_order_created(order)
    except Exception as e:
        print(f"Failed to send new order notification: {e}")


def _send_payment_confirmed_notification(order):
    """ارسال نوتیفیکیشن تأیید پرداخت"""
    try:
        from apps.content.services import NotificationService
        NotificationService.notify_order_status_changed(order, 'pending')
    except Exception as e:
        print(f"Failed to send payment confirmed notification: {e}")


def _send_processing_notification(order):
    """ارسال نوتیفیکیشن شروع پردازش"""
    try:
        from apps.content.services import NotificationService
        NotificationService.notify_order_status_changed(order, 'confirmed')
    except Exception as e:
        print(f"Failed to send processing notification: {e}")


def _send_shipped_notification(order):
    """ارسال نوتیفیکیشن ارسال سفارش"""
    try:
        from apps.content.services import NotificationService
        NotificationService.notify_order_status_changed(order, 'preparing')
    except Exception as e:
        print(f"Failed to send shipped notification: {e}")


def _send_delivered_notification(order):
    """ارسال نوتیفیکیشن تحویل سفارش"""
    pass
