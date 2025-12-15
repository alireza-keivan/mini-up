# apps/payments/signals.py

"""
Signals for Payment App
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Payment

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Payment)
def notify_payment_status(sender, instance, created, **kwargs):
    """
    ارسال اعلان برای تغییر وضعیت پرداخت
    """
    if created:
        return
    
    try:
        from apps.content.services import NotificationService
        
        # پرداخت موفق
        if hasattr(instance, '_old_status'):
            old_status = instance._old_status
            
            if old_status != 'verified' and instance.status == 'verified':
                NotificationService.notify_payment_success(instance)
            
            # پرداخت ناموفق
            elif old_status != 'failed' and instance.status == 'failed':
                NotificationService.notify_payment_failed(instance)
                
    except Exception as e:
        logger.error(f"Failed to send payment notification: {e}")


@receiver(post_save, sender=Payment)
def track_payment_status_change(sender, instance, **kwargs):
    """
    ردیابی تغییرات وضعیت برای سیگنال بعدی
    """
    if instance.pk:
        try:
            old_instance = Payment.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Payment.DoesNotExist:
            pass
