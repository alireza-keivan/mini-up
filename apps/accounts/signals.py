# apps/accounts/signals.py

"""
Signals for Accounts App

- Auto-create Wallet when user registers
- Log user activities
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import User

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    """
    ایجاد کیف پول خودکار برای کاربر جدید
    """
    if created:
        try:
            from apps.wallet.models import Wallet
            
            wallet, wallet_created = Wallet.objects.get_or_create(user=instance)
            
            if wallet_created:
                logger.info(f"Wallet created for user: {instance.phone}")
        
        except ImportError:
            # Wallet app not installed yet
            logger.warning("Wallet app not available, skipping wallet creation")
        
        except Exception as e:
            logger.error(f"Error creating wallet for {instance.phone}: {e}")


@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """
    لاگ ایجاد کاربر جدید
    """
    if created:
        logger.info(f"New user registered: {instance.phone}")
