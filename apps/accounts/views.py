# apps/accounts/views.py

"""
Authentication Views for Mini-up
OTP-Only Authentication System
"""

import json
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings

from .services import AuthService, OTPService
from .models import User, Profile, Address, BankCard

logger = logging.getLogger(__name__)

def normalize_phone(phone: str) -> str:
    """Normalize Iranian mobile numbers"""
    if not phone:
        return ''

    # Convert Persian/Arabic digits to English
    persian = '۰۱۲۳۴۵۶۷۸۹'
    arabic = '٠١٢٣٤٥٦٧٨٩'
    english = '0123456789'

    trans = str.maketrans(persian + arabic, english + english)
    phone = phone.translate(trans)

    # Remove non-digits
    phone = ''.join(ch for ch in phone if ch.isdigit())

    if phone.startswith('0098'):
        phone = phone[4:]
    elif phone.startswith('098'):
        phone = phone[3:]
    elif phone.startswith('98'):
        phone = phone[2:]
    elif phone.startswith('+98'):
        phone = phone[3:]

    if phone.startswith('9') and len(phone) == 10:
        phone = '0' + phone

    if len(phone) == 11 and phone.startswith('09'):
        return phone

    return ''

def mask_phone(phone: str) -> str:
    """Mask middle digits (0912***6789)"""
    if phone and len(phone) == 11:
        return phone[:4] + '***' + phone[-4:]
    return phone or ''

def mask_email(email: str) -> str:
    """Mask email (te***@gmail.com)"""
    if not email or '@' not in email:
        return email or ''
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked = local[0] + '***'
    else:
        masked = local[:2] + '***'
    return f"{masked}@{domain}"


def get_user_identifier(user) -> str:
    """Get display identifier for user (phone or email)"""
    return user.phone or user.email or f"User {user.id}"


# ============================================================================
# ACCOUNTS INDEX - Redirect to appropriate page
# ============================================================================

class AccountsIndexView(View):
    """
    Base /accounts/ route handler.
    Redirects authenticated users to dashboard/profile.
    Redirects guests to login.
    """
    def get(self, request):
        if request.user.is_authenticated:
            # Redirect to dashboard or profile
            return redirect('accounts:dashboard')

        return redirect('accounts:login')


# ============================================================================
# LOGIN VIEW
# ============================================================================

class LoginView(View):
    template_name = 'accounts/login.html'
   
    def get(self, request):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL or '/')

        return render(request, self.template_name, {
            'page_title': 'ورود به مینی‌آپ',
            'google_oauth_enabled': getattr(settings, 'GOOGLE_OAUTH_ENABLED', False),
        })
    def post(self, request):
        # Parse JSON or form data
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                phone = data.get('phone', '').strip()
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'داده نامعتبر'}, status=400)
        else:
            phone = request.POST.get('phone', '').strip()

        if not phone:
            return JsonResponse({
                'success': False,
                'message': 'شماره موبایل را وارد کنید',
                'field': 'phone'
            }, status=400)

        # Normalize phone
        phone = normalize_phone(phone)
        if not phone:
            return JsonResponse({
                'success': False,
                'message': 'شماره موبایل نامعتبر است',
                'field': 'phone'
            }, status=400)

        # Send OTP
        result = AuthService.start_login(phone)

        if result['success']:
            request.session['auth_phone'] = phone
            request.session['otp_id'] = result.get('otp_id')

            return JsonResponse({
                'success': True,
                'message': result['message'],
                'expires_in': result.get('expires_in', 120),
                'redirect_url': reverse('accounts:verify'),
            })

        return JsonResponse({
            'success': False,
            'message': result['message'],
            'wait_seconds': result.get('wait_seconds', 0)
        }, status=429 if result.get('wait_seconds') else 400)



class GoogleLoginView(View):
    """شروع فرآیند ورود با گوگل"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL or '/')
        
        # TODO: Redirect to Google OAuth URL
        # از کتابخانه‌هایی مثل social-auth-app-django استفاده کنید
        # یا OAuth flow را دستی پیاده‌سازی کنید
        
        google_client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', None)
        if not google_client_id:
            return JsonResponse({
                'success': False,
                'message': 'ورود با گوگل فعال نیست'
            }, status=400)
        
        # Build Google OAuth URL
        redirect_uri = request.build_absolute_uri(reverse('accounts:google_callback'))
        scope = 'openid email profile'
        
        google_auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={google_client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope={scope}&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        
        return redirect(google_auth_url)

class GoogleCallbackView(View):
    """دریافت callback از گوگل و ایجاد/ورود کاربر"""
    
    def get(self, request):
        code = request.GET.get('code')
        error = request.GET.get('error')
        
        if error:
            logger.warning(f"Google OAuth error: {error}")
            return redirect(f"{reverse('accounts:login')}?error=google_denied")
        
        if not code:
            return redirect(f"{reverse('accounts:login')}?error=google_failed")
        
        try:
            # Exchange code for tokens
            google_data = self._exchange_code_for_user_info(request, code)
            
            if not google_data:
                return redirect(f"{reverse('accounts:login')}?error=google_failed")
            
            # Find or create user
            user, created = self._get_or_create_google_user(google_data)
            
            # Login user
            login(request, user)
            
            logger.info(f"Google login successful for: {user.email}")
            
            # Redirect
            next_url = request.session.pop('next', None) or settings.LOGIN_REDIRECT_URL or '/'
            return redirect(next_url)
            
        except Exception as e:
            logger.error(f"Google OAuth callback error: {e}")
            return redirect(f"{reverse('accounts:login')}?error=google_failed")
    
    def _exchange_code_for_user_info(self, request, code):
        """Exchange authorization code for user info"""
        import requests
        
        client_id = settings.GOOGLE_OAUTH_CLIENT_ID
        client_secret = settings.GOOGLE_OAUTH_CLIENT_SECRET
        redirect_uri = request.build_absolute_uri(reverse('accounts:google_callback'))
        
        # Get tokens
        token_response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            },
            timeout=10
        )
        
        if not token_response.ok:
            logger.error(f"Google token exchange failed: {token_response.text}")
            return None
        
        tokens = token_response.json()
        access_token = tokens.get('access_token')
        
        # Get user info
        userinfo_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        
        if not userinfo_response.ok:
            logger.error(f"Google userinfo failed: {userinfo_response.text}")
            return None
        
        return userinfo_response.json()
    
    def _get_or_create_google_user(self, google_data):
        """Find existing user or create new one from Google data"""
        google_id = google_data.get('id')
        email = google_data.get('email')
        
        # Try to find by google_id first
        user = User.objects.filter(google_id=google_id).first()
        if user:
            # Update info if needed
            self._update_google_user_info(user, google_data)
            return user, False
        
        # Try to find by email
        if email:
            user = User.objects.filter(email=email).first()
            if user:
                # Link Google account to existing user
                user.google_id = google_id
                user.avatar_url = google_data.get('picture', '')
                if not user.is_email_verified:
                    user.is_email_verified = google_data.get('verified_email', False)
                user.save()
                return user, False
        
        # Create new user
        user = User.objects.create_google_user(
            email=email,
            google_id=google_id,
            first_name=google_data.get('given_name', ''),
            last_name=google_data.get('family_name', ''),
            avatar_url=google_data.get('picture', ''),
            is_email_verified=google_data.get('verified_email', False),
        )
        
        return user, True
    
    def _update_google_user_info(self, user, google_data):
        """به‌روزرسانی اطلاعات کاربر گوگل در ورودهای بعدی"""
        updated = False

        if user.avatar_url != google_data.get('picture', ''):
            user.avatar_url = google_data.get('picture', '')
            updated = True

        if not user.is_email_verified and google_data.get('verified_email', False):
            user.is_email_verified = True
            updated = True

        if updated:
            user.save()
            logger.info(f"Updated Google user info for: {user.email or user.id}")
        return user

# ============================================================================
# VERIFY VIEW
# ============================================================================

class VerifyView(View):
    template_name = 'accounts/verify.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL or '/')

        phone = request.session.get('auth_phone')
        if not phone:
            return redirect('accounts:login')

        context = {
            'page_title': 'تایید کد',
            'phone': mask_phone(phone),
            'phone_full': phone,
            'remaining_time': OTPService.get_remaining_time(phone),
            'otp_length': OTPService.OTP_LENGTH
        }
        return render(request, self.template_name, context)

    def post(self, request):
        phone = request.session.get('auth_phone')
        if not phone:
            return JsonResponse({
                'success': False,
                'message': 'نشست منقضی شده، دوباره تلاش کنید',
                'redirect_url': reverse('accounts:login')
            }, status=400)

        # Parse JSON or form data
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                code = data.get('code', '').strip()
            except:
                return JsonResponse({'success': False, 'message': 'داده نامعتبر'}, status=400)
        else:
            code = request.POST.get('code', '').strip()

        if not code:
            return JsonResponse({'success': False, 'message': 'کد را وارد کنید'}, status=400)

        if len(code) != OTPService.OTP_LENGTH:
            return JsonResponse({
                'success': False,
                'message': f'کد باید {OTPService.OTP_LENGTH} رقم باشد'
            }, status=400)

        # Verify and login
        result = AuthService.verify_and_login(request, phone, code)

        if result['success']:
            request.session.pop('auth_phone', None)
            request.session.pop('otp_id', None)

            return JsonResponse({
                'success': True,
                'message': result['message'],
                'is_new_user': result.get('is_new_user', False),
                'redirect_url': result.get('redirect_url', '/')
            })

        return JsonResponse({'success': False, 'message': result['message']}, status=400)


# ============================================================================
# RESEND OTP
# ============================================================================

class ResendOTPView(View):

    def post(self, request):
        phone = request.session.get('auth_phone')

        if not phone:
            # Try fetch from JSON body
            try:
                data = json.loads(request.body)
                phone = normalize_phone(data.get('phone', ''))
            except:
                phone = None

        if not phone:
            return JsonResponse({'success': False, 'message': 'شماره یافت نشد'}, status=400)

        result = AuthService.start_login(phone)

        if result['success']:
            request.session['auth_phone'] = phone
            request.session['otp_id'] = result.get('otp_id')

            return JsonResponse({
                'success': True,
                'message': 'کد جدید ارسال شد',
                'expires_in': result.get('expires_in', 120)
            })

        return JsonResponse({
            'success': False,
            'message': result['message'],
            'wait_seconds': result.get('wait_seconds', 0)
        }, status=429 if result.get('wait_seconds') else 400)


# ============================================================================
# LOGOUT
# ============================================================================

class LogoutView(View):

    def get(self, request):
        return self._logout(request)

    def post(self, request):
        return self._logout(request)

    def _logout(self, request):
        AuthService.logout_user(request)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'خارج شدید',
                'redirect_url': reverse('accounts:login')
            })

        return redirect('accounts:login')


# ============================================================================
# PROFILE
# ============================================================================

@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        user = request.user
        
        # Get or create profile
        from .models import Profile
        profile, _ = Profile.objects.get_or_create(user=user)
        
        # Get wallet
        try:
            from apps.wallet.models import Wallet
            wallet, _ = Wallet.objects.get_or_create(user=user)
        except:
            wallet = None
        
        # Get orders count
        try:
            from apps.orders.models import Order
            orders_count = Order.objects.filter(user=user).count()
        except:
            orders_count = 0
        
        # Get addresses
        from .models import Address
        addresses = Address.objects.filter(user=user)
        
        # Get bank cards
        from .models import BankCard
        bank_cards = BankCard.objects.filter(user=user)
        
        # Calculate security score (simplified)
        security_score = 0
        if user.is_phone_verified:
            security_score += 30
        if user.google_id:
            security_score += 20
        if profile.national_code and profile.national_code_verified:
            security_score += 30
        if bank_cards.filter(is_verified=True).exists():
            security_score += 20
        
        context = {
            'page_title': 'پروفایل',
            'user': user,
            'wallet': wallet,
            'orders_count': orders_count,
            'addresses': addresses,
            'bank_cards': bank_cards,
            'security_score': security_score,
        }
        
        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user

        # Parse JSON
        try:
            data = json.loads(request.body)
        except:
            data = request.POST

        updated = []

        if 'first_name' in data:
            user.first_name = data['first_name'].strip()[:30]
            updated.append('first_name')

        if 'last_name' in data:
            user.last_name = data['last_name'].strip()[:30]
            updated.append('last_name')

        if updated:
            user.save(update_fields=updated)
            return JsonResponse({'success': True, 'message': 'پروفایل ذخیره شد'})

        return JsonResponse({'success': False, 'message': 'تغییری صورت نگرفت'}, status=400)


# ============================================================================
# CHECK AUTH STATUS (API)
# ============================================================================

def check_auth_status(request):
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'user': {
                'phone': request.user.phone,
                'name': request.user.get_full_name() or request.user.phone,
                'avatar': request.user.avatar.url if getattr(request.user, 'avatar', None) else None
            }
        })

    return JsonResponse({'authenticated': False})


# ============================================================================
# HELPERS
# ============================================================================

def normalize_phone(phone: str) -> str:
    """Normalize Iranian mobile numbers"""
    if not phone:
        return ''

    # Convert Persian/Arabic digits to English
    persian = '۰۱۲۳۴۵۶۷۸۹'
    arabic = '٠١٢٣٤٥٦٧٨٩'
    english = '0123456789'

    trans = str.maketrans(persian + arabic, english + english)
    phone = phone.translate(trans)

    # Remove non-digits
    phone = ''.join(ch for ch in phone if ch.isdigit())

    if phone.startswith('0098'):
        phone = phone[4:]
    elif phone.startswith('098'):
        phone = phone[3:]
    elif phone.startswith('98'):
        phone = phone[2:]
    elif phone.startswith('+98'):
        phone = phone[3:]

    if phone.startswith('9') and len(phone) == 10:
        phone = '0' + phone

    if len(phone) == 11 and phone.startswith('09'):
        return phone

    return ''


def mask_phone(phone: str) -> str:
    """Mask middle digits (0912***6789)"""
    if len(phone) == 11:
        return phone[:4] + '***' + phone[-4:]
    return phone



class DashboardView(LoginRequiredMixin, TemplateView):
    """داشبورد کاربر"""
    template_name = 'accounts/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'داشبورد'
        return context


class OrdersView(LoginRequiredMixin, TemplateView):
    """
    نمایش لیست سفارشات کاربر
    """
    template_name = 'accounts/orders.html'
    login_url = '/accounts/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'سفارشات من'
        context['orders'] = []  # بعداً: Order.objects.filter(user=self.request.user)
        return context


@login_required
def transactions_view(request):
    """
    نمایش تراکنش‌های کاربر
    """
    context = {
        'page_title': 'تراکنش‌ها',
        'transactions': [],  # TODO: Transaction.objects.filter(user=request.user)
    }
    return render(request, 'accounts/transactions.html', context)


@login_required
def tickets_view(request):
    """
    نمایش تیکت‌های پشتیبانی کاربر
    """
    context = {
        'page_title': 'تیکت‌های پشتیبانی',
        'tickets': [],  # TODO: Ticket.objects.filter(user=request.user)
    }
    return render(request, 'accounts/tickets.html', context)

@login_required
def favorites_view(request):
    """
    نمایش لیست علاقه‌مندی‌های کاربر
    """
    context = {
        'page_title': 'علاقه‌مندی‌ها',
        'favorites': [],  # TODO: Favorite.objects.filter(user=request.user)
    }
    return render(request, 'accounts/favorites.html', context)

@login_required
def settings_view(request):
    """
    تنظیمات حساب کاربری
    """
    context = {
        'page_title': 'تنظیمات',
    }
    return render(request, 'accounts/settings.html', context)

def notifications_view(request):
    """
    لیست اعلان‌های کاربر
    """
    # TODO: بعداً از مدل Notification استفاده می‌شود
    notifications = []
    
    context = {
        'page_title': 'اعلان‌ها',
        'notifications': notifications,
    }
    return render(request, 'accounts/notifications.html', context)

class AddBankCardView(LoginRequiredMixin, View):
    """افزودن کارت بانکی جدید"""
    
    def post(self, request):
        card_number = request.POST.get('card_number', '').replace(' ', '').replace('-', '')
        
        # اعتبارسنجی شماره کارت
        if not card_number or len(card_number) != 16 or not card_number.isdigit():
            return JsonResponse({
                'success': False,
                'message': 'شماره کارت نامعتبر است'
            }, status=400)
        
        # TODO: ذخیره در دیتابیس
        # BankCard.objects.create(user=request.user, card_number=card_number)
        
        return JsonResponse({
            'success': True,
            'message': 'کارت بانکی با موفقیت اضافه شد'
        })


class DeleteBankCardView(LoginRequiredMixin, View):
    """حذف کارت بانکی"""
    
    def post(self, request, card_id):
        # TODO: حذف از دیتابیس
        # BankCard.objects.filter(id=card_id, user=request.user).delete()
        
        return JsonResponse({
            'success': True,
            'message': 'کارت بانکی حذف شد'
        })
        
# ==================== Address Views ====================

class AddAddressView(LoginRequiredMixin, View):
    """افزودن آدرس جدید"""
    
    def post(self, request):
        receiver_name = request.POST.get('receiver_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        city = request.POST.get('city', '').strip()
        address = request.POST.get('address', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        
        # اعتبارسنجی
        errors = []
        if not receiver_name:
            errors.append('نام گیرنده الزامی است')
        if not phone_number:
            errors.append('شماره تماس الزامی است')
        if not address:
            errors.append('آدرس الزامی است')
            
        if errors:
            return JsonResponse({
                'success': False,
                'message': '، '.join(errors)
            }, status=400)
        
        # TODO: ذخیره در دیتابیس
        # Address.objects.create(
        #     user=request.user,
        #     receiver_name=receiver_name,
        #     phone_number=phone_number,
        #     city=city,
        #     address=address,
        #     postal_code=postal_code
        # )
        
        return JsonResponse({
            'success': True,
            'message': 'آدرس با موفقیت اضافه شد'
        })


class DeleteAddressView(LoginRequiredMixin, View):
    """حذف آدرس"""
    
    def post(self, request, address_id):
        # TODO: حذف از دیتابیس
        # Address.objects.filter(id=address_id, user=request.user).delete()
        
        return JsonResponse({
            'success': True,
            'message': 'آدرس حذف شد'
        })


class SetDefaultAddressView(LoginRequiredMixin, View):
    """تنظیم آدرس پیش‌فرض"""
    
    def post(self, request, address_id):
        # TODO: تنظیم پیش‌فرض
        # Address.objects.filter(user=request.user).update(is_default=False)
        # Address.objects.filter(id=address_id, user=request.user).update(is_default=True)
        
        return JsonResponse({
            'success': True,
            'message': 'آدرس پیش‌فرض تنظیم شد'
        })
        
class EditAddressView(LoginRequiredMixin, View):
    """ویرایش آدرس"""
    
    def get(self, request, address_id):
        # TODO: نمایش فرم ویرایش
        # address = get_object_or_404(Address, id=address_id, user=request.user)
        return render(request, 'accounts/edit_address.html', {'address_id': address_id})
    
    def post(self, request, address_id):
        # TODO: ویرایش آدرس
        # address = get_object_or_404(Address, id=address_id, user=request.user)
        # address.receiver_name = request.POST.get('receiver_name')
        # address.save()
        return JsonResponse({'success': True, 'message': 'آدرس ویرایش شد'})