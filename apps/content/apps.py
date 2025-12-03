# apps/content/apps.py

from django.apps import AppConfig


class ContentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.content'
    verbose_name = 'مدیریت محتوا'

    def ready(self):
        """Import signals when app is ready"""
        try:
            from . import signals  # noqa: F401
        except ImportError:
            pass
