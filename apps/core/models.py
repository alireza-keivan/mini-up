from django.db import models


class ServiceDescription(models.Model):
    """
    توضیحات چهارگانه پایین صفحه اصلی
    """
    class ServiceType(models.TextChoices):
        VIRTUAL = 'virtual', 'خدمات مجازی'
        MINI_GAME = 'mini_game', 'مینی گیم'
        GAMING_PRODUCTS = 'gaming_products', 'محصولات گیمینگ'
        ACCESSORIES = 'accessories', 'لوازم جانبی'

    service_type = models.CharField(
        max_length=50,
        choices=ServiceType.choices,
        unique=True,
        verbose_name='نوع خدمت'
    )
    title = models.CharField(max_length=100, verbose_name='عنوان')
    description = models.TextField(verbose_name='توضیحات')
    icon = models.ImageField(
        upload_to='services/icons/',
        blank=True,
        null=True,
        verbose_name='آیکون (اختیاری)'
    )
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'توضیح خدمت'
        verbose_name_plural = 'توضیحات خدمات'

    def __str__(self):
        return self.get_service_type_display()
