# apps/accounts/views.py

"""
Authentication Views for Mini-up
OTP-Only Authentication System
"""
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.contrib import messages
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
   
    @method_decorator(ensure_csrf_cookie)
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
@method_decorator(ensure_csrf_cookie, name='dispatch')
class VerifyView(View):
    template_name = 'accounts/verify.html'

    @method_decorator(ensure_csrf_cookie)
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
        profile_updated = []

        # Update user fields
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()[:30]
            updated.append('first_name')

        if 'last_name' in data:
            user.last_name = data['last_name'].strip()[:30]
            updated.append('last_name')

        if updated:
            user.save(update_fields=updated)

        # Update profile fields
        if 'national_code' in data:
            from .models import Profile
            profile, _ = Profile.objects.get_or_create(user=user)
            national_code = data['national_code'].strip()
            if national_code:
                # Basic validation: 10 digits
                if national_code.isdigit() and len(national_code) == 10:
                    profile.national_code = national_code
                    profile_updated.append('national_code')
                else:
                    return JsonResponse({'success': False, 'message': 'کد ملی باید ۱۰ رقم باشد'}, status=400)
            else:
                profile.national_code = None
                profile_updated.append('national_code')
            
            if profile_updated:
                profile.save(update_fields=profile_updated)

        if updated or profile_updated:
            return JsonResponse({
                'success': True, 
                'message': 'پروفایل با موفقیت ذخیره شد',
                'user': {
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            })

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
    """داشبورد کاربر - با تب‌های مختلف"""
    template_name = 'accounts/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # ═══════════════════════════════════════════════════════════════
        # USER INFO
        # ═══════════════════════════════════════════════════════════════
        profile = user.profile if hasattr(user, 'profile') else None
        context['user'] = user
        context['profile'] = profile
        
        # Get addresses
        try:
            from .models import Address
            addresses = Address.objects.filter(user=user)
            context['addresses'] = addresses
        except Exception as e:
            context['addresses'] = []
            logger.warning(f"Addresses data error: {e}")
        
        # Get bank cards
        try:
            from .models import BankCard
            bank_cards = BankCard.objects.filter(user=user)
            context['bank_cards'] = bank_cards
        except Exception as e:
            context['bank_cards'] = []
            logger.warning(f"Bank cards data error: {e}")
        
        # ═══════════════════════════════════════════════════════════════
        # WALLET DATA
        # ═══════════════════════════════════════════════════════════════
        try:
            from apps.wallet.models import Wallet, WalletTransaction
            wallet, created = Wallet.objects.get_or_create(user=user)
            recent_transactions = WalletTransaction.objects.filter(
                wallet=wallet
            ).order_by('-created_at')[:10]
            
            context['wallet'] = wallet
            context['wallet_transactions'] = recent_transactions
        except Exception as e:
            context['wallet'] = None
            context['wallet_transactions'] = []
            logger.warning(f"Wallet data error: {e}")
        
        # ═══════════════════════════════════════════════════════════════
        # ORDERS DATA
        # ═══════════════════════════════════════════════════════════════
        try:
            from apps.orders.models import Order
            orders = Order.objects.filter(user=user).order_by('-created_at')[:10]
            context['orders'] = orders
            context['orders_count'] = Order.objects.filter(user=user).count()
        except Exception as e:
            context['orders'] = []
            context['orders_count'] = 0
            logger.warning(f"Orders data error: {e}")
        
        context['title'] = 'داشبورد'
        context['page_title'] = 'داشبورد کاربری'
        
        return context
    
    def post(self, request):
        """Handle POST requests for wallet operations and profile updates"""
        user = request.user
        
        # Check if it's a file upload (multipart/form-data)
        if request.FILES:
            action = request.POST.get('action')
            
            # ═══════════════════════════════════════════════════════════
            # AVATAR UPLOAD
            # ═══════════════════════════════════════════════════════════
            if action == 'upload_avatar':
                avatar_file = request.FILES.get('avatar')
                
                if not avatar_file:
                    return JsonResponse({
                        'success': False,
                        'message': 'فایل تصویر یافت نشد'
                    }, status=400)
                
                # Validate file type
                if not avatar_file.content_type.startswith('image/'):
                    return JsonResponse({
                        'success': False,
                        'message': 'فرمت فایل نامعتبر است. لطفا یک تصویر انتخاب کنید'
                    }, status=400)
                
                # Validate file size (max 5MB)
                if avatar_file.size > 5 * 1024 * 1024:
                    return JsonResponse({
                        'success': False,
                        'message': 'حجم فایل نباید بیشتر از ۵ مگابایت باشد'
                    }, status=400)
                
                try:
                    # Save avatar
                    user.avatar = avatar_file
                    user.save(update_fields=['avatar'])
                    
                    logger.info(f"Avatar updated for user {user.phone}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'تصویر پروفایل با موفقیت بروزرسانی شد',
                        'avatar_url': user.avatar.url if user.avatar else None
                    })
                except Exception as e:
                    logger.error(f"Avatar upload error: {e}")
                    return JsonResponse({
                        'success': False,
                        'message': 'خطا در ذخیره تصویر'
                    }, status=500)
        
        # Handle JSON requests
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            # ═══════════════════════════════════════════════════════════
            # WALLET DEPOSIT
            # ═══════════════════════════════════════════════════════════
            if action == 'wallet_deposit':
                amount = int(data.get('amount', 0))
                gateway = data.get('gateway', 'zarinpal')
                
                # Validate amount
                from django.conf import settings
                min_amount = getattr(settings, 'MIN_WALLET_TOPUP', 10000)
                max_amount = getattr(settings, 'MAX_WALLET_TOPUP', 50000000)
                
                if amount < min_amount:
                    return JsonResponse({
                        'success': False,
                        'message': f'حداقل مبلغ شارژ {min_amount:,} تومان است'
                    }, status=400)
                
                if amount > max_amount:
                    return JsonResponse({
                        'success': False,
                        'message': f'حداکثر مبلغ شارژ {max_amount:,} تومان است'
                    }, status=400)
                
                # Create wallet deposit request
                from apps.wallet.models import Wallet, WalletDepositRequest
                wallet, _ = Wallet.objects.get_or_create(user=user)
                
                deposit_request = WalletDepositRequest.objects.create(
                    wallet=wallet,
                    amount=amount,
                    gateway=gateway,
                    status='pending'
                )
                
                # Generate payment URL (simplified - you should integrate with actual payment gateway)
                # For now, return a mock payment URL
                # In production, you'd call the payment gateway API here
                from django.urls import reverse
                payment_url = request.build_absolute_uri(
                    reverse('wallet:deposit_verify')
                ) + f'?token={deposit_request.id}'
                
                logger.info(f"Wallet deposit request created: {deposit_request.id} for user {user.phone}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'درخواست شارژ ایجاد شد',
                    'payment_url': payment_url,
                    'deposit_id': deposit_request.id
                })
            
            # ═══════════════════════════════════════════════════════════
            # ADD ADDRESS
            # ═══════════════════════════════════════════════════════════
            elif action == 'add_address':
                from .models import Address
                
                # Validate required fields
                required_fields = ['title', 'recipient_name', 'recipient_phone', 'province', 'city', 'postal_code', 'full_address']
                for field in required_fields:
                    if not data.get(field):
                        return JsonResponse({
                            'success': False,
                            'message': f'فیلد {field} الزامی است'
                        }, status=400)
                
                # Validate phone number
                phone = data.get('recipient_phone', '').strip()
                if not phone.startswith('09') or len(phone) != 11:
                    return JsonResponse({
                        'success': False,
                        'message': 'شماره تماس باید با ۰۹ شروع شده و ۱۱ رقم باشد'
                    }, status=400)
                
                # Validate postal code
                postal_code = data.get('postal_code', '').strip()
                if not postal_code.isdigit() or len(postal_code) != 10:
                    return JsonResponse({
                        'success': False,
                        'message': 'کد پستی باید ۱۰ رقم باشد'
                    }, status=400)
                
                try:
                    # Create address
                    address = Address.objects.create(
                        user=user,
                        title=data.get('title').strip(),
                        recipient_name=data.get('recipient_name').strip(),
                        recipient_phone=phone,
                        province=data.get('province').strip(),
                        city=data.get('city').strip(),
                        postal_code=postal_code,
                        full_address=data.get('full_address').strip(),
                        is_default=data.get('is_default', False)
                    )
                    
                    logger.info(f"Address created: {address.id} for user {user.phone}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'آدرس با موفقیت ذخیره شد',
                        'address_id': address.id
                    })
                except Exception as e:
                    logger.error(f"Address creation error: {e}")
                    return JsonResponse({
                        'success': False,
                        'message': 'خطا در ذخیره آدرس'
                    }, status=500)
            
            # ═══════════════════════════════════════════════════════════
            # ADD BANK CARD
            # ═══════════════════════════════════════════════════════════
            elif action == 'add_bank_card':
                from .models import BankCard
                from .bank_utils import detect_bank_from_card_number
                
                # Validate card number
                card_number = data.get('card_number', '').strip()
                if not card_number.isdigit() or len(card_number) != 16:
                    return JsonResponse({
                        'success': False,
                        'message': 'شماره کارت باید ۱۶ رقم باشد'
                    }, status=400)
                
                # Auto-detect bank from card number
                bank_info = detect_bank_from_card_number(card_number)
                bank_name = bank_info['name'] if bank_info else data.get('bank_name', '').strip()
                
                if not bank_name:
                    return JsonResponse({
                        'success': False,
                        'message': 'بانک قابل تشخیص نیست. لطفا دوباره تلاش کنید'
                    }, status=400)
                
                # Check if card already exists
                if BankCard.objects.filter(user=user, card_number=card_number).exists():
                    return JsonResponse({
                        'success': False,
                        'message': 'این کارت قبلا ثبت شده است'
                    }, status=400)
                
                try:
                    # Create bank card (bank_name will be auto-detected in model's save method)
                    bank_card = BankCard.objects.create(
                        user=user,
                        card_number=card_number,
                        bank_name=bank_name,
                        is_default=data.get('is_default', False)
                    )
                    
                    logger.info(f"Bank card created: {bank_card.id} ({bank_card.bank_full_name}) for user {user.phone}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'کارت بانکی با موفقیت ذخیره شد',
                        'card_id': bank_card.id
                    })
                except Exception as e:
                    logger.error(f"Bank card creation error: {e}")
                    return JsonResponse({
                        'success': False,
                        'message': 'خطا در ذخیره کارت'
                    }, status=500)
            
            return JsonResponse({
                'success': False,
                'message': 'عملیات نامعتبر'
            }, status=400)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'داده‌های ارسالی نامعتبر است'
            }, status=400)
        except Exception as e:
            logger.error(f"Dashboard POST error: {e}")
            return JsonResponse({
                'success': False,
                'message': 'خطایی رخ داد. لطفا دوباره تلاش کنید'
            }, status=500)


class OrdersView(LoginRequiredMixin, TemplateView):
    """
    نمایش لیست سفارشات کاربر
    """
    template_name = 'orders/order_list.html'
    login_url = '/accounts/login/'
    
    def get_context_data(self, **kwargs):
        from apps.orders.models import Order
        from django.db.models import Count, Q
        
        context = super().get_context_data(**kwargs)
        
        # Get user's orders
        orders = Order.objects.filter(user=self.request.user).order_by('-created_at')
        
        # Calculate stats
        context['orders'] = orders
        context['orders_count'] = orders.count()
        context['completed_count'] = orders.filter(status='completed').count()
        context['processing_count'] = orders.filter(status='processing').count()
        context['page_title'] = 'سفارشات من'
        
        return context


@login_required
def transactions_view(request):
    """
    نمایش تراکنش‌های کیف پول کاربر
    Display user's wallet transactions with filtering and pagination
    """
    from apps.wallet.models import WalletTransaction, Wallet
    from django.core.paginator import Paginator
    from django.db.models import Sum, Q
    from decimal import Decimal
    
    # Get or create user's wallet
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Get all transactions for user's wallet
    transactions = WalletTransaction.objects.filter(
        wallet=wallet
    ).select_related(
        'wallet',
        'order',
        'payment_transaction',
        'performed_by'
    ).order_by('-created_at')
    
    # Filter by transaction type
    transaction_type = request.GET.get('type', '')
    if transaction_type and transaction_type in dict(WalletTransaction.TransactionType.choices):
        transactions = transactions.filter(transaction_type=transaction_type)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status and status in dict(WalletTransaction.TransactionStatus.choices):
        transactions = transactions.filter(status=status)
    
    # Date range filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        from datetime import datetime
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            transactions = transactions.filter(created_at__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        from datetime import datetime
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            transactions = transactions.filter(created_at__lte=date_to_obj)
        except ValueError:
            pass
    
    # Search by description or transaction_id
    search_query = request.GET.get('q', '').strip()
    if search_query:
        transactions = transactions.filter(
            Q(description__icontains=search_query) |
            Q(transaction_id__icontains=search_query)
        )
    
    # Calculate statistics
    total_count = transactions.count()
    
    # Calculate totals by status
    completed_transactions = transactions.filter(status=WalletTransaction.TransactionStatus.COMPLETED)
    total_deposits = completed_transactions.filter(
        transaction_type__in=[
            WalletTransaction.TransactionType.DEPOSIT,
            WalletTransaction.TransactionType.REFUND,
            WalletTransaction.TransactionType.GIFT,
            WalletTransaction.TransactionType.CASHBACK,
            WalletTransaction.TransactionType.TRANSFER_IN
        ]
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    total_withdrawals = completed_transactions.filter(
        transaction_type__in=[
            WalletTransaction.TransactionType.WITHDRAW,
            WalletTransaction.TransactionType.PURCHASE,
            WalletTransaction.TransactionType.TRANSFER_OUT
        ]
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Make withdrawals positive for display
    total_withdrawals = abs(total_withdrawals)
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(transactions, 20)  # 20 transactions per page
    page_obj = paginator.get_page(page_number)
    
    # Transaction type choices for filter
    transaction_types = WalletTransaction.TransactionType.choices
    status_choices = WalletTransaction.TransactionStatus.choices
    
    context = {
        'page_title': 'تراکنش‌ها',
        'transactions': page_obj,
        'page_obj': page_obj,
        'wallet': wallet,
        'total_count': total_count,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'transaction_types': transaction_types,
        'status_choices': status_choices,
        'selected_type': transaction_type,
        'selected_status': status,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
    }
    return render(request, 'accounts/transactions.html', context)


@login_required
def tickets_view(request):
    """
    نمایش تیکت‌های پشتیبانی کاربر
    """
    from apps.consulting.models import SupportTicket
    from django.core.paginator import Paginator
    from django.db.models import Q
    from datetime import datetime
    
    tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')
    
    # فیلتر بر اساس وضعیت
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['pending', 'in_progress', 'answered', 'closed']:
        tickets = tickets.filter(status=status_filter)
    
    # جستجو
    search_query = request.GET.get('q')
    if search_query:
        tickets = tickets.filter(
            Q(ticket_id__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(initial_message__icontains=search_query)
        )
    
    # فیلتر تاریخی
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            tickets = tickets.filter(created_at__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the entire end date
            from datetime import timedelta
            date_to_obj = date_to_obj + timedelta(days=1)
            tickets = tickets.filter(created_at__lt=date_to_obj)
        except ValueError:
            pass
    
    # صفحه‌بندی
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'تیکت‌های پشتیبانی',
        'tickets': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'accounts/tickets.html', context)


@login_required
def ticket_create_view(request):
    """
    ایجاد تیکت جدید
    """
    from apps.consulting.models import SupportTicket, TicketMessage, TicketAttachment
    
    if request.method == 'POST':
        subject = request.POST.get('subject')
        initial_message = request.POST.get('message')
        attachment = request.FILES.get('attachment')
        
        # اعتبارسنجی
        if not all([subject, initial_message]):
            messages.error(request, 'لطفا تمام فیلدهای ضروری را پر کنید.')
            return render(request, 'accounts/ticket_create.html', {})
        
        # بررسی حجم فایل (حداکثر 5 مگابایت)
        if attachment:
            max_size = 5 * 1024 * 1024  # 5 MB in bytes
            if attachment.size > max_size:
                messages.error(request, 'حجم فایل نباید بیشتر از 5 مگابایت باشد.')
                return render(request, 'accounts/ticket_create.html', {})
        
        # ایجاد تیکت بدون دسته‌بندی و اولویت
        ticket = SupportTicket.objects.create(
            user=request.user,
            category=None,
            subject=subject,
            initial_message=initial_message,
            priority=None
        )
        
        # Handle attachment if provided
        if attachment:
            try:
                # Create a message for the attachment
                first_message = TicketMessage.objects.create(
                    ticket=ticket,
                    sender=request.user,
                    message="[تصویر ضمیمه]",
                    is_staff_reply=False
                )
                TicketAttachment.objects.create(
                    message=first_message,
                    file=attachment
                )
            except Exception as e:
                messages.warning(request, f'تیکت ثبت شد اما تصویر ضمیمه آپلود نشد: {str(e)}')
        
        messages.success(request, f'تیکت شما با شماره {ticket.ticket_id} ثبت شد.')
        return redirect('accounts:ticket_detail', ticket_id=ticket.ticket_id)
    
    return render(request, 'accounts/ticket_create.html', {})


@login_required
def ticket_detail_view(request, ticket_id):
    """
    جزئیات تیکت و چت
    """
    from apps.consulting.models import SupportTicket
    
    ticket = get_object_or_404(
        SupportTicket,
        ticket_id=ticket_id,
        user=request.user
    )
    
    # دریافت پیام‌ها
    messages_qs = ticket.messages.select_related('sender').prefetch_related('attachments').order_by('created_at')
    
    # علامت‌گذاری پیام‌های پشتیبان به عنوان خوانده شده
    unread_staff_messages = messages_qs.filter(is_staff_reply=True, is_read=False)
    for msg in unread_staff_messages:
        msg.mark_as_read()
    
    context = {
        'ticket': ticket,
        'ticket_messages': messages_qs,
    }
    return render(request, 'accounts/ticket_detail.html', context)


@login_required
def ticket_message_create_view(request, ticket_id):
    """
    ارسال پیام در تیکت
    """
    from apps.consulting.models import SupportTicket, TicketMessage, TicketAttachment
    from django.views.decorators.http import require_POST
    
    ticket = get_object_or_404(
        SupportTicket,
        ticket_id=ticket_id,
        user=request.user
    )
    
    if request.method != 'POST':
        return redirect('accounts:ticket_detail', ticket_id=ticket.ticket_id)
    
    # بررسی وضعیت تیکت
    if ticket.is_closed:
        messages.error(request, 'این تیکت بسته شده است. برای ارسال پیام ابتدا تیکت را بازگشایی کنید.')
        return redirect('accounts:ticket_detail', ticket_id=ticket.ticket_id)
    
    message_text = request.POST.get('message')
    if not message_text or not message_text.strip():
        messages.error(request, 'متن پیام نمی‌تواند خالی باشد.')
        return redirect('accounts:ticket_detail', ticket_id=ticket.ticket_id)
    
    # ایجاد پیام
    message = TicketMessage.objects.create(
        ticket=ticket,
        sender=request.user,
        message=message_text.strip(),
        is_staff_reply=False
    )
    
    # آپلود فایل (در صورت وجود)
    uploaded_file = request.FILES.get('attachment')
    if uploaded_file:
        # بررسی حجم فایل (حداکثر 5 مگابایت)
        max_size = 5 * 1024 * 1024  # 5 MB in bytes
        if uploaded_file.size > max_size:
            messages.error(request, 'حجم فایل نباید بیشتر از 5 مگابایت باشد.')
            return redirect('accounts:ticket_detail', ticket_id=ticket.ticket_id)
        
        try:
            TicketAttachment.objects.create(
                message=message,
                file=uploaded_file
            )
        except Exception as e:
            messages.warning(request, f'پیام ارسال شد اما فایل ضمیمه آپلود نشد: {str(e)}')
    
    messages.success(request, 'پیام شما ارسال شد.')
    return redirect('accounts:ticket_detail', ticket_id=ticket.ticket_id)


@login_required
def ticket_close_view(request, ticket_id):
    """
    بستن تیکت
    """
    from apps.consulting.models import SupportTicket
    
    if request.method != 'POST':
        return redirect('accounts:ticket_detail', ticket_id=ticket_id)
    
    ticket = get_object_or_404(
        SupportTicket,
        ticket_id=ticket_id,
        user=request.user
    )
    
    if ticket.is_closed:
        messages.info(request, 'این تیکت قبلا بسته شده است.')
    else:
        ticket.close()
        messages.success(request, 'تیکت با موفقیت بسته شد.')
    
    return redirect('accounts:ticket_detail', ticket_id=ticket.ticket_id)


@login_required
def ticket_reopen_view(request, ticket_id):
    """
    بازگشایی تیکت بسته شده
    """
    from apps.consulting.models import SupportTicket
    
    if request.method != 'POST':
        return redirect('accounts:ticket_detail', ticket_id=ticket_id)
    
    ticket = get_object_or_404(
        SupportTicket,
        ticket_id=ticket_id,
        user=request.user
    )
    
    if not ticket.is_closed:
        messages.info(request, 'این تیکت باز است.')
    else:
        ticket.reopen()
        messages.success(request, 'تیکت بازگشایی شد.')
    
    return redirect('accounts:ticket_detail', ticket_id=ticket.ticket_id)


@login_required
def favorites_view(request):
    """
    نمایش لیست علاقه‌مندی‌های کاربر
    Display user's wishlist with product details
    """
    from apps.products.models import Wishlist, WishlistItem
    
    # Get wishlist items - using both models for compatibility
    # Check if user has wishlist items (detailed model with variants)
    wishlist_items = WishlistItem.objects.filter(
        wishlist__user=request.user
    ).select_related(
        'product',
        'product__category',
        'product__brand',
        'variant'
    ).prefetch_related(
        'product__images'
    ).order_by('-created_at')
    
    # If no wishlist items, fall back to simple Wishlist model
    if not wishlist_items.exists():
        simple_wishlists = Wishlist.objects.filter(
            user=request.user
        ).select_related(
            'product',
            'product__category',
            'product__brand'
        ).prefetch_related(
            'product__images'
        ).order_by('-created_at')
        
        # Convert to compatible format for template
        favorites = simple_wishlists
    else:
        favorites = wishlist_items
    
    # Calculate statistics
    total_items = favorites.count()
    
    # Calculate total value (sum of all wishlist product prices)
    total_value = 0
    out_of_stock_count = 0
    
    for item in favorites:
        product = item.product
        if hasattr(item, 'variant') and item.variant:
            # If item has a variant, use variant price
            total_value += item.variant.price
            if item.variant.stock <= 0:
                out_of_stock_count += 1
        else:
            # Use product price
            total_value += product.price
            if not product.is_in_stock:
                out_of_stock_count += 1
    
    context = {
        'page_title': 'علاقه‌مندی‌ها',
        'favorites': favorites,
        'total_items': total_items,
        'total_value': total_value,
        'out_of_stock_count': out_of_stock_count,
        'in_stock_count': total_items - out_of_stock_count,
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

@login_required
def notifications_view(request):
    """
    لیست اعلان‌های کاربر
    """
    from apps.content.services import NotificationService
    from django.core.paginator import Paginator
    
    # دریافت اعلان‌ها
    notifications = NotificationService.list_all(request.user)
    
    # فیلتر بر اساس نوع
    filter_type = request.GET.get('type')
    if filter_type in ['info', 'success', 'warning', 'error']:
        notifications = notifications.filter(type=filter_type)
    
    # فیلتر خوانده نشده
    if request.GET.get('unread') == '1':
        notifications = notifications.filter(is_read=False)
    
    # صفحه‌بندی
    paginator = Paginator(notifications, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # تعداد خوانده نشده
    unread_count = NotificationService.get_unread_count(request.user)
    
    context = {
        'page_title': 'اعلان‌ها',
        'notifications': page_obj,
        'unread_count': unread_count,
        'filter_type': filter_type,
    }
    return render(request, 'accounts/notifications.html', context)

class AddBankCardView(LoginRequiredMixin, View):
    """افزودن کارت بانکی جدید"""
    
    def post(self, request):
        from .models import BankCard
        from django.db import IntegrityError
        
        card_number = request.POST.get('card_number', '').replace(' ', '').replace('-', '')
        bank_name = request.POST.get('bank_name', '').strip()
        is_default = request.POST.get('is_default') == 'true'
        
        # اعتبارسنجی شماره کارت
        if not card_number or len(card_number) != 16 or not card_number.isdigit():
            return JsonResponse({
                'success': False,
                'message': 'شماره کارت نامعتبر است'
            }, status=400)
        
        # تشخیص نام بانک از شماره کارت (6 رقم اول)
        if not bank_name:
            bank_name = self._detect_bank_name(card_number[:6])
        
        try:
            # بررسی تکراری نبودن
            if BankCard.objects.filter(user=request.user, card_number=card_number).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'این کارت قبلاً ثبت شده است'
                }, status=400)
            
            # محدودیت تعداد کارت (حداکثر 5 کارت)
            if BankCard.objects.filter(user=request.user).count() >= 5:
                return JsonResponse({
                    'success': False,
                    'message': 'حداکثر 5 کارت بانکی می‌توانید ثبت کنید'
                }, status=400)
            
            # ذخیره در دیتابیس
            card = BankCard.objects.create(
                user=request.user,
                card_number=card_number,
                bank_name=bank_name,
                is_default=is_default
            )
            
            return JsonResponse({
                'success': True,
                'message': 'کارت بانکی با موفقیت اضافه شد',
                'card': {
                    'id': card.id,
                    'masked_number': card.masked_number,
                    'bank_name': card.bank_name,
                    'is_default': card.is_default
                }
            })
            
        except IntegrityError:
            return JsonResponse({
                'success': False,
                'message': 'خطا در ثبت کارت بانکی'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطای غیرمنتظره: {str(e)}'
            }, status=500)
    
    def _detect_bank_name(self, bin_code):
        """تشخیص نام بانک از BIN کارت (6 رقم اول)"""
        bank_bins = {
            '603799': 'بانک ملی',
            '589210': 'بانک سپه',
            '627648': 'بانک توسعه صادرات',
            '627961': 'بانک صنعت و معدن',
            '606373': 'بانک مهر ایران',
            '639607': 'بانک صنعت و معدن',
            '627353': 'بانک تجارت',
            '585983': 'بانک تجارت',
            '622106': 'بانک پارسیان',
            '639347': 'بانک پاسارگاد',
            '636214': 'بانک آینده',
            '505785': 'بانک توسعه تعاون',
            '627412': 'بانک اقتصاد نوین',
            '639370': 'بانک مهر اقتصاد',
            '639599': 'بانک قوامین',
            '504862': 'بانک شهر',
            '639347': 'بانک پاسارگاد',
            '636949': 'بانک حکمت ایرانیان',
            '627381': 'بانک انصار',
            '505801': 'بانک کوثر',
        }
        return bank_bins.get(bin_code, 'سایر بانک‌ها')


class DeleteBankCardView(LoginRequiredMixin, View):
    """حذف کارت بانکی"""
    
    def post(self, request, card_id):
        from .models import BankCard
        from django.shortcuts import get_object_or_404
        
        try:
            # پیدا کردن کارت متعلق به کاربر
            card = get_object_or_404(BankCard, id=card_id, user=request.user)
            
            # اگر کارت پیش‌فرض است، کارت بعدی را پیش‌فرض می‌کنیم
            if card.is_default:
                next_card = BankCard.objects.filter(
                    user=request.user
                ).exclude(id=card_id).first()
                
                if next_card:
                    next_card.is_default = True
                    next_card.save(update_fields=['is_default'])
            
            # حذف کارت
            card.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'کارت بانکی با موفقیت حذف شد'
            })
            
        except BankCard.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'کارت بانکی یافت نشد'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در حذف کارت: {str(e)}'
            }, status=500)


class SetDefaultBankCardView(LoginRequiredMixin, View):
    """تنظیم کارت بانکی پیش‌فرض"""
    
    def post(self, request, card_id):
        from .models import BankCard
        from django.shortcuts import get_object_or_404
        
        try:
            # پیدا کردن کارت متعلق به کاربر
            card = get_object_or_404(BankCard, id=card_id, user=request.user)
            
            # غیرفعال کردن سایر کارت‌های پیش‌فرض
            BankCard.objects.filter(user=request.user, is_default=True).update(is_default=False)
            
            # تنظیم این کارت به عنوان پیش‌فرض
            card.is_default = True
            card.save(update_fields=['is_default'])
            
            return JsonResponse({
                'success': True,
                'message': 'کارت پیش‌فرض با موفقیت تنظیم شد'
            })
            
        except BankCard.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'کارت بانکی یافت نشد'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در تنظیم کارت: {str(e)}'
            }, status=500)


class GetBankCardsView(LoginRequiredMixin, View):
    """دریافت لیست کارت‌های بانکی کاربر"""
    
    def get(self, request):
        from .models import BankCard
        
        try:
            cards = BankCard.objects.filter(user=request.user).order_by('-is_default', '-created_at')
            
            cards_data = [{
                'id': card.id,
                'masked_number': card.masked_number,
                'bank_name': card.bank_name,
                'is_default': card.is_default,
                'is_verified': card.is_verified,
                'created_at': card.created_at.strftime('%Y/%m/%d')
            } for card in cards]
            
            return JsonResponse({
                'success': True,
                'cards': cards_data,
                'count': len(cards_data)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در دریافت کارت‌ها: {str(e)}'
            }, status=500)

        
# ==================== Address Views ====================

class AddAddressView(LoginRequiredMixin, View):
    """افزودن آدرس جدید"""
    
    def post(self, request):
        from .models import Address
        import re
        
        # دریافت داده‌ها
        title = request.POST.get('title', 'خانه').strip()
        recipient_name = request.POST.get('recipient_name', '').strip()
        recipient_phone = request.POST.get('recipient_phone', '').strip()
        province = request.POST.get('province', '').strip()
        city = request.POST.get('city', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        full_address = request.POST.get('full_address', '').strip()
        is_default = request.POST.get('is_default') == 'true'
        
        # اعتبارسنجی
        errors = []
        
        if not recipient_name:
            errors.append('نام گیرنده الزامی است')
        elif len(recipient_name) < 3:
            errors.append('نام گیرنده باید حداقل 3 کاراکتر باشد')
            
        if not recipient_phone:
            errors.append('شماره تماس الزامی است')
        elif not re.match(r'^09\d{9}$', recipient_phone):
            errors.append('شماره موبایل نامعتبر است (باید 11 رقم و با 09 شروع شود)')
            
        if not province:
            errors.append('استان الزامی است')
            
        if not city:
            errors.append('شهر الزامی است')
            
        if not full_address:
            errors.append('آدرس کامل الزامی است')
        elif len(full_address) < 10:
            errors.append('آدرس باید حداقل 10 کاراکتر باشد')
            
        if postal_code and not re.match(r'^\d{10}$', postal_code):
            errors.append('کد پستی باید 10 رقم باشد')
            
        if errors:
            return JsonResponse({
                'success': False,
                'message': ' - '.join(errors)
            }, status=400)
        
        try:
            # محدودیت تعداد آدرس (حداکثر 10 آدرس)
            if Address.objects.filter(user=request.user).count() >= 10:
                return JsonResponse({
                    'success': False,
                    'message': 'حداکثر 10 آدرس می‌توانید ثبت کنید'
                }, status=400)
            
            # ذخیره در دیتابیس
            address = Address.objects.create(
                user=request.user,
                title=title,
                recipient_name=recipient_name,
                recipient_phone=recipient_phone,
                province=province,
                city=city,
                postal_code=postal_code,
                full_address=full_address,
                is_default=is_default
            )
            
            return JsonResponse({
                'success': True,
                'message': 'آدرس با موفقیت اضافه شد',
                'address': {
                    'id': address.id,
                    'title': address.title,
                    'recipient_name': address.recipient_name,
                    'city': address.city,
                    'is_default': address.is_default
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در ثبت آدرس: {str(e)}'
            }, status=500)


class DeleteAddressView(LoginRequiredMixin, View):
    """حذف آدرس"""
    
    def post(self, request, address_id):
        from .models import Address
        from django.shortcuts import get_object_or_404
        
        try:
            # پیدا کردن آدرس متعلق به کاربر
            address = get_object_or_404(Address, id=address_id, user=request.user)
            
            # اگر آدرس پیش‌فرض است، آدرس بعدی را پیش‌فرض می‌کنیم
            if address.is_default:
                next_address = Address.objects.filter(
                    user=request.user
                ).exclude(id=address_id).first()
                
                if next_address:
                    next_address.is_default = True
                    next_address.save(update_fields=['is_default'])
            
            # حذف آدرس
            address.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'آدرس با موفقیت حذف شد'
            })
            
        except Address.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'آدرس یافت نشد'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در حذف آدرس: {str(e)}'
            }, status=500)


class SetDefaultAddressView(LoginRequiredMixin, View):
    """تنظیم آدرس پیش‌فرض"""
    
    def post(self, request, address_id):
        from .models import Address
        from django.shortcuts import get_object_or_404
        
        try:
            # پیدا کردن آدرس متعلق به کاربر
            address = get_object_or_404(Address, id=address_id, user=request.user)
            
            # غیرفعال کردن سایر آدرس‌های پیش‌فرض
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            
            # تنظیم این آدرس به عنوان پیش‌فرض
            address.is_default = True
            address.save(update_fields=['is_default'])
            
            return JsonResponse({
                'success': True,
                'message': 'آدرس پیش‌فرض با موفقیت تنظیم شد'
            })
            
        except Address.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'آدرس یافت نشد'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در تنظیم آدرس: {str(e)}'
            }, status=500)
        
class EditAddressView(LoginRequiredMixin, View):
    """ویرایش آدرس"""
    
    def get(self, request, address_id):
        from .models import Address
        from django.shortcuts import get_object_or_404
        
        try:
            address = get_object_or_404(Address, id=address_id, user=request.user)
            
            return JsonResponse({
                'success': True,
                'address': {
                    'id': address.id,
                    'title': address.title,
                    'recipient_name': address.recipient_name,
                    'recipient_phone': address.recipient_phone,
                    'province': address.province,
                    'city': address.city,
                    'postal_code': address.postal_code,
                    'full_address': address.full_address,
                    'is_default': address.is_default
                }
            })
        except Address.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'آدرس یافت نشد'
            }, status=404)
    
    def post(self, request, address_id):
        from .models import Address
        from django.shortcuts import get_object_or_404
        import re
        
        try:
            address = get_object_or_404(Address, id=address_id, user=request.user)
            
            # دریافت داده‌ها
            title = request.POST.get('title', '').strip()
            recipient_name = request.POST.get('recipient_name', '').strip()
            recipient_phone = request.POST.get('recipient_phone', '').strip()
            province = request.POST.get('province', '').strip()
            city = request.POST.get('city', '').strip()
            postal_code = request.POST.get('postal_code', '').strip()
            full_address = request.POST.get('full_address', '').strip()
            is_default = request.POST.get('is_default') == 'true'
            
            # اعتبارسنجی
            errors = []
            
            if recipient_name and len(recipient_name) < 3:
                errors.append('نام گیرنده باید حداقل 3 کاراکتر باشد')
                
            if recipient_phone and not re.match(r'^09\d{9}$', recipient_phone):
                errors.append('شماره موبایل نامعتبر است')
                
            if full_address and len(full_address) < 10:
                errors.append('آدرس باید حداقل 10 کاراکتر باشد')
                
            if postal_code and not re.match(r'^\d{10}$', postal_code):
                errors.append('کد پستی باید 10 رقم باشد')
                
            if errors:
                return JsonResponse({
                    'success': False,
                    'message': ' - '.join(errors)
                }, status=400)
            
            # بروزرسانی فیلدها
            if title:
                address.title = title
            if recipient_name:
                address.recipient_name = recipient_name
            if recipient_phone:
                address.recipient_phone = recipient_phone
            if province:
                address.province = province
            if city:
                address.city = city
            if postal_code:
                address.postal_code = postal_code
            if full_address:
                address.full_address = full_address
            
            # مدیریت پیش‌فرض
            if is_default and not address.is_default:
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
                address.is_default = True
            
            address.save()
            
            return JsonResponse({
                'success': True,
                'message': 'آدرس با موفقیت ویرایش شد',
                'address': {
                    'id': address.id,
                    'title': address.title,
                    'recipient_name': address.recipient_name,
                    'city': address.city,
                    'is_default': address.is_default
                }
            })
            
        except Address.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'آدرس یافت نشد'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در ویرایش آدرس: {str(e)}'
            }, status=500)


class GetAddressesView(LoginRequiredMixin, View):
    """دریافت لیست آدرس‌های کاربر"""
    
    def get(self, request):
        from .models import Address
        
        try:
            addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
            
            addresses_data = [{
                'id': addr.id,
                'title': addr.title,
                'recipient_name': addr.recipient_name,
                'recipient_phone': addr.recipient_phone,
                'province': addr.province,
                'city': addr.city,
                'postal_code': addr.postal_code,
                'full_address': addr.full_address,
                'is_default': addr.is_default,
                'created_at': addr.created_at.strftime('%Y/%m/%d')
            } for addr in addresses]
            
            return JsonResponse({
                'success': True,
                'addresses': addresses_data,
                'count': len(addresses_data)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در دریافت آدرس‌ها: {str(e)}'
            }, status=500)