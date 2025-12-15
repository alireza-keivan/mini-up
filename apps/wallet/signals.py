# apps/wallet/signals.py

"""
Signals for Wallet App

نکته مهم:
---------
ایجاد Wallet برای کاربر جدید در apps/accounts/signals.py انجام می‌شود.
این کار باعث می‌شود همه موارد مرتبط با کاربر (Profile, Wallet) 
در یک جا مدیریت شوند و از تداخل جلوگیری شود.

این فایل برای سیگنال‌های مخصوص عملیات Wallet است (مثل لاگ تراکنش‌ها)
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Wallet, Transaction

logger = logging.getLogger(__name__)


# ============================================
# ❌ سیگنال زیر غیرفعال شد (تکراری بود)
# ============================================
# @receiver(post_save, sender=User)
# def create_wallet_for_new_user(sender, instance, created, **kwargs):
#     """این سیگنال به accounts/signals.py منتقل شد"""
#     if created:
#         Wallet.objects.get_or_create(user=instance)


# ============================================
# ✅ سیگنال‌های مخصوص Wallet
# ============================================
@receiver(post_save, sender=Transaction)
def log_transaction(sender, instance, created, **kwargs):
    """لاگ تراکنش‌های جدید"""
    if created:
        logger.info(
            f"💰 Transaction: {instance.transaction_type} | "
            f"Amount: {instance.amount:,} | "
            f"User: {instance.wallet.user}"
        )
        
        # ارسال اعلان برای تراکنش‌های مهم
        try:
            from apps.content.services import NotificationService
            
            if instance.transaction_type == 'deposit' and instance.status == 'completed':
                # شارژ کیف پول
                NotificationService.notify_wallet_deposit(instance)
            elif instance.transaction_type == 'purchase' and instance.status == 'completed':
                # خرید با کیف پول
                NotificationService.notify_wallet_purchase(instance)
        except Exception as e:
            logger.error(f"Failed to send wallet notification: {e}")
