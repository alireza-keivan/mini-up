# apps/accounts/views.py

"""
Authentication Views for Mini-up
OTP-Only Authentication System
"""

import json
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.contrib.auth import logout
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings

from .services import AuthService, OTPService
from .models import User


logger = logging.getLogger(__name__)


# ============================================================================
# LOGIN VIEW
# ============================================================================

class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL or '/')

        return render(request, self.template_name, {
            'page_title': 'ورود به مینی‌آپ'
        })

    def post(self, request):
        # Parse JSON or form data
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                phone = data.get('phone', '').strip()
            except:
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
        return render(request, self.template_name, {
            'page_title': 'پروفایل',
            'user': request.user
        })

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

        if 'email' in data:
            email = data['email'].strip().lower()
            if email and '@' in email:
                if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                    return JsonResponse({
                        'success': False,
                        'message': 'این ایمیل قبلاً استفاده شده',
                        'field': 'email'
                    }, status=400)
                user.email = email
                updated.append('email')

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
