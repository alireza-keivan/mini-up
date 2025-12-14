# apps/content/models.py

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import MinLengthValidator


# ═══════════════════════════════════════════════════════════════════════════════
# BLOG / ARTICLES
# ═══════════════════════════════════════════════════════════════════════════════

class ArticleCategory(models.Model):
    """
    دسته‌بندی مقالات
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='نام دسته‌بندی')
    slug = models.SlugField(max_length=120, unique=True, allow_unicode=True, verbose_name='نامک')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    icon = models.CharField(max_length=50, blank=True, verbose_name='آیکون')
    image = models.ImageField(
        upload_to='content/categories/',
        blank=True,
        null=True,
        verbose_name='تصویر'
    )
    
    # Parent for nested categories
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='دسته‌بندی والد'
    )
    
    # SEO
    meta_title = models.CharField(max_length=70, blank=True, verbose_name='عنوان متا')
    meta_description = models.CharField(max_length=160, blank=True, verbose_name='توضیحات متا')
    
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'دسته‌بندی مقاله'
        verbose_name_plural = 'دسته‌بندی‌های مقالات'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    @property
    def article_count(self):
        return self.articles.filter(status='published').count()


class ArticleTag(models.Model):
    """
    تگ‌های مقالات
    
    نحوه ارتباط با مقالات:
    - ارتباط Many-to-Many: هر مقاله می‌تواند چند تگ داشته باشد و هر تگ می‌تواند به چند مقاله متصل باشد
    - نام تگ: برای نمایش (مثلاً "گیمینگ")
    - نامک (slug): برای URL و جستجو (مثلاً "gaming" یا "گیمینگ")
    - استفاده: در مقاله از طریق فیلد tags به تگ‌ها متصل می‌شود
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name='نام تگ',
        help_text='نام نمایشی تگ که در سایت نمایش داده می‌شود'
    )
    slug = models.SlugField(
        max_length=60, 
        unique=True, 
        allow_unicode=True, 
        verbose_name='نامک',
        help_text='شناسه یکتا برای URL - به صورت خودکار از نام تگ تولید می‌شود'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'تگ'
        verbose_name_plural = 'تگ‌ها'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
    
    @property
    def article_count(self):
        """تعداد مقالات منتشر شده با این تگ"""
        return self.articles.filter(status='published').count()


class Article(models.Model):
    """
    مقالات و پست‌های بلاگ
    """
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'پیش‌نویس'
        PENDING = 'pending', 'در انتظار تأیید'
        PUBLISHED = 'published', 'منتشر شده'
        ARCHIVED = 'archived', 'آرشیو شده'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Content
    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(5)],
        verbose_name='عنوان'
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        allow_unicode=True,
        verbose_name='نامک'
    )
    excerpt = models.TextField(
        max_length=300,
        blank=True,
        verbose_name='خلاصه',
        help_text='خلاصه کوتاه برای نمایش در لیست'
    )
    content = models.TextField(verbose_name='محتوا')
    
    # Media
    featured_image = models.ImageField(
        upload_to='content/articles/',
        blank=True,
        null=True,
        verbose_name='تصویر شاخص'
    )
    featured_image_alt = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='متن جایگزین تصویر'
    )
    
    # Relations
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='articles',
        verbose_name='نویسنده'
    )
    category = models.ForeignKey(
        ArticleCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name='دسته‌بندی'
    )
    tags = models.ManyToManyField(
        ArticleTag,
        blank=True,
        related_name='articles',
        verbose_name='تگ‌ها',
        help_text='تگ‌های مرتبط با این مقاله را انتخاب کنید. هر مقاله می‌تواند چند تگ داشته باشد.'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name='وضعیت'
    )
    
    # Publishing
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='تاریخ انتشار'
    )
    
    # SEO
    meta_title = models.CharField(max_length=70, blank=True, verbose_name='عنوان متا')
    meta_description = models.CharField(max_length=160, blank=True, verbose_name='توضیحات متا')
    meta_keywords = models.CharField(max_length=200, blank=True, verbose_name='کلمات کلیدی')
    canonical_url = models.URLField(blank=True, verbose_name='URL کنونیکال')
    
    # Statistics
    view_count = models.PositiveIntegerField(default=0, verbose_name='تعداد بازدید')
    
    # Settings
    allow_comments = models.BooleanField(default=True, verbose_name='اجازه کامنت')
    is_featured = models.BooleanField(default=False, verbose_name='مقاله ویژه')
    is_pinned = models.BooleanField(default=False, verbose_name='سنجاق شده')
    
    # Reading time (auto-calculated)
    reading_time = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='زمان مطالعه (دقیقه)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'مقاله'
        verbose_name_plural = 'مقالات'
        ordering = ['-is_pinned', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['category', 'status']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        
        # Auto-set published_at
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        
        # Calculate reading time (average 200 words per minute for Persian)
        if self.content:
            word_count = len(self.content.split())
            self.reading_time = max(1, round(word_count / 200))
        
        super().save(*args, **kwargs)

    def publish(self):
        """انتشار مقاله"""
        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at', 'updated_at'])

    def increment_view(self):
        """افزایش تعداد بازدید"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED


class ArticleImage(models.Model):
    """
    تصاویر اضافی مقاله (گالری تصاویر)
    هر مقاله می‌تواند چند تصویر داشته باشد
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='مقاله'
    )
    
    image = models.ImageField(
        upload_to='content/articles/gallery/',
        verbose_name='تصویر'
    )
    alt_text = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='متن جایگزین',
        help_text='توضیح تصویر برای SEO و دسترسی‌پذیری'
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='عنوان تصویر',
        help_text='توضیح کوتاه که زیر تصویر نمایش داده می‌شود'
    )
    
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='ترتیب نمایش'
    )
    
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ آپلود')

    class Meta:
        verbose_name = 'تصویر مقاله'
        verbose_name_plural = 'تصاویر مقالات'
        ordering = ['article', 'order']

    def __str__(self):
        return f'تصویر {self.order} - {self.article.title[:30]}'


class ArticleComment(models.Model):
    """
    کامنت‌های مقالات
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار تأیید'
        APPROVED = 'approved', 'تأیید شده'
        REJECTED = 'rejected', 'رد شده'
        SPAM = 'spam', 'اسپم'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='مقاله'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='article_comments',
        verbose_name='کاربر'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='پاسخ به'
    )
    
    content = models.TextField(
        max_length=1000,
        validators=[MinLengthValidator(3)],
        verbose_name='متن کامنت'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='وضعیت'
    )
    
    like_count = models.PositiveIntegerField(default=0, verbose_name='تعداد لایک')
    
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='آدرس IP')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'کامنت مقاله'
        verbose_name_plural = 'کامنت‌های مقالات'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} در {self.article.title[:30]}'

    def approve(self):
        self.status = self.Status.APPROVED
        self.save(update_fields=['status', 'updated_at'])

    def reject(self):
        self.status = self.Status.REJECTED
        self.save(update_fields=['status', 'updated_at'])


# ═══════════════════════════════════════════════════════════════════════════════
# STATIC PAGES
# ═══════════════════════════════════════════════════════════════════════════════

class Page(models.Model):
    """
    صفحات استاتیک سایت
    مانند: درباره ما، تماس با ما، قوانین، حریم خصوصی
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    title = models.CharField(max_length=200, verbose_name='عنوان')
    slug = models.SlugField(
        max_length=220,
        unique=True,
        allow_unicode=True,
        verbose_name='نامک',
        help_text='آدرس صفحه: /page/your-slug/'
    )
    
    content = models.TextField(verbose_name='محتوا')
    
    # Optional featured image
    featured_image = models.ImageField(
        upload_to='content/pages/',
        blank=True,
        null=True,
        verbose_name='تصویر'
    )
    
    # SEO
    meta_title = models.CharField(max_length=70, blank=True, verbose_name='عنوان متا')
    meta_description = models.CharField(max_length=160, blank=True, verbose_name='توضیحات متا')
    
    # Template (optional custom template)
    template_name = models.CharField(
        max_length=100,
        blank=True,
        default='content/page_detail.html',
        verbose_name='قالب',
        help_text='مسیر فایل قالب سفارشی'
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_in_footer = models.BooleanField(default=False, verbose_name='نمایش در فوتر')
    is_in_header = models.BooleanField(default=False, verbose_name='نمایش در هدر')
    
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'صفحه'
        verbose_name_plural = 'صفحات'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True) 
            super().save(*args, **kwargs)
            
# ═══════════════════════════════════════════════════════════════════════════════
# FAQ (سوالات متداول)
# ═══════════════════════════════════════════════════════════════════════════════

class FAQItem(models.Model):
    """
    سوالات متداول
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    question = models.CharField(max_length=300, verbose_name='سؤال')
    answer = models.TextField(verbose_name='پاسخ')

    category = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='دسته (اختیاری)'
    )

    is_active = models.BooleanField(default=True, verbose_name='فعال')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'سوال متداول'
        verbose_name_plural = 'سوالات متداول'
        ordering = ['order', 'question']

    def __str__(self):
        return self.question


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS (اعلان‌های سیستمی)
# ═══════════════════════════════════════════════════════════════════════════════

class SystemNotification(models.Model):
    """
    اعلان‌های سیستمی داخلی برای کاربران
    مثل: پیام‌های اطلاع‌رسانی، هشدارها، خبرها
    """

    class NotificationType(models.TextChoices):
        INFO = 'info', 'اطلاعات'
        SUCCESS = 'success', 'موفقیت'
        WARNING = 'warning', 'هشدار'
        ERROR = 'error', 'خطا'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=200, verbose_name='عنوان')
    message = models.TextField(verbose_name='متن اعلان')

    type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        verbose_name='نوع اعلان'
    )

    # ارسال برای همه یا برای یک کاربر خاص
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='کاربر مقصد'
    )
    send_to_all = models.BooleanField(default=False, verbose_name='ارسال برای همه کاربران')

    # وضعیت خوانده شده
    is_read = models.BooleanField(default=False, verbose_name='خوانده شده')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ خوانده شدن')

    # نمایش
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ انقضا')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'اعلان'
        verbose_name_plural = 'اعلان‌های سیستمی'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at

    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])