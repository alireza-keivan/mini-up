from django.db import models
from django.core.validators import URLValidator


class SocialMediaLinks(models.Model):
    """
    لینک‌های شبکه‌های اجتماعی - تنها یک رکورد باید وجود داشته باشد
    """
    instagram = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='اینستاگرام (username)',
        help_text='فقط نام کاربری را وارد کنید: مثلا minigame.shop'
    )
    telegram = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='تلگرام (username)',
        help_text='فقط نام کاربری را وارد کنید: مثلا miniupir'
    )
    youtube = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='یوتیوب (channel name)',
        help_text='فقط نام کانال را وارد کنید: مثلا minigame_org'
    )
    whatsapp = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='واتساپ (شماره یا لینک)',
        help_text='شماره تلفن یا لینک واتساپ'
    )
    twitter = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='توییتر/X (username)',
        help_text='فقط نام کاربری را وارد کنید'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'لینک شبکه اجتماعی'
        verbose_name_plural = 'لینک‌های شبکه‌های اجتماعی'

    def __str__(self):
        return 'لینک‌های شبکه‌های اجتماعی'

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SocialMediaLinks.objects.exists():
            # Update existing instance
            existing = SocialMediaLinks.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)

    @property
    def instagram_url(self):
        return f'https://instagram.com/{self.instagram}' if self.instagram else ''

    @property
    def telegram_url(self):
        return f'https://t.me/{self.telegram}' if self.telegram else ''

    @property
    def youtube_url(self):
        return f'https://youtube.com/@{self.youtube}' if self.youtube else ''

    @property
    def whatsapp_url(self):
        if self.whatsapp:
            if self.whatsapp.startswith('http'):
                return self.whatsapp
            else:
                return f'https://wa.me/{self.whatsapp.replace("+", "").replace(" ", "")}'
        return ''

    @property
    def twitter_url(self):
        return f'https://twitter.com/{self.twitter}' if self.twitter else ''


class YouTubeVideo(models.Model):
    """
    ویدیوی معرفی از یوتیوب - تنها یک رکورد باید وجود داشته باشد
    """
    video_url = models.URLField(
        max_length=500,
        verbose_name='لینک ویدیو یوتیوب',
        help_text='لینک کامل ویدیو یوتیوب را وارد کنید: مثلا https://www.youtube.com/watch?v=VIDEO_ID'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='عنوان ویدیو',
        help_text='عنوان نمایشی برای ویدیو'
    )
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات',
        help_text='توضیح کوتاه درباره ویدیو'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال',
        help_text='ویدیو در صفحه اصلی نمایش داده شود؟'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'ویدیوی یوتیوب'
        verbose_name_plural = 'ویدیوهای یوتیوب'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Ensure only one active instance exists
        if self.is_active:
            YouTubeVideo.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @property
    def video_id(self):
        """Extract YouTube video ID from URL"""
        import re
        if 'youtube.com/watch?v=' in self.video_url:
            return self.video_url.split('watch?v=')[1].split('&')[0]
        elif 'youtu.be/' in self.video_url:
            return self.video_url.split('youtu.be/')[1].split('?')[0]
        elif 'youtube.com/embed/' in self.video_url:
            return self.video_url.split('embed/')[1].split('?')[0]
        return None

    @property
    def embed_url(self):
        """Get embeddable YouTube URL"""
        video_id = self.video_id
        if video_id:
            return f'https://www.youtube.com/embed/{video_id}'
        return ''

    @property
    def thumbnail_url(self):
        """Get video thumbnail URL"""
        video_id = self.video_id
        if video_id:
            return f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
        return ''


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
