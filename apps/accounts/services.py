# apps/accounts/services.py

"""
Authentication services for Mini-up.
Handles OTP generation, verification, SMS sending, and user authentication.
"""

import random
import string
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth import login, logout

from .models import User, OTP, UserActivity

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# SMS SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class SMSService:
    """
    سرویس ارسال پیامک
    
    در حالت توسعه، کد OTP در کنسول چاپ می‌شود.
    در production از سرویس‌هایی مثل کاوه‌نگار یا ملی‌پیامک استفاده کنید.
    """
    
    # تنظیمات از settings
    API_KEY = getattr(settings, 'SMS_API_KEY', None)
    SENDER = getattr(settings, 'SMS_SENDER', None)
    IS_ENABLED = getattr(settings, 'SMS_ENABLED', False)
    
    @classmethod
    def send_otp(cls, phone: str, code: str) -> dict:
        """
        ارسال کد OTP به شماره موبایل
        
        Args:
            phone: شماره موبایل (09xxxxxxxxx)
            code: کد OTP
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        message = f"کد تایید شما در مینی‌آپ: {code}\nاین کد تا ۲ دقیقه معتبر است."
        
        # در حالت توسعه
        if settings.DEBUG or not cls.IS_ENABLED:
            logger.info(f"📱 [DEV MODE] SMS to {phone}: {code}")
            print(f"\n{'='*50}")
            print(f"📱 کد OTP برای {phone}: {code}")
            print(f"{'='*50}\n")
            return {'success': True, 'message': 'کد در کنسول چاپ شد (حالت توسعه)'}
        
        # ═══════════════════════════════════════════════════════════════════
        # در production یکی از این‌ها را فعال کنید:
        # ═══════════════════════════════════════════════════════════════════
        
        # --- کاوه‌نگار ---
        # try:
        #     import requests
        #     url = f"https://api.kavenegar.com/v1/{cls.API_KEY}/verify/lookup.json"
        #     data = {
        #         'receptor': phone,
        #         'token': code,
        #         'template': 'miniup-verify'  # نام قالب در پنل کاوه‌نگار
        #     }
        #     response = requests.post(url, data=data, timeout=10)
        #     result = response.json()
        #     if result.get('return', {}).get('status') == 200:
        #         return {'success': True, 'message': 'کد ارسال شد'}
        #     else:
        #         return {'success': False, 'message': result.get('return', {}).get('message', 'خطا')}
        # except Exception as e:
        #     logger.error(f"Kavenegar Error: {e}")
        #     return {'success': False, 'message': str(e)}
        
        # --- ملی پیامک ---
        # try:
        #     import requests
        #     url = "https://rest.payamak-panel.com/api/SendSMS/SendSMS"
        #     data = {
        #         'username': cls.API_KEY,
        #         'password': cls.SENDER,
        #         'to': phone,
        #         'from': '50004001234567',
        #         'text': message,
        #         'isflash': False
        #     }
        #     response = requests.post(url, data=data, timeout=10)
        #     return {'success': True, 'message': 'کد ارسال شد'}
        # except Exception as e:
        #     logger.error(f"MeliPayamak Error: {e}")
        #     return {'success': False, 'message': str(e)}
        
        return {'success': True, 'message': 'کد ارسال شد'}
    
    @classmethod
    def send_welcome(cls, phone: str, name: str = '') -> dict:
        """ارسال پیام خوش‌آمدگویی"""
        message = f"سلام{' ' + name if name else ''}! به مینی‌آپ خوش آمدید 🎮"
        
        if settings.DEBUG:
            logger.info(f"📱 [DEV] Welcome SMS to {phone}: {message}")
            return {'success': True, 'message': 'sent in dev mode'}
        
        return {'success': True, 'message': 'sent'}


# ═══════════════════════════════════════════════════════════════════════════════
# OTP SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class OTPService:
    """
    سرویس مدیریت کد یکبار مصرف (OTP)
    
    ویژگی‌ها:
    - ایجاد و اعتبارسنجی OTP
    - محدودیت نرخ ارسال (Rate Limiting)
    - محدودیت تعداد تلاش
    """
    
    # تنظیمات
    OTP_LENGTH = getattr(settings, 'OTP_LENGTH', 5)
    OTP_EXPIRE_SECONDS = getattr(settings, 'OTP_EXPIRE_SECONDS', 120)  # 2 دقیقه
    MAX_ATTEMPTS = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)
    COOLDOWN_SECONDS = getattr(settings, 'OTP_COOLDOWN_SECONDS', 60)  # 1 دقیقه بین هر ارسال
    MAX_DAILY_REQUESTS = getattr(settings, 'OTP_MAX_DAILY_REQUESTS', 10)
    
    @classmethod
    def generate_code(cls) -> str:
        """تولید کد عددی تصادفی"""
        return ''.join(random.choices(string.digits, k=cls.OTP_LENGTH))
    
    @classmethod
    def get_rate_limit_key(cls, phone: str) -> str:
        """کلید کش برای rate limiting"""
        return f"otp_cooldown_{phone}"
    
    @classmethod
    def get_daily_count_key(cls, phone: str) -> str:
        """کلید کش برای شمارش روزانه"""
        today = timezone.now().strftime('%Y%m%d')
        return f"otp_daily_{phone}_{today}"
    
    @classmethod
    def check_rate_limit(cls, phone: str) -> dict:
        """
        بررسی محدودیت نرخ ارسال
        
        Returns:
            dict: {'allowed': bool, 'wait_seconds': int, 'message': str}
        """
        # بررسی cooldown (فاصله بین ارسال‌ها)
        cooldown_key = cls.get_rate_limit_key(phone)
        last_request = cache.get(cooldown_key)
        
        if last_request:
            elapsed = (timezone.now() - last_request).total_seconds()
            remaining = int(cls.COOLDOWN_SECONDS - elapsed)
            if remaining > 0:
                return {
                    'allowed': False,
                    'wait_seconds': remaining,
                    'message': f'لطفاً {remaining} ثانیه صبر کنید'
                }
        
        # بررسی تعداد درخواست روزانه
        daily_key = cls.get_daily_count_key(phone)
        daily_count = cache.get(daily_key, 0)
        
        if daily_count >= cls.MAX_DAILY_REQUESTS:
            return {
                'allowed': False,
                'wait_seconds': 0,
                'message': 'تعداد درخواست‌های روزانه به حد مجاز رسیده است'
            }
        
        return {'allowed': True, 'wait_seconds': 0, 'message': ''}
    
    @classmethod
    @transaction.atomic
    def create_and_send(cls, phone: str, purpose: str = OTP.Purpose.LOGIN) -> dict:
        """
        ایجاد OTP جدید و ارسال پیامک
        
        Args:
            phone: شماره موبایل
            purpose: هدف (login, register, reset, verify_phone)
            
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'otp_id': int (در صورت موفقیت),
                'expires_in': int (ثانیه تا انقضا)
            }
        """
        # بررسی محدودیت نرخ
        rate_check = cls.check_rate_limit(phone)
        if not rate_check['allowed']:
            return {
                'success': False,
                'message': rate_check['message'],
                'wait_seconds': rate_check['wait_seconds']
            }
        
        # غیرفعال کردن OTPهای قبلی
        OTP.objects.filter(
            phone=phone,
            is_used=False,
            expires_at__gt=timezone.now()
        ).update(is_used=True)
        
        # ایجاد OTP جدید
        code = cls.generate_code()
        otp = OTP.objects.create(
            phone=phone,
            code=code,
            purpose=purpose,
            expires_at=timezone.now() + timedelta(seconds=cls.OTP_EXPIRE_SECONDS)
        )
        
        # ارسال پیامک
        sms_result = SMSService.send_otp(phone, code)
        
        if not sms_result['success']:
            # اگر ارسال ناموفق بود، OTP را حذف کن
            otp.delete()
            return {
                'success': False,
                'message': sms_result['message']
            }
        
        # ذخیره در کش برای rate limiting
        cache.set(
            cls.get_rate_limit_key(phone),
            timezone.now(),
            cls.COOLDOWN_SECONDS
        )
        
        # افزایش شمارنده روزانه
        daily_key = cls.get_daily_count_key(phone)
        daily_count = cache.get(daily_key, 0)
        cache.set(daily_key, daily_count + 1, 86400)  # 24 ساعت
        
        logger.info(f"OTP created for {phone}, purpose: {purpose}")
        
        return {
            'success': True,
            'message': 'کد تایید ارسال شد',
            'otp_id': otp.id,
            'expires_in': cls.OTP_EXPIRE_SECONDS
        }
    
    @classmethod
    def verify(cls, phone: str, code: str, purpose: str = None) -> dict:
        """
        تایید کد OTP
        
        Args:
            phone: شماره موبایل
            code: کد وارد شده توسط کاربر
            purpose: هدف (اختیاری - برای فیلتر دقیق‌تر)
            
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'user': User object (اگر موجود باشد)
            }
        """
        # پیدا کردن OTP معتبر
        filters = {
            'phone': phone,
            'is_used': False,
            'expires_at__gt': timezone.now()
        }
        if purpose:
            filters['purpose'] = purpose
        
        otp = OTP.objects.filter(**filters).order_by('-created_at').first()
        
        if not otp:
            return {
                'success': False,
                'message': 'کد منقضی شده یا نامعتبر است'
            }
        
        # بررسی تعداد تلاش
        if otp.attempts >= cls.MAX_ATTEMPTS:
            otp.is_used = True
            otp.save()
            return {
                'success': False,
                'message': 'تعداد تلاش‌ها به حد مجاز رسید. لطفاً کد جدید دریافت کنید'
            }
        
        # تایید کد
        if otp.verify(code):
            # پیدا کردن کاربر
            user = User.objects.filter(phone=phone).first()
            
            logger.info(f"OTP verified for {phone}")
            
            return {
                'success': True,
                'message': 'کد تایید شد',
                'user': user,
                'is_new_user': user is None
            }
        else:
            remaining = cls.MAX_ATTEMPTS - otp.attempts
            return {
                'success': False,
                'message': f'کد اشتباه است. {remaining} تلاش باقی‌مانده'
            }
    
    @classmethod
    def get_remaining_time(cls, phone: str) -> int:
        """
        دریافت زمان باقی‌مانده تا امکان ارسال مجدد
        
        Returns:
            int: ثانیه‌های باقی‌مانده (0 اگر مجاز است)
        """
        cooldown_key = cls.get_rate_limit_key(phone)
        last_request = cache.get(cooldown_key)
        
        if not last_request:
            return 0
        
        elapsed = (timezone.now() - last_request).total_seconds()
        remaining = int(cls.COOLDOWN_SECONDS - elapsed)
        
        return max(0, remaining)


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class AuthService:
    """
    سرویس احراز هویت OTP-Only
    
    فلوی کامل:
    1. کاربر شماره موبایل وارد می‌کند
    2. OTP ارسال می‌شود
    3. کاربر OTP را وارد می‌کند
    4. اگر کاربر وجود دارد → لاگین
    """
    @classmethod
    def start_login(cls, phone: str) -> dict:
        """
        مرحله ۱: دریافت شماره موبایل و ارسال OTP

        Returns:
            dict {
                success,
                message,
                otp_id (If success),
                expires_in,
                wait_seconds
            }
        """
        phone = phone.strip()

        if not (phone.startswith("09") and len(phone) == 11):
            return {'success': False, 'message': 'شماره موبایل نامعتبر است'}

        # ایجاد و ارسال OTP
        result = OTPService.create_and_send(phone, OTP.Purpose.LOGIN)

        return result

    @classmethod
    @transaction.atomic
    def verify_and_login(cls, request, phone: str, code: str) -> dict:
        """
        مرحله ۲: تایید OTP و ورود یا ثبت‌نام خودکار

        Returns:
            dict {
                success,
                message,
                is_new_user,
                redirect_url
            }
        """

        verify = OTPService.verify(phone=phone, code=code, purpose=OTP.Purpose.LOGIN)

        if not verify['success']:
            return verify

        user = verify.get('user')
        is_new = False

        # اگر کاربر وجود ندارد → ایجاد کاربر جدید
        if not user:
            user = User.objects.create_user(
                phone=phone,
                username=f"user_{phone}",
                is_active=True
            )
            is_new = True

            # پیام خوش‌آمد
            SMSService.send_welcome(phone)

            # ثبت فعالیت
            UserActivity.objects.create(
                user=user,
                action=UserActivity.Action.REGISTER,
                description="ثبت نام با OTP"
            )
        else:
            # ثبت فعالیت ورود
            UserActivity.objects.create(
                user=user,
                action=UserActivity.Action.LOGIN,
                description="ورود با OTP"
            )

        # ورود به سیستم
        login(request, user)

        logger.info(f"User logged in: {phone} (new={is_new})")

        return {
            'success': True,
            'message': 'با موفقیت وارد شدید',
            'is_new_user': is_new,
            'redirect_url': settings.LOGIN_REDIRECT_URL or '/'
        }

    @classmethod
    def logout_user(cls, request):
        """خروج کاربر"""
        from django.contrib.auth import logout
        from apps.accounts.models import UserActivity
        
        user = request.user
        
        if user.is_authenticated:
            try:
                # ثبت فعالیت خروج
                UserActivity.objects.create(
                    user=user,
                    activity_type=UserActivity.ActivityType.LOGOUT,  # ✅ استفاده صحیح از Enum
                    ip_address=cls._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    description='خروج از سیستم'
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not log user activity: {e}")
            
            # خروج کاربر
            logout(request)
        
        return {'success': True, 'message': 'خارج شدید'}
    
    @staticmethod
    def _get_client_ip(request):
        """دریافت IP کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip