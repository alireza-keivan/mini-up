# apps/wallet/views.py

from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
import json

# ═══════════════════════════════════════════════════════════════════════════════
# HTML TEMPLATE VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class WalletDashboardView(LoginRequiredMixin, TemplateView):
    """
    داشبورد اصلی کیف پول
    """
    template_name = 'wallet/dashboard.html'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # دریافت یا ساخت کیف پول کاربر
        try:
            from .models import Wallet, WalletTransaction
            wallet, created = Wallet.objects.get_or_create(user=user)
            
            # آخرین تراکنش‌ها
            recent_transactions = WalletTransaction.objects.filter(
                wallet=wallet
            ).order_by('-created_at')[:10]
            
            context['wallet'] = wallet
            context['recent_transactions'] = recent_transactions
            
        except Exception as e:
            # اگر مدل‌ها هنوز migrate نشده‌اند
            context['wallet'] = {
                'balance': 0,
                'gift_balance': 0,
            }
            context['recent_transactions'] = []
            context['error'] = str(e)
        
        return context


class WalletDepositView(LoginRequiredMixin, TemplateView):
    """
    صفحه شارژ کیف پول
    """
    template_name = 'wallet/deposit.html'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        try:
            from .models import Wallet, WalletDepositRequest
            wallet, created = Wallet.objects.get_or_create(user=user)
            
            # شارژهای اخیر
            recent_deposits = WalletDepositRequest.objects.filter(
                wallet=wallet
            ).order_by('-created_at')[:5]
            
            context['wallet'] = wallet
            context['recent_deposits'] = recent_deposits
            
        except Exception as e:
            context['wallet'] = {
                'balance': 0,
                'gift_balance': 0,
            }
            context['recent_deposits'] = []
        
        # تنظیمات شارژ
        from django.conf import settings
        context['min_deposit'] = getattr(settings, 'MIN_WALLET_TOPUP', 10000)
        context['max_deposit'] = getattr(settings, 'MAX_WALLET_TOPUP', 50000000)
        
        return context


class WalletTransactionsView(LoginRequiredMixin, TemplateView):
    """
    لیست تراکنش‌های کیف پول
    """
    template_name = 'wallet/transactions.html'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        try:
            from .models import Wallet, WalletTransaction
            wallet = Wallet.objects.get(user=user)
            
            # همه تراکنش‌ها با pagination
            transactions = WalletTransaction.objects.filter(
                wallet=wallet
            ).order_by('-created_at')
            
            context['wallet'] = wallet
            context['transactions'] = transactions
            
        except Exception as e:
            context['wallet'] = {
                'balance': 0,
                'gift_balance': 0,
            }
            context['transactions'] = []
        
        return context


# ═══════════════════════════════════════════════════════════════════════════════
# DEPOSIT PROCESS VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class WalletDepositCreateView(LoginRequiredMixin, View):
    """
    ایجاد درخواست شارژ و انتقال به درگاه پرداخت
    """
    login_url = '/login/'
    
    def post(self, request):
        try:
            # دریافت مبلغ
            amount = int(request.POST.get('amount', 0))
            gateway = request.POST.get('gateway', 'zarinpal')
            
            # اعتبارسنجی مبلغ
            from django.conf import settings
            min_amount = getattr(settings, 'MIN_WALLET_TOPUP', 10000)
            max_amount = getattr(settings, 'MAX_WALLET_TOPUP', 50000000)
            
            if amount < min_amount:
                messages.error(request, f'حداقل مبلغ شارژ {min_amount:,} تومان است')
                return redirect('wallet:deposit')
            
            if amount > max_amount:
                messages.error(request, f'حداکثر مبلغ شارژ {max_amount:,} تومان است')
                return redirect('wallet:deposit')
            
            # ایجاد درخواست شارژ
            from .models import Wallet, WalletDepositRequest
            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            
            deposit_request = WalletDepositRequest.objects.create(
                wallet=wallet,
                amount=amount,
                gateway=gateway,
                status='pending'
            )
            
            # اتصال به درگاه پرداخت
            if gateway == 'zarinpal':
                return self._process_zarinpal(request, deposit_request)
            else:
                # درگاه پیش‌فرض
                return self._process_zarinpal(request, deposit_request)
                
        except ValueError:
            messages.error(request, 'مبلغ وارد شده معتبر نیست')
            return redirect('wallet:deposit')
        except Exception as e:
            messages.error(request, f'خطا در پردازش: {str(e)}')
            return redirect('wallet:deposit')
    
    def _process_zarinpal(self, request, deposit_request):
        """پردازش پرداخت زرین‌پال"""
        from apps.payments.services import ZarinPalService
        
        callback_url = request.build_absolute_uri(
            reverse('wallet:deposit_verify')
        )
        
        zarinpal = ZarinPalService(sandbox=True)
        result = zarinpal.request_payment(
            amount=deposit_request.amount,
            description=f'شارژ کیف پول - {deposit_request.amount:,} تومان',
            callback_url=callback_url,
            mobile=getattr(request.user, 'phone', None),
            email=getattr(request.user, 'email', None),
        )
        
        if result['success']:
            # ذخیره authority
            deposit_request.authority = result['authority']
            deposit_request.save()
            
            # انتقال به درگاه
            return redirect(result['payment_url'])
        else:
            messages.error(request, f'خطا در اتصال به درگاه: {result.get("error", "خطای نامشخص")}')
            deposit_request.status = 'failed'
            deposit_request.save()
            return redirect('wallet:deposit')


class WalletDepositVerifyView(LoginRequiredMixin, View):
    """
    تأیید پرداخت و شارژ کیف پول
    """
    login_url = '/login/'
    
    def get(self, request):
        authority = request.GET.get('Authority')
        status = request.GET.get('Status')
        
        if status != 'OK':
            messages.error(request, 'پرداخت توسط شما لغو شد')
            return redirect('wallet:deposit')
        
        try:
            from .models import WalletDepositRequest
            from .services import WalletService
            
            # پیدا کردن درخواست شارژ
            deposit_request = WalletDepositRequest.objects.get(
                authority=authority,
                wallet__user=request.user,
                status='pending'
            )
            
            # تأیید پرداخت از زرین‌پال
            from apps.payments.services import ZarinPalService
            zarinpal = ZarinPalService(sandbox=True)
            
            verify_result = zarinpal.verify_payment(
                authority=authority,
                amount=deposit_request.amount
            )
            
            if verify_result['success']:
                # شارژ کیف پول
                wallet_service = WalletService(deposit_request.wallet)
                wallet_service.deposit(
                    amount=deposit_request.amount,
                    description=f'شارژ کیف پول - کد پیگیری: {verify_result.get("ref_id", "N/A")}',
                    reference_id=verify_result.get('ref_id')
                )
                
                # به‌روزرسانی درخواست
                deposit_request.status = 'completed'
                deposit_request.ref_id = verify_result.get('ref_id')
                deposit_request.save()
                
                messages.success(
                    request, 
                    f'کیف پول شما با موفقیت به مبلغ {deposit_request.amount:,} تومان شارژ شد'
                )
                return redirect('wallet:dashboard')
            else:
                deposit_request.status = 'failed'
                deposit_request.save()
                messages.error(request, f'خطا در تأیید پرداخت: {verify_result.get("error")}')
                return redirect('wallet:deposit')
                
        except WalletDepositRequest.DoesNotExist:
            messages.error(request, 'درخواست شارژ یافت نشد')
            return redirect('wallet:deposit')
        except Exception as e:
            messages.error(request, f'خطا: {str(e)}')
            return redirect('wallet:deposit')


# ═══════════════════════════════════════════════════════════════════════════════
# API VIEWS (اختیاری - برای AJAX)
# ═══════════════════════════════════════════════════════════════════════════════

class WalletBalanceAPIView(LoginRequiredMixin, View):
    """
    API برای دریافت موجودی کیف پول
    """
    def get(self, request):
        try:
            from .models import Wallet
            wallet = Wallet.objects.get(user=request.user)
            return JsonResponse({
                'success': True,
                'balance': wallet.balance,
                'gift_balance': wallet.gift_balance,
                'total': wallet.total_balance,
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
