# apps/orders/apps.py

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'مدیریت سفارشات'

    def ready(self):
        """Import signals when app is ready"""
        try:
            from . import signals  # noqa: F401
        except ImportError:
            pass