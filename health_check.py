# health_check.py

"""
Backend Health Check Script
Run: python health_check.py
"""

import os
import sys

# اضافه کردن root پروژه به path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# تشخیص خودکار settings module
POSSIBLE_SETTINGS = [
    'miniup.settings.development',
    'miniup.settings.dev',
    'miniup.settings.local',
    'miniup.settings',
    'config.settings.development',
    'config.settings',
    'settings',
]

settings_module = None
for setting in POSSIBLE_SETTINGS:
    try:
        __import__(setting)
        settings_module = setting
        break
    except ImportError:
        continue

if not settings_module:
    # اگر هیچ‌کدام پیدا نشد، از فایل‌های موجود بخوان
    print("⚠️  Could not auto-detect settings module.")
    print("   Checking for settings files...")
    
    # بررسی ساختار
    if os.path.exists(os.path.join(BASE_DIR, 'miniup', 'settings.py')):
        settings_module = 'miniup.settings'
    elif os.path.exists(os.path.join(BASE_DIR, 'miniup', 'settings', '__init__.py')):
        settings_module = 'miniup.settings'
    elif os.path.exists(os.path.join(BASE_DIR, 'miniup', 'settings', 'base.py')):
        # Settings تقسیم شده - باید development یا production باشد
        if os.path.exists(os.path.join(BASE_DIR, 'miniup', 'settings', 'development.py')):
            settings_module = 'miniup.settings.development'
        elif os.path.exists(os.path.join(BASE_DIR, 'miniup', 'settings', 'dev.py')):
            settings_module = 'miniup.settings.dev'
        else:
            print("❌ No development settings found!")
            print("   Please create: miniup/settings/development.py")
            sys.exit(1)
    else:
        print("❌ Cannot find Django settings!")
        sys.exit(1)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

import django
try:
    django.setup()
    print(f"✅ Using settings: {settings_module}")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

from django.core.management import call_command
from django.db import connection
from io import StringIO


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def check_system():
    """Run Django system checks."""
    print_header("۱. System Check")
    try:
        output = StringIO()
        call_command('check', stdout=output, stderr=output)
        result = output.getvalue()
        if 'no issues' in result.lower() or not result.strip():
            print("✅ System check passed - No issues found")
            return True
        else:
            print(f"⚠️  Issues found:\n{result}")
            return False
    except Exception as e:
        print(f"❌ System check failed: {e}")
        return False


def check_database():
    """Check database connection."""
    print_header("۲. Database Connection")
    try:
        connection.ensure_connection()
        print(f"✅ Database connected: {connection.vendor}")
        print(f"   Database name: {connection.settings_dict.get('NAME', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def check_migrations():
    """Check migration status."""
    print_header("۳. Migration Status")
    try:
        output = StringIO()
        call_command('showmigrations', '--plan', stdout=output)
        migrations = output.getvalue()
        
        unapplied = [line for line in migrations.split('\n') if line.strip().startswith('[ ]')]
        applied = [line for line in migrations.split('\n') if line.strip().startswith('[X]')]
        
        print(f"✅ Applied migrations: {len(applied)}")
        
        if unapplied:
            print(f"⚠️  Unapplied migrations: {len(unapplied)}")
            for m in unapplied[:5]:
                print(f"   - {m.strip()}")
            if len(unapplied) > 5:
                print(f"   ... and {len(unapplied) - 5} more")
            return False
        else:
            print("✅ All migrations applied")
            return True
    except Exception as e:
        print(f"❌ Migration check failed: {e}")
        return False


def check_apps():
    """Check all installed apps."""
    print_header("۴. Installed Apps")
    from django.apps import apps
    
    local_apps = [
        'apps.core',
        'apps.accounts', 
        'apps.products',
        'apps.orders',
        'apps.payments',
        'apps.wallet',
        'apps.coupons',
        'apps.consulting',
        'apps.content',
    ]
    
    all_ok = True
    for app_name in local_apps:
        try:
            app_config = apps.get_app_config(app_name.split('.')[-1])
            models_count = len(list(app_config.get_models()))
            print(f"✅ {app_name}: {models_count} models")
        except Exception as e:
            print(f"❌ {app_name}: {e}")
            all_ok = False
    
    return all_ok


def check_models():
    """Check model integrity."""
    print_header("۵. Model Integrity")
    from django.apps import apps
    
    total_models = 0
    errors = []
    
    for app_config in apps.get_app_configs():
        if app_config.name.startswith('apps.'):
            for model in app_config.get_models():
                total_models += 1
                try:
                    # Try to access model's meta
                    _ = model._meta.db_table
                    _ = model._meta.get_fields()
                except Exception as e:
                    errors.append(f"{model.__name__}: {e}")
    
    print(f"✅ Total models checked: {total_models}")
    
    if errors:
        print(f"❌ Errors found: {len(errors)}")
        for err in errors:
            print(f"   - {err}")
        return False
    else:
        print("✅ All models OK")
        return True


def check_admin():
    """Check admin registration."""
    print_header("۶. Admin Registration")
    from django.contrib import admin
    
    registered = list(admin.site._registry.keys())
    local_models = [m for m in registered if m.__module__.startswith('apps.')]
    
    print(f"✅ Total registered models: {len(registered)}")
    print(f"✅ Local app models in admin: {len(local_models)}")
    
    # List by app
    apps_models = {}
    for model in local_models:
        app = model._meta.app_label
        if app not in apps_models:
            apps_models[app] = []
        apps_models[app].append(model.__name__)
    
    for app, models in sorted(apps_models.items()):
        print(f"   📁 {app}: {', '.join(models)}")
    
    return True


def check_urls():
    """Check URL configuration."""
    print_header("۷. URL Configuration")
    try:
        from django.urls import get_resolver
        resolver = get_resolver()
        
        url_patterns = []
        def extract_urls(patterns, prefix=''):
            for pattern in patterns:
                if hasattr(pattern, 'url_patterns'):
                    extract_urls(pattern.url_patterns, prefix + str(pattern.pattern))
                else:
                    url_patterns.append(prefix + str(pattern.pattern))
        
        extract_urls(resolver.url_patterns)
        
        print(f"✅ Total URL patterns: {len(url_patterns)}")
        
        # Key URLs check
        key_urls = ['admin/', 'api/', 'accounts/', 'products/', 'orders/', 'wallet/', 'payments/']
        for url in key_urls:
            found = any(url in p for p in url_patterns)
            status = "✅" if found else "⚠️ "
            print(f"   {status} {url}")
        
        return True
    except Exception as e:
        print(f"❌ URL check failed: {e}")
        return False


def check_settings():
    """Check important settings."""
    print_header("۸. Settings Check")
    from django.conf import settings
    
    checks = [
        ('DEBUG', settings.DEBUG, 'Boolean'),
        ('AUTH_USER_MODEL', getattr(settings, 'AUTH_USER_MODEL', 'NOT SET'), 'accounts.User'),
        ('TIME_ZONE', settings.TIME_ZONE, 'Asia/Tehran'),
        ('LANGUAGE_CODE', settings.LANGUAGE_CODE, 'fa-ir'),
        ('STATIC_URL', settings.STATIC_URL, '/static/'),
        ('MEDIA_URL', settings.MEDIA_URL, '/media/'),
    ]
    
    for name, value, expected in checks:
        status = "✅" if str(value) == str(expected) or expected == 'Boolean' else "⚠️ "
        print(f"   {status} {name}: {value}")
    
    return True


def run_health_check():
    """Run all health checks."""
    print("\n" + "🏥 MINIUP BACKEND HEALTH CHECK 🏥".center(60))
    print("=" * 60)
    
    results = {
        'System Check': check_system(),
        'Database': check_database(),
        'Migrations': check_migrations(),
        'Apps': check_apps(),
        'Models': check_models(),
        'Admin': check_admin(),
        'URLs': check_urls(),
        'Settings': check_settings(),
    }
    
    # Summary
    print_header("📊 SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {check}")
    
    print(f"\n{'='*60}")
    print(f"   Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("   🎉 ALL CHECKS PASSED! Backend is healthy.")
    else:
        print("   ⚠️  Some checks failed. Please review above.")
    
    print("=" * 60 + "\n")
    
    return passed == total


if __name__ == '__main__':
    success = run_health_check()
    sys.exit(0 if success else 1)
