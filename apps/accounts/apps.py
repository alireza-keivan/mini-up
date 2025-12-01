from django.apps import AppConfig


# apps/accounts/apps.py
class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    label = 'accounts'
    verbose_name = 'حساب‌های کاربری'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import apps.accounts.signals  # noqa
        except ImportError:
            pass