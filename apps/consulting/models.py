# apps/consulting/models.py

"""
Consulting App Models

سیستم مشاوره شامل:
- Consultant: مشاوران
- ConsultingCategory: دسته‌بندی مشاوره‌ها
- TimeSlot: بازه‌های زمانی قابل رزرو
- Appointment: نوبت‌های رزرو شده
- ConsultantReview: نظرات کاربران
"""

import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class ConsultingCategory(models.Model):
    """
    دسته‌بندی مشاوره‌ها
    مثال: روانشناسی، حقوقی، مالی، تحصیلی، ...
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(
        max_length=100,
        verbose_name='نام دسته‌بندی'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        allow_unicode=True,
        verbose_name='اسلاگ'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='آیکون',
        help_text='نام آیکون (مثلاً: psychology, gavel, account_balance)'
    )
    
    image = models.ImageField(
        upload_to='consulting/categories/',
        blank=True,
        null=True,
        verbose_name='تصویر'
    )
    
    # Settings
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='ترتیب')
    
    # SEO
    meta_title = models.CharField(max_length=60, blank=True, verbose_name='عنوان متا')
    meta_description = models.CharField(max_length=160, blank=True, verbose_name='توضیحات متا')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'دسته‌بندی مشاوره'
        verbose_name_plural = 'دسته‌بندی‌های مشاوره'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def consultant_count(self):
        """تعداد مشاوران فعال این دسته"""
        return self.consultants.filter(is_active=True, is_verified=True).count()


class Consultant(models.Model):
    """
    مشاور
    هر مشاور یک کاربر است با اطلاعات تخصصی اضافه
    """
    
    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'در انتظار تایید'
        VERIFIED = 'verified', 'تایید شده'
        REJECTED = 'rejected', 'رد شده'
        SUSPENDED = 'suspended', 'تعلیق شده'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User relation
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consultant_profile',
        verbose_name='کاربر'
    )
    
    # Categories (M2M)
    categories = models.ManyToManyField(
        ConsultingCategory,
        related_name='consultants',
        verbose_name='تخصص‌ها'
    )
    
    # Professional info
    title = models.CharField(
        max_length=100,
        verbose_name='عنوان تخصصی',
        help_text='مثال: روانشناس بالینی، وکیل پایه یک دادگستری'
    )
    
    bio = models.TextField(
        verbose_name='درباره من',
        help_text='معرفی کوتاه (حداکثر ۵۰۰ کاراکتر)'
    )
    
    experience_years = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='سال‌های تجربه'
    )
    
    education = models.TextField(
        blank=True,
        verbose_name='تحصیلات',
        help_text='مدارک تحصیلی (هر مدرک در یک خط)'
    )
    
    certifications = models.TextField(
        blank=True,
        verbose_name='گواهینامه‌ها',
        help_text='گواهینامه‌های حرفه‌ای'
    )
    
    # Profile
    profile_image = models.ImageField(
        upload_to='consulting/consultants/profiles/',
        blank=True,
        null=True,
        verbose_name='تصویر پروفایل'
    )
    
    cover_image = models.ImageField(
        upload_to='consulting/consultants/covers/',
        blank=True,
        null=True,
        verbose_name='تصویر کاور'
    )
    
    # Pricing (per minute)
    price_per_minute = models.PositiveIntegerField(
        default=5000,
        validators=[MinValueValidator(1000)],
        verbose_name='قیمت هر دقیقه (تومان)'
    )
    
    # Session settings
    min_session_duration = models.PositiveSmallIntegerField(
        default=15,
        verbose_name='حداقل مدت جلسه (دقیقه)'
    )
    
    max_session_duration = models.PositiveSmallIntegerField(
        default=60,
        verbose_name='حداکثر مدت جلسه (دقیقه)'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال',
        help_text='آیا مشاور در حال حاضر فعال است؟'
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name='تایید شده'
    )
    
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        verbose_name='وضعیت تایید'
    )
    
    is_online = models.BooleanField(
        default=False,
        verbose_name='آنلاین',
        help_text='آیا مشاور الان آنلاین است؟'
    )
    
    is_available = models.BooleanField(
        default=True,
        verbose_name='در دسترس',
        help_text='آیا امکان رزرو وقت دارد؟'
    )
    
    # Statistics
    total_sessions = models.PositiveIntegerField(default=0, verbose_name='تعداد جلسات')
    total_hours = models.DecimalField(
        max_digits=8,
        decimal_places=1,
        default=0,
        verbose_name='ساعات مشاوره'
    )
    
    # Rating (cached)
    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name='امتیاز'
    )
    review_count = models.PositiveIntegerField(default=0, verbose_name='تعداد نظرات')
    
    # Verification docs (admin only)
    national_id_image = models.ImageField(
        upload_to='consulting/consultants/docs/',
        blank=True,
        null=True,
        verbose_name='تصویر کارت ملی'
    )
    
    license_image = models.ImageField(
        upload_to='consulting/consultants/docs/',
        blank=True,
        null=True,
        verbose_name='تصویر پروانه کار'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تایید')
    last_online_at = models.DateTimeField(null=True, blank=True, verbose_name='آخرین آنلاین')
    
    class Meta:
        verbose_name = 'مشاور'
        verbose_name_plural = 'مشاوران'
        ordering = ['-rating', '-total_sessions']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.phone} - {self.title}"
    
    @property
    def display_name(self):
        """نام نمایشی مشاور"""
        return self.user.get_full_name() or f"مشاور {str(self.id)[:8]}"
    
    @property
    def session_price_15(self):
        """قیمت جلسه ۱۵ دقیقه‌ای"""
        return self.price_per_minute * 15
    
    @property
    def session_price_30(self):
        """قیمت جلسه ۳۰ دقیقه‌ای"""
        return self.price_per_minute * 30
    
    @property
    def session_price_60(self):
        """قیمت جلسه ۶۰ دقیقه‌ای"""
        return self.price_per_minute * 60
    
    def update_rating(self):
        """بروزرسانی امتیاز بر اساس نظرات"""
        from django.db.models import Avg, Count
        
        stats = self.reviews.filter(is_approved=True).aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        
        self.rating = stats['avg_rating'] or 0
        self.review_count = stats['count']
        self.save(update_fields=['rating', 'review_count'])


class TimeSlot(models.Model):
    """
    بازه زمانی قابل رزرو
    مشاوران می‌توانند زمان‌های کاری خود را تعریف کنند
    """
    
    class SlotStatus(models.TextChoices):
        AVAILABLE = 'available', 'آزاد'
        BOOKED = 'booked', 'رزرو شده'
        BLOCKED = 'blocked', 'بلاک شده'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    consultant = models.ForeignKey(
        Consultant,
        on_delete=models.CASCADE,
        related_name='time_slots',
        verbose_name='مشاور'
    )
    
    # Time
    date = models.DateField(verbose_name='تاریخ')
    start_time = models.TimeField(verbose_name='ساعت شروع')
    end_time = models.TimeField(verbose_name='ساعت پایان')
    
    # Duration in minutes
    duration = models.PositiveSmallIntegerField(
        default=30,
        verbose_name='مدت (دقیقه)'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=SlotStatus.choices,
        default=SlotStatus.AVAILABLE,
        verbose_name='وضعیت'
    )
    
    # Price override (optional)
    custom_price = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='قیمت سفارشی',
        help_text='اگر خالی باشد از قیمت پیش‌فرض مشاور استفاده می‌شود'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'بازه زمانی'
        verbose_name_plural = 'بازه‌های زمانی'
        ordering = ['date', 'start_time']
        unique_together = ['consultant', 'date', 'start_time']
    
    def __str__(self):
        return f"{self.consultant.display_name} - {self.date} {self.start_time}"
    
    @property
    def price(self):
        """قیمت این بازه"""
        if self.custom_price:
            return self.custom_price
        return self.consultant.price_per_minute * self.duration
    
    @property
    def is_past(self):
        """آیا این بازه گذشته است؟"""
        from datetime import datetime
        slot_datetime = datetime.combine(self.date, self.start_time)
        return timezone.make_aware(slot_datetime) < timezone.now()
    
    @property
    def is_available(self):
        """آیا قابل رزرو است؟"""
        return (
            self.status == self.SlotStatus.AVAILABLE and
            not self.is_past
        )

class Appointment(models.Model):
    """
    نوبت مشاوره
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار پرداخت'
        WAITING = 'waiting', 'در انتظار شروع'
        IN_PROGRESS = 'in_progress', 'در حال برگزاری'
        COMPLETED = 'completed', 'تکمیل شده'
        CANCELLED = 'cancelled', 'لغو شده'
        FAILED = 'failed', 'ناموفق'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='کاربر'
    )

    consultant = models.ForeignKey(
        Consultant,
        on_delete=models.PROTECT,
        related_name='appointments',
        verbose_name='مشاور'
    )

    slot = models.OneToOneField(
        TimeSlot,
        on_delete=models.PROTECT,
        related_name='appointment',
        verbose_name='بازه زمانی'
    )

    # Pricing
    price = models.PositiveIntegerField(
        verbose_name='قیمت نهایی (تومان)'
    )

    # Session info
    session_link = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='لینک جلسه'
    )

    description = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='توضیحات کاربر'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='وضعیت'
    )

    # Payment
    payment_transaction = models.ForeignKey(
        'payments.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consulting_appointments',
        verbose_name='تراکنش پرداخت'
    )

    # Rating / review link
    has_review = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'نوبت مشاوره'
        verbose_name_plural = 'نوبت‌های مشاوره'
        ordering = ['-created_at']

    def __str__(self):
        return f'نوبت {self.id} - {self.consultant.display_name}'

    @property
    def duration(self):
        return self.slot.duration

    @property
    def is_paid(self):
        return self.payment_transaction and self.payment_transaction.is_successful

    def mark_as_paid(self, transaction):
        self.payment_transaction = transaction
        self.status = self.Status.WAITING
        self.save()

    def start_session(self):
        self.status = self.Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()

    def complete_session(self):
        self.status = self.Status.COMPLETED
        self.finished_at = timezone.now()
        self.save()


class ConsultantReview(models.Model):
    """
    نظرات کاربران برای مشاور
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name='نوبت'
    )

    consultant = models.ForeignKey(
        Consultant,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='مشاور'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consulting_reviews',
        verbose_name='کاربر'
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='امتیاز'
    )

    comment = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='نظر'
    )

    is_approved = models.BooleanField(
        default=True,
        verbose_name='تایید شده'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'نظر مشاوره'
        verbose_name_plural = 'نظرات مشاوره'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.rating}⭐ - {self.consultant.display_name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update consultant rating
        self.consultant.update_rating()