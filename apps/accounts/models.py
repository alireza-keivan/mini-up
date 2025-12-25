# Create your models here.
"""
User management models for Mini-up.
Custom user model with phone-based authentication and OTP verification.
"""

import random
import string
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    """Custom user manager for phone-based authentication only."""
    
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
    
    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('is_phone_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('سوپریوزر باید is_staff=True داشته باشد')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('سوپریوزر باید is_superuser=True داشته باشد')
        
        return self.create_user(phone=phone, password=password, **extra_fields)
    
    def create_google_user(self, google_id, email, **extra_fields):
        """ایجاد کاربر از طریق Google OAuth"""
        if not google_id:
            raise ValueError('google_id الزامی است')
        if not email:
            raise ValueError('ایمیل الزامی است')
        
        extra_fields.setdefault('auth_provider', 'google')
        extra_fields.setdefault('is_email_verified', True)
        
        return self.create_user(email=email, google_id=google_id, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with phone-based authentication and Google OAuth.
    Users can login with phone number OTP or Google account.
    """
    
    phone_regex = RegexValidator(
        regex=r'^09\d{9}$',
        message='شماره موبایل باید با ۰۹ شروع شده و ۱۱ رقم باشد'
    )
    
    class AuthProvider(models.TextChoices):
        PHONE = 'phone', 'شماره موبایل'
        GOOGLE = 'google', 'گوگل'
    
    phone = models.CharField(
        max_length=11,
        unique=True,
        null=True,          # ✅ اجازه NULL برای کاربران گوگل
        blank=True,
        validators=[phone_regex],
        verbose_name='شماره موبایل'
    )
    
    email = models.EmailField(
        unique=True,
        null=True,          # ✅ اجازه NULL برای کاربران موبایل
        blank=True,
        verbose_name='ایمیل'
    )
    
    # Google OAuth info (populated when user logs in via Google)
    google_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        verbose_name='شناسه گوگل'
    )
    avatar_url = models.URLField(
        null=True,
        blank=True,
        verbose_name='آدرس آواتار گوگل'
    )
    
    
    auth_provider = models.CharField(
        max_length=10,
        choices=AuthProvider.choices,
        default=AuthProvider.PHONE,
        verbose_name='روش ثبت‌نام'
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
    is_email_verified = models.BooleanField(
        default=False, 
        verbose_name='ایمیل تایید شده'
        )
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
    
    def clean(self):
        """اعتبارسنجی قبل از ذخیره"""
        super().clean()
        
        # نرمال‌سازی ایمیل
        if self.email:
            self.email = self.email.lower().strip()
        
        # حداقل یکی از phone یا email باید پر باشد
        if not self.phone and not self.email:
            raise ValidationError(
                'حداقل یکی از فیلدهای شماره موبایل یا ایمیل باید پر شود.'
            )
            
    def save(self, *args, **kwargs):
        # تولید کد معرفی یکتا
        self.full_clean()
        if not self.referral_code:
            self.referral_code = self._generate_referral_code()
        super().save(*args, **kwargs)
    
    def get_full_name(self):
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.phone or self.email or f'کاربر {self.pk}'
    
    def get_short_name(self):
        return self.first_name or self.phone or self.email
    
    def _generate_referral_code(self):
        """Generate a unique 8-character referral code."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not User.objects.filter(referral_code=code).exists():
                return code
            
    @property
    def is_google_user(self):
        """آیا کاربر با گوگل ثبت‌نام کرده؟"""
        return self.auth_provider == self.AuthProvider.GOOGLE
    
    @property
    def has_google_linked(self):
        """آیا حساب گوگل متصل است؟"""
        return bool(self.google_id)
    
    @property
    def wallet_balance(self):
        """Get user's current wallet balance."""
        from apps.wallet.models import Wallet
        wallet, _ = Wallet.objects.get_or_create(user=self)
        return wallet.balance
    
    def get_avatar_url(self):
        """دریافت URL آواتار (محلی یا گوگل)"""
        if self.avatar:
            return self.avatar.url
        if self.avatar_url:
            return self.avatar_url
        return None
    
    def get_display_name(self):
        """نام نمایشی برای UI"""
        if self.first_name:
            return self.first_name
        if self.phone:
            return f'کاربر {self.phone[-4:]}'
        if self.email:
            return self.email.split('@')[0]
        return f'کاربر {self.pk}'


class OTP(models.Model):
    """
    One-Time Password for phone verification and login.
    """
    
    class Purpose(models.TextChoices):
        LOGIN = 'login', 'ورود'
        REGISTER = 'register', 'ثبت نام'
        VERIFY_PHONE = 'verify_phone', 'تایید موبایل'
    
    phone = models.CharField(max_length=11, verbose_name='شماره موبایل')
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
        return f'{self.phone} - {self.code}'
    
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


class Profile(models.Model):
    """
    Extended user profile information.
    Automatically created for each user via signal.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='کاربر'
    )
    
    # Profile verification status
    is_verified = models.BooleanField(default=False, verbose_name='تایید هویت')
    national_code_verified = models.BooleanField(default=False, verbose_name='کد ملی تایید شده')
    
    # Additional personal info
    national_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='کد ملی'
    )
    
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاریخ تولد'
    )
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'مرد'), ('female', 'زن'), ('other', 'سایر')],
        blank=True,
        verbose_name='جنسیت'
    )
    bio = models.TextField(blank=True, max_length=500, verbose_name='درباره من')
    national_id = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='کد ملی'
    )
    # Location info (from form, not address model)
    city = models.CharField(max_length=50, blank=True, verbose_name='شهر')
    postal_code = models.CharField(max_length=10, blank=True, verbose_name='کد پستی')
    address = models.TextField(blank=True, verbose_name='آدرس')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'پروفایل'
        verbose_name_plural = 'پروفایل‌ها'
    
    def __str__(self):
        return f'پروفایل {self.user}'
    
    @property
    def avatar(self):
        """Return user's avatar from User model."""
        return self.user.avatar
    
    @property
    def completion_percentage(self):
        """Calculate profile completion percentage."""
        fields = [
            self.user.first_name,
            self.user.last_name,
            self.user.email,
            self.user.avatar,
            self.national_code,
            self.user.date_of_birth,
            self.gender,
            self.city,
        ]
        filled = sum(1 for f in fields if f)
        return int((filled / len(fields)) * 100)


class BankCard(models.Model):
    """
    User bank cards for wallet withdrawals.
    Card numbers are stored masked for security.
    Bank is auto-detected from card number BIN.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bank_cards',
        verbose_name='کاربر'
    )
    
    # Card information
    card_number = models.CharField(max_length=16, verbose_name='شماره کارت')
    bank_name = models.CharField(max_length=100, blank=True, verbose_name='نام بانک')
    is_default = models.BooleanField(default=False, verbose_name='کارت پیش‌فرض')
    is_verified = models.BooleanField(default=False, verbose_name='تایید شده')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'کارت بانکی'
        verbose_name_plural = 'کارت‌های بانکی'
        ordering = ['-is_default', '-created_at']
        unique_together = [['user', 'card_number']]
    
    def __str__(self):
        return f'{self.masked_number} - {self.bank_name}'
    
    @property
    def masked_number(self):
        """Return masked card number (e.g., 1234 - **** - **** - 6037)."""
        if len(self.card_number) == 16:
            # Format: Last 4 digits - **** - **** - First 4 digits
            return f'{self.card_number[-4:]} - **** - **** - {self.card_number[:4]}'
        return self.card_number
    
    @property
    def bank_info(self):
        """Get complete bank information from card number."""
        from .bank_utils import detect_bank_from_card_number
        return detect_bank_from_card_number(self.card_number)
    
    @property
    def bank_logo_icon(self):
        """Get bank logo icon class."""
        info = self.bank_info
        return info['logo'] if info else 'fa-university'
    
    @property
    def bank_color(self):
        """Get bank brand color."""
        info = self.bank_info
        return info['color'] if info else '#999999'
    
    @property
    def bank_full_name(self):
        """Get bank full name."""
        info = self.bank_info
        return info['full_name'] if info else self.bank_name or 'بانک نامشخص'
    
    def detect_and_set_bank(self):
        """Detect bank from card number and set bank_name."""
        from .bank_utils import detect_bank_from_card_number
        bank_info = detect_bank_from_card_number(self.card_number)
        if bank_info:
            self.bank_name = bank_info['name']
        return self.bank_name
    
    def save(self, *args, **kwargs):
        # Auto-detect bank if not set
        if not self.bank_name or self.bank_name == 'سایر':
            self.detect_and_set_bank()
        
        # Ensure only one default card per user
        if self.is_default:
            BankCard.objects.filter(user=self.user, is_default=True).update(is_default=False)
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
