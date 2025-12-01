# Create your models here.
"""
User management models for Mini-up.
Custom user model with phone-based authentication and OTP verification.
"""

import random
import string
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    """Custom user manager for phone-based authentication."""
    
    def create_user(self, phone=None, email=None, password=None, **extra_fields):
        if not phone and not email:
            raise ValueError('کاربر باید شماره موبایل یا ایمیل داشته باشد')
        
        if email:
            email = self.normalize_email(email)
        
        user = self.model(phone=phone, email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('سوپریوزر باید is_staff=True داشته باشد')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('سوپریوزر باید is_superuser=True داشته باشد')
        
        return self.create_user(phone, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with phone-based authentication.
    Users can login with phone number or email.
    """
    
    phone_regex = RegexValidator(
        regex=r'^09\d{9}$',
        message='شماره موبایل باید با ۰۹ شروع شده و ۱۱ رقم باشد'
    )
    
    phone = models.CharField(
        max_length=11,
        unique=True,
        null=True,
        blank=True,
        validators=[phone_regex],
        verbose_name='شماره موبایل'
    )
    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
        verbose_name='ایمیل'
    )
    
    # Profile info
    first_name = models.CharField(max_length=50, blank=True, verbose_name='نام')
    last_name = models.CharField(max_length=50, blank=True, verbose_name='نام خانوادگی')
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='تصویر پروفایل'
    )
    date_of_birth = models.DateField(null=True, blank=True, verbose_name='تاریخ تولد')
    
    # Verification status
    is_phone_verified = models.BooleanField(default=False, verbose_name='موبایل تایید شده')
    is_email_verified = models.BooleanField(default=False, verbose_name='ایمیل تایید شده')
    is_verified = models.BooleanField(default=False, verbose_name='تایید شده')
    
    # Referral system
    referral_code = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        verbose_name='کد معرفی'
    )
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals',
        verbose_name='معرف'
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_staff = models.BooleanField(default=False, verbose_name='کارمند')
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='تاریخ عضویت')
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='آخرین ورود')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    objects = UserManager()
    
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.phone or self.email or f'User {self.pk}'
    
    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.phone or self.email
    
    def get_short_name(self):
        return self.first_name or self.phone or self.email
    
    def save(self, *args, **kwargs):
        # Generate unique referral code
        if not self.referral_code:
            self.referral_code = self._generate_referral_code()
        super().save(*args, **kwargs)
    
    def _generate_referral_code(self):
        """Generate a unique 8-character referral code."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not User.objects.filter(referral_code=code).exists():
                return code
    
    @property
    def wallet_balance(self):
        """Get user's current wallet balance."""
        from apps.wallet.models import Wallet
        wallet, _ = Wallet.objects.get_or_create(user=self)
        return wallet.balance


class OTP(models.Model):
    """
    One-Time Password for phone/email verification and login.
    """
    
    class Purpose(models.TextChoices):
        LOGIN = 'login', 'ورود'
        REGISTER = 'register', 'ثبت نام'
        RESET_PASSWORD = 'reset', 'بازیابی رمز'
        VERIFY_PHONE = 'verify_phone', 'تایید موبایل'
        VERIFY_EMAIL = 'verify_email', 'تایید ایمیل'
    
    phone = models.CharField(max_length=11, null=True, blank=True, verbose_name='شماره موبایل')
    email = models.EmailField(null=True, blank=True, verbose_name='ایمیل')
    code = models.CharField(max_length=6, verbose_name='کد')
    purpose = models.CharField(
        max_length=20,
        choices=Purpose.choices,
        default=Purpose.LOGIN,
        verbose_name='هدف'
    )
    
    is_used = models.BooleanField(default=False, verbose_name='استفاده شده')
    attempts = models.PositiveSmallIntegerField(default=0, verbose_name='تعداد تلاش')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    expires_at = models.DateTimeField(verbose_name='تاریخ انقضا')
    
    class Meta:
        verbose_name = 'کد یکبار مصرف'
        verbose_name_plural = 'کدهای یکبار مصرف'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.phone or self.email} - {self.code}'
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_code()
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(
                seconds=getattr(settings, 'OTP_EXPIRE_SECONDS', 120)
            )
        super().save(*args, **kwargs)
    
    def _generate_code(self):
        """Generate numeric OTP code."""
        length = getattr(settings, 'OTP_LENGTH', 5)
        return ''.join(random.choices(string.digits, k=length))
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired and self.attempts < 5
    
    def verify(self, code):
        """Verify the OTP code."""
        self.attempts += 1
        self.save(update_fields=['attempts'])
        
        if not self.is_valid:
            return False
        
        if self.code == code:
            self.is_used = True
            self.save(update_fields=['is_used'])
            return True
        
        return False


class Address(models.Model):
    """User shipping addresses."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name='کاربر'
    )
    
    title = models.CharField(max_length=50, default='خانه', verbose_name='عنوان')
    recipient_name = models.CharField(max_length=100, verbose_name='نام گیرنده')
    recipient_phone = models.CharField(max_length=11, verbose_name='شماره گیرنده')
    
    province = models.CharField(max_length=50, verbose_name='استان')
    city = models.CharField(max_length=50, verbose_name='شهر')
    postal_code = models.CharField(max_length=10, verbose_name='کد پستی')
    full_address = models.TextField(verbose_name='آدرس کامل')
    
    is_default = models.BooleanField(default=False, verbose_name='آدرس پیش‌فرض')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'آدرس'
        verbose_name_plural = 'آدرس‌ها'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f'{self.title} - {self.city}'
    
    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class UserActivity(models.Model):
    """Track user activities for analytics and security."""
    
    class ActivityType(models.TextChoices):
        LOGIN = 'login', 'ورود'
        LOGOUT = 'logout', 'خروج'
        REGISTER = 'register', 'ثبت نام'
        PASSWORD_CHANGE = 'password_change', 'تغییر رمز'
        PROFILE_UPDATE = 'profile_update', 'بروزرسانی پروفایل'
        ORDER_PLACED = 'order_placed', 'ثبت سفارش'
        WALLET_TOPUP = 'wallet_topup', 'شارژ کیف پول'
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name='کاربر'
    )
    activity_type = models.CharField(
        max_length=30,
        choices=ActivityType.choices,
        verbose_name='نوع فعالیت'
    )
    description = models.TextField(blank=True, verbose_name='توضیحات')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='آی‌پی')
    user_agent = models.TextField(blank=True, verbose_name='مرورگر')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ')
    
    class Meta:
        verbose_name = 'فعالیت کاربر'
        verbose_name_plural = 'فعالیت‌های کاربران'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user} - {self.activity_type}'
