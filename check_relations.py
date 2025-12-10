#!/usr/bin/env python
"""
check_relations.py
بررسی صحت روابط بین مدل‌های Django

اجرا: python check_relations.py
"""

import os
import sys
import django

# ============================================
# پیکربندی Django - این بخش حیاتی است!
# ============================================

# تنظیم مسیر پروژه
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# تنظیم متغیر محیطی Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miniup.settings.development')

# راه‌اندازی Django
django.setup()

# ============================================
# حالا می‌توانیم از مدل‌ها استفاده کنیم
# ============================================

from django.apps import apps
from django.db.models import OneToOneField, ForeignKey, ManyToManyField


def check_all_relations():
    """بررسی تمام روابط در پروژه"""
    
    print("\n" + "=" * 60)
    print("🔍 گزارش کامل روابط مدل‌ها")
    print("=" * 60)
    
    # لیست اپ‌های پروژه
    my_apps = ['accounts', 'wallet', 'core', 'products', 'orders', 'payments']
    
    for app_name in my_apps:
        try:
            app_config = apps.get_app_config(app_name)
            models = app_config.get_models()
            
            print(f"\n📦 اپلیکیشن: {app_name}")
            print("-" * 40)
            
            for model in models:
                print(f"\n  📋 مدل: {model.__name__}")
                
                # پیدا کردن روابط
                relations = []
                for field in model._meta.get_fields():
                    if isinstance(field, OneToOneField):
                        relations.append(f"    🔗 OneToOne → {field.related_model.__name__} (field: {field.name})")
                    elif isinstance(field, ForeignKey):
                        relations.append(f"    🔗 ForeignKey → {field.related_model.__name__} (field: {field.name})")
                    elif isinstance(field, ManyToManyField):
                        relations.append(f"    🔗 ManyToMany ↔ {field.related_model.__name__} (field: {field.name})")
                
                # روابط معکوس
                for field in model._meta.get_fields():
                    if field.is_relation and field.auto_created and not field.concrete:
                        if hasattr(field, 'related_model') and field.related_model:
                            relations.append(f"    ↩️  Reverse از {field.related_model.__name__} (name: {field.name})")
                
                if relations:
                    for rel in relations:
                        print(rel)
                else:
                    print("    (بدون رابطه)")
                    
        except LookupError:
            print(f"  ⚠️ اپ {app_name} یافت نشد یا مدلی ندارد")
    
    print("\n" + "=" * 60)


def test_relations_integrity():
    """تست صحت داده‌ای روابط"""
    
    from apps.accounts.models import User, Profile
    from apps.wallet.models import Wallet
    
    print("\n" + "=" * 60)
    print("🧪 تست صحت داده‌ای روابط")
    print("=" * 60)
    
    errors = []
    
    # --- بررسی Users بدون Profile ---
    users_without_profile = []
    for user in User.objects.all():
        try:
            _ = user.profile
        except Profile.DoesNotExist:
            users_without_profile.append(user)
    
    if users_without_profile:
        print(f"\n❌ کاربران بدون Profile ({len(users_without_profile)}):")
        for u in users_without_profile[:5]:
            print(f"   - User ID: {u.id} | {u.phone or u.email or 'N/A'}")
        if len(users_without_profile) > 5:
            print(f"   ... و {len(users_without_profile) - 5} مورد دیگر")
        errors.append("users_without_profile")
    else:
        print("\n✅ همه کاربران Profile دارند")
    
    # --- بررسی Users بدون Wallet ---
    users_without_wallet = []
    for user in User.objects.all():
        try:
            _ = user.wallet
        except Wallet.DoesNotExist:
            users_without_wallet.append(user)
    
    if users_without_wallet:
        print(f"\n❌ کاربران بدون Wallet ({len(users_without_wallet)}):")
        for u in users_without_wallet[:5]:
            print(f"   - User ID: {u.id} | {u.phone or u.email or 'N/A'}")
        if len(users_without_wallet) > 5:
            print(f"   ... و {len(users_without_wallet) - 5} مورد دیگر")
        errors.append("users_without_wallet")
    else:
        print("\n✅ همه کاربران Wallet دارند")
    
    # --- بررسی Profiles یتیم (بدون User معتبر) ---
    orphan_profiles = Profile.objects.filter(user__isnull=True)
    if orphan_profiles.exists():
        print(f"\n❌ Profile‌های بدون User: {orphan_profiles.count()}")
        errors.append("orphan_profiles")
    else:
        print("\n✅ همه Profile‌ها User معتبر دارند")
    
    # --- بررسی Wallets یتیم ---
    orphan_wallets = Wallet.objects.filter(user__isnull=True)
    if orphan_wallets.exists():
        print(f"\n❌ Wallet‌های بدون User: {orphan_wallets.count()}")
        errors.append("orphan_wallets")
    else:
        print("\n✅ همه Wallet‌ها User معتبر دارند")
    
    # --- آمار کلی ---
    print("\n" + "-" * 40)
    print("📊 آمار کلی:")
    print(f"   👥 تعداد کاربران: {User.objects.count()}")
    print(f"   👤 تعداد پروفایل‌ها: {Profile.objects.count()}")
    print(f"   💰 تعداد کیف پول‌ها: {Wallet.objects.count()}")
    
    return errors


def fix_missing_relations(dry_run=True):
    """ایجاد Profile و Wallet برای کاربران فاقد آن"""
    
    from apps.accounts.models import User, Profile
    from apps.wallet.models import Wallet
    
    print("\n" + "=" * 60)
    if dry_run:
        print("🔍 شبیه‌سازی اصلاح روابط (بدون تغییر واقعی)")
    else:
        print("🔧 اصلاح روابط ناقص")
    print("=" * 60)
    
    to_create_profiles = 0
    to_create_wallets = 0
    
    for user in User.objects.all():
        # چک Profile
        try:
            _ = user.profile
        except Profile.DoesNotExist:
            to_create_profiles += 1
            if not dry_run:
                Profile.objects.create(user=user)
        
        # چک Wallet
        try:
            _ = user.wallet
        except Wallet.DoesNotExist:
            to_create_wallets += 1
            if not dry_run:
                Wallet.objects.create(user=user)
    
    if dry_run:
        print(f"\n📋 نیاز به ایجاد {to_create_profiles} پروفایل")
        print(f"📋 نیاز به ایجاد {to_create_wallets} کیف پول")
        if to_create_profiles > 0 or to_create_wallets > 0:
            print("\n💡 برای اصلاح، اسکریپت را با --fix اجرا کنید")
    else:
        print(f"\n✅ {to_create_profiles} پروفایل جدید ایجاد شد")
        print(f"✅ {to_create_wallets} کیف پول جدید ایجاد شد")


def main():
    """تابع اصلی"""
    import argparse
    
    parser = argparse.ArgumentParser(description='بررسی صحت روابط مدل‌های Django')
    parser.add_argument('--fix', action='store_true', help='اصلاح روابط ناقص')
    parser.add_argument('--skip-structure', action='store_true', help='عدم نمایش ساختار روابط')
    args = parser.parse_args()
    
    print("\n" + "🚀 شروع بررسی روابط..." + "\n")
    
    # بررسی ساختار روابط
    if not args.skip_structure:
        check_all_relations()
    
    # بررسی صحت داده‌ای
    errors = test_relations_integrity()
    
    # اصلاح روابط
    if errors:
        fix_missing_relations(dry_run=not args.fix)
    
    # نتیجه نهایی
    print("\n" + "=" * 60)
    if not errors:
        print("✅ همه روابط صحیح هستند!")
    else:
        print(f"⚠️ {len(errors)} مشکل یافت شد")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
