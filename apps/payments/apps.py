from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payments'
    verbose_name = 'پرداخت‌ها'
    
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            from . import signals  # noqa: F401
        except ImportError:
            pass
