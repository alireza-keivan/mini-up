# apps/consulting/apps.py

from django.apps import AppConfig


class ConsultingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.consulting'
    label = 'consulting'
    verbose_name = 'مشاوره'

    def ready(self):
        """
        بارگذاری سیگنال‌ها هنگام آماده شدن اپلیکیشن
        """
        try:
            import apps.consulting.signals  # noqa: F401
        except ImportError:
            pass
