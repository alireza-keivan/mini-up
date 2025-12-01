# apps/products/apps.py

from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.products'
    verbose_name = 'مدیریت محصولات'

    def ready(self):
        """Import signals when app is ready."""
        try:
            from apps.products import signals  # noqa: F401
        except ImportError:
            pass
