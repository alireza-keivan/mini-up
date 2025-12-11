# apps/accounts/adapters.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.core.files.base import ContentFile
from django.contrib import messages
import requests
import logging

logger = logging.getLogger(__name__)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    آداپتور سفارشی برای دریافت حداکثر اطلاعات از گوگل
    """
    
    def populate_user(self, request, sociallogin, data):
        """
        پر کردن اطلاعات کاربر از داده‌های گوگل
        این متد قبل از ذخیره کاربر فراخوانی می‌شود
        """
        user = super().populate_user(request, sociallogin, data)
        
        # دریافت اطلاعات از extra_data گوگل
        extra_data = sociallogin.account.extra_data
        
        # ذخیره نام
        user.first_name = extra_data.get('given_name', '') or data.get('first_name', '')
        user.last_name = extra_data.get('family_name', '') or data.get('last_name', '')
        
        # ایمیل
        user.email = extra_data.get('email', '') or data.get('email', '')
        
        logger.info(f"Populated user from Google: {user.email}, {user.first_name} {user.last_name}")
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        ذخیره کاربر و دانلود عکس پروفایل
        """
        user = super().save_user(request, sociallogin, form)
        
        # دریافت اطلاعات اضافی از گوگل
        extra_data = sociallogin.account.extra_data
        
        # ذخیره عکس پروفایل
        picture_url = extra_data.get('picture')
        if picture_url:
            self._save_avatar_from_google(user, picture_url)
        
        # پیام خوش‌آمدگویی
        if user.first_name:
            messages.success(request, f'🎉 {user.first_name} عزیز، خوش آمدید!')
        else:
            messages.success(request, '🎉 خوش آمدید! ثبت‌نام شما با موفقیت انجام شد.')
        
        logger.info(f"New user created from Google: {user.email}")
        
        return user
    
    def _save_avatar_from_google(self, user, picture_url):
        """
        دانلود و ذخیره عکس پروفایل از گوگل
        """
        try:
            # اطمینان از وجود پروفایل
            if not hasattr(user, 'profile') or not user.profile:
                return
            
            # تغییر URL برای دریافت عکس با کیفیت بالاتر
            # پیش‌فرض گوگل 96x96 است، ما 400x400 می‌خواهیم
            if '=s96-c' in picture_url:
                picture_url = picture_url.replace('=s96-c', '=s400-c')
            elif '?' not in picture_url:
                picture_url += '?sz=400'
            
            # دانلود عکس
            response = requests.get(picture_url, timeout=10)
            response.raise_for_status()
            
            # ذخیره عکس
            filename = f'google_avatar_{user.id}.jpg'
            user.profile.avatar.save(
                filename,
                ContentFile(response.content),
                save=True
            )
            
            logger.info(f"Avatar saved for user {user.id}")
            
        except requests.RequestException as e:
            logger.warning(f"Failed to download Google avatar: {e}")
        except Exception as e:
            logger.error(f"Error saving avatar: {e}")
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        مدیریت خطاهای احراز هویت
        """
        logger.error(f"Social auth error: provider={provider_id}, error={error}, exception={exception}")
        messages.error(request, 'متأسفانه ورود با گوگل با مشکل مواجه شد. لطفاً دوباره تلاش کنید.')
        super().authentication_error(request, provider_id, error, exception, extra_context)


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    آداپتور سفارشی برای مدیریت اکانت‌ها
    """
    
    def get_login_redirect_url(self, request):
        """
        تعیین صفحه ریدایرکت بعد از ورود
        """
        # اگر صفحه قبلی در session یا GET وجود دارد
        next_url = request.GET.get('next') or request.session.get('next')
        if next_url:
            # حذف از session
            if 'next' in request.session:
                del request.session['next']
            return next_url
        
        # پیش‌فرض: صفحه اصلی
        return '/'
    
    def get_signup_redirect_url(self, request):
        """
        ریدایرکت بعد از ثبت‌نام - همان صفحه اصلی
        """
        return self.get_login_redirect_url(request)
    
    def get_logout_redirect_url(self, request):
        """
        ریدایرکت بعد از خروج
        """
        return '/'
