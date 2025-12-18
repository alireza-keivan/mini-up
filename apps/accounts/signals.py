# apps/accounts/signals.py

"""
Signals for Accounts App

- Auto-create Profile when user registers
- Auto-create Wallet when user registers
- Log user activities
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_related_objects(sender, instance, created, **kwargs):
    """
    ایجاد خودکار Profile و Wallet برای کاربر جدید
    این سیگنال هم برای کاربران موبایلی و هم گوگلی کار می‌کند
    
    نکته: از get_or_create استفاده می‌کنیم تا اگر قبلاً ساخته شده، تکرار نشود
    """
    if not created:
        return
    
    # شناسه کاربر برای لاگ
    user_identifier = instance.phone or instance.email or f"ID:{instance.id}"
    auth_method = "Google" if instance.auth_provider == User.AuthProvider.GOOGLE else "Phone"
    
    # ۱. ایجاد پروفایل
    try:
        from .models import Profile
        profile, profile_created = Profile.objects.get_or_create(user=instance)
        if profile_created:
            logger.info(f"✅ Profile created for user: {user_identifier}")
        else:
            logger.debug(f"Profile already exists for user: {user_identifier}")
    except Exception as e:
        logger.error(f"❌ Error creating profile for {user_identifier}: {e}")
    
    # ۲. ایجاد کیف پول
    try:
        from apps.wallet.models import Wallet
        wallet, wallet_created = Wallet.objects.get_or_create(user=instance)
        if wallet_created:
            logger.info(f"✅ Wallet created for user: {user_identifier}")
        else:
            logger.debug(f"Wallet already exists for user: {user_identifier}")
    except ImportError:
        logger.warning("⚠️ Wallet app not available, skipping wallet creation")
    except Exception as e:
        logger.error(f"❌ Error creating wallet for {user_identifier}: {e}")
    
    # ۳. لاگ ثبت‌نام
    logger.info(f"🎉 New user registered via {auth_method}: {user_identifier}")
