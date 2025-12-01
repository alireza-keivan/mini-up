# apps/wallet/api_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db.models import Q, Sum, Count
from .models import Wallet, WalletTransaction, WalletDepositRequest
from .services import WalletService
from .serializers import (
    WalletSerializer,
    WalletBalanceSerializer,
    WalletTransactionSerializer,
    WalletDepositRequestSerializer,
    DepositRequestCreateSerializer,
    TransferSerializer,
)


# ═══════════════════════════════════════════════════════════════════════════════
# WALLET INFO APIs
# ═══════════════════════════════════════════════════════════════════════════════

class WalletDetailAPIView(APIView):
    """
    دریافت اطلاعات کامل کیف پول
    GET /wallet/api/v1/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = WalletService.get_or_create_wallet(request.user)
        serializer = WalletSerializer(wallet)
        return Response({
            'success': True,
            'data': serializer.data
        })


class WalletBalanceAPIView(APIView):
    """
    دریافت موجودی کیف پول (سبک‌تر)
    GET /wallet/api/v1/balance/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = WalletService.get_or_create_wallet(request.user)
        serializer = WalletBalanceSerializer(wallet)
        return Response({
            'success': True,
            'data': serializer.data
        })


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSACTIONS API
# ═══════════════════════════════════════════════════════════════════════════════

class WalletTransactionsAPIView(APIView):
    """
    لیست تراکنش‌های کیف پول
    GET /wallet/api/v1/transactions/
    
    Query Params:
        - type: فیلتر بر اساس نوع (deposit, withdraw, purchase, ...)
        - limit: تعداد (پیش‌فرض 20، حداکثر 100)
        - offset: شروع از
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = WalletService.get_or_create_wallet(request.user)
        
        # فیلترها
        tx_type = request.query_params.get('type', None)
        limit = min(int(request.query_params.get('limit', 20)), 100)
        offset = int(request.query_params.get('offset', 0))
        
        # کوئری
        transactions = WalletTransaction.objects.filter(wallet=wallet)
        
        if tx_type:
            transactions = transactions.filter(transaction_type=tx_type)
        
        transactions = transactions.order_by('-created_at')[offset:offset + limit]
        
        serializer = WalletTransactionSerializer(transactions, many=True)
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'data': serializer.data
        })


class WalletTransactionDetailAPIView(APIView):
    """
    جزئیات یک تراکنش خاص
    GET /wallet/api/v1/transactions/<uuid:pk>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        wallet = WalletService.get_or_create_wallet(request.user)
        
        transaction = get_object_or_404(
            WalletTransaction,
            pk=pk,
            wallet=wallet
        )
        
        serializer = WalletTransactionSerializer(transaction)
        return Response({
            'success': True,
            'data': serializer.data
        })


# ═══════════════════════════════════════════════════════════════════════════════
# DEPOSIT APIs (شارژ کیف پول)
# ═══════════════════════════════════════════════════════════════════════════════

class WalletDepositCreateAPIView(APIView):
    """
    ایجاد درخواست شارژ کیف پول
    POST /wallet/api/v1/deposit/create/
    
    Body:
        - amount: مبلغ (تومان)
        - gateway: درگاه پرداخت (پیش‌فرض: zarinpal)
    
    Returns:
        - deposit_request: اطلاعات درخواست
        - payment_url: لینک پرداخت
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DepositRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        amount = serializer.validated_data['amount']
        gateway = serializer.validated_data.get('gateway', 'zarinpal')
        
        try:
            # ایجاد درخواست شارژ
            wallet = WalletService.get_or_create_wallet(request.user)
            
            # بررسی محدودیت‌ها
            if amount < WalletService.MIN_DEPOSIT:
                return Response({
                    'success': False,
                    'error': f'حداقل مبلغ شارژ {WalletService.MIN_DEPOSIT:,} تومان است'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if amount > WalletService.MAX_DEPOSIT:
                return Response({
                    'success': False,
                    'error': f'حداکثر مبلغ شارژ {WalletService.MAX_DEPOSIT:,} تومان است'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ساخت درخواست
            from django.utils import timezone
            from datetime import timedelta
            
            deposit_request = WalletDepositRequest.objects.create(
                wallet=wallet,
                amount=amount,
                status='pending',
                expires_at=timezone.now() + timedelta(minutes=15)
            )
            
            # اتصال به درگاه پرداخت
            if gateway == 'zarinpal':
                payment_result = self._create_zarinpal_payment(request, deposit_request)
            else:
                payment_result = self._create_zarinpal_payment(request, deposit_request)
            
            if not payment_result['success']:
                deposit_request.status = 'failed'
                deposit_request.save()
                return Response({
                    'success': False,
                    'error': payment_result.get('error', 'خطا در اتصال به درگاه')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ذخیره authority
            deposit_request.authority = payment_result.get('authority')
            deposit_request.save()
            
            return Response({
                'success': True,
                'data': {
                    'deposit_id': str(deposit_request.id),
                    'amount': int(deposit_request.amount),
                    'payment_url': payment_result['payment_url'],
                    'authority': payment_result.get('authority'),
                }
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'خطای سرور: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_zarinpal_payment(self, request, deposit_request):
        """اتصال به زرین‌پال"""
        try:
            from apps.payments.services import ZarinPalService
            from django.urls import reverse
            
            callback_url = request.build_absolute_uri(
                reverse('wallet:deposit_verify')
            )
            
            zarinpal = ZarinPalService(sandbox=True)
            result = zarinpal.request_payment(
                amount=int(deposit_request.amount),
                description=f'شارژ کیف پول - {deposit_request.amount:,} تومان',
                callback_url=callback_url,
                mobile=getattr(request.user, 'phone', None),
                email=getattr(request.user, 'email', None),
            )
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


class WalletDepositVerifyAPIView(APIView):
    """
    تأیید پرداخت شارژ کیف پول (برای AJAX)
    POST /wallet/api/v1/deposit/verify/
    
    Body:
        - authority: کد authority از درگاه
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        authority = request.data.get('authority')
        
        if not authority:
            return Response({
                'success': False,
                'error': 'کد تراکنش الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # پیدا کردن درخواست شارژ
            deposit_request = get_object_or_404(
                WalletDepositRequest,
                authority=authority,
                wallet__user=request.user,
                status='pending'
            )
            
            # تأیید از زرین‌پال
            from apps.payments.services import ZarinPalService
            
            zarinpal = ZarinPalService(sandbox=True)
            verify_result = zarinpal.verify_payment(
                authority=authority,
                amount=int(deposit_request.amount)
            )
            
            if verify_result['success']:
                # شارژ کیف پول
                wallet_tx = WalletService.deposit(
                    wallet=deposit_request.wallet,
                    amount=deposit_request.amount,
                    description=f'شارژ کیف پول - کد پیگیری: {verify_result.get("ref_id", "N/A")}'
                )
                
                # به‌روزرسانی درخواست
                deposit_request.status = 'paid'
                deposit_request.ref_id = verify_result.get('ref_id')
                deposit_request.wallet_transaction = wallet_tx
                deposit_request.save()
                
                return Response({
                    'success': True,
                    'message': f'کیف پول با موفقیت شارژ شد',
                    'data': {
                        'amount': int(deposit_request.amount),
                        'ref_id': verify_result.get('ref_id'),
                        'new_balance': int(deposit_request.wallet.total_balance),
                    }
                })
            else:
                deposit_request.status = 'failed'
                deposit_request.save()
                
                return Response({
                    'success': False,
                    'error': verify_result.get('error', 'خطا در تأیید پرداخت')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except WalletDepositRequest.DoesNotExist:
            return Response({
                'success': False,
                'error': 'درخواست شارژ یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletDepositsHistoryAPIView(APIView):
    """
    تاریخچه درخواست‌های شارژ
    GET /wallet/api/v1/deposits/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = WalletService.get_or_create_wallet(request.user)
        
        deposits = WalletDepositRequest.objects.filter(
            wallet=wallet
        ).order_by('-created_at')[:20]
        
        serializer = WalletDepositRequestSerializer(deposits, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSFER API (انتقال وجه)
# ═══════════════════════════════════════════════════════════════════════════════

class WalletTransferAPIView(APIView):
    """
    انتقال وجه به کاربر دیگر
    POST /wallet/api/v1/transfer/
    
    Body:
        - receiver_phone: شماره موبایل گیرنده
        - amount: مبلغ (تومان)
        - description: توضیحات (اختیاری)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransferSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        receiver_phone = serializer.validated_data['receiver_phone']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')
        
        try:
            # پیدا کردن کیف پول فرستنده
            sender_wallet = WalletService.get_or_create_wallet(request.user)
            
            # پیدا کردن گیرنده
            from apps.accounts.models import User
            
            try:
                receiver = User.objects.get(phone=receiver_phone)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'کاربر با این شماره موبایل یافت نشد'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if receiver == request.user:
                return Response({
                    'success': False,
                    'error': 'انتقال به خودتان امکان‌پذیر نیست'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            receiver_wallet = WalletService.get_or_create_wallet(receiver)
            
            # انجام انتقال
            result = WalletService.transfer(
                sender_wallet=sender_wallet,
                receiver_wallet=receiver_wallet,
                amount=amount,
                description=description
            )
            
            return Response({
                'success': True,
                'message': f'مبلغ {amount:,} تومان با موفقیت منتقل شد',
                'data': {
                    'amount': int(amount),
                    'receiver_phone': receiver_phone,
                    'new_balance': int(sender_wallet.total_balance),
                }
            })
            
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'خطای سرور: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════════════════════════════════
# WITHDRAW API (برداشت به حساب بانکی)
# ═══════════════════════════════════════════════════════════════════════════════

class WalletWithdrawAPIView(APIView):
    """
    درخواست برداشت به حساب بانکی
    POST /wallet/api/v1/withdraw/
    
    Body:
        - amount: مبلغ (تومان)
        - iban: شماره شبا (IR + 24 رقم)
        - card_number: شماره کارت (اختیاری)
    
    Note: برداشت نیاز به تأیید ادمین دارد
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount')
        iban = request.data.get('iban', '').strip()
        card_number = request.data.get('card_number', '').strip()
        
        # اعتبارسنجی
        if not amount:
            return Response({
                'success': False,
                'error': 'مبلغ الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = Decimal(str(amount))
        except:
            return Response({
                'success': False,
                'error': 'مبلغ نامعتبر است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if amount < 50000:
            return Response({
                'success': False,
                'error': 'حداقل مبلغ برداشت ۵۰,۰۰۰ تومان است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # اعتبارسنجی شبا
        if not iban:
            return Response({
                'success': False,
                'error': 'شماره شبا الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # حذف فاصله‌ها و نرمال‌سازی
        iban = iban.replace(' ', '').upper()
        
        if not iban.startswith('IR'):
            iban = 'IR' + iban
        
        if len(iban) != 26:
            return Response({
                'success': False,
                'error': 'شماره شبا باید ۲۴ رقم باشد (بدون IR)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            wallet = WalletService.get_or_create_wallet(request.user)
            
            # بررسی موجودی (فقط balance اصلی، نه gift)
            if wallet.balance < amount:
                return Response({
                    'success': False,
                    'error': f'موجودی قابل برداشت کافی نیست. موجودی فعلی: {wallet.balance:,} تومان'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # بررسی قفل بودن
            if wallet.is_locked:
                return Response({
                    'success': False,
                    'error': f'کیف پول قفل است: {wallet.lock_reason}'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # ثبت درخواست برداشت (در انتظار تأیید ادمین)
            # NOTE: در اینجا فقط تراکنش pending ثبت می‌شود
            # برداشت واقعی پس از تأیید ادمین انجام می‌شود
            
            withdraw_tx = WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type=WalletTransaction.TransactionType.WITHDRAW,
                status=WalletTransaction.TransactionStatus.PENDING,
                amount=-amount,  # منفی برای برداشت
                balance_before=wallet.total_balance,
                balance_after=wallet.total_balance,  # هنوز کم نشده
                description=f'درخواست برداشت به شبا: {iban}',
                metadata={
                    'iban': iban,
                    'card_number': card_number,
                    'status': 'pending_admin_approval'
                }
            )
            
            return Response({
                'success': True,
                'message': 'درخواست برداشت ثبت شد و در انتظار تأیید است',
                'data': {
                    'transaction_id': str(withdraw_tx.id),
                    'amount': int(amount),
                    'iban': iban,
                    'status': 'pending',
                    'note': 'پس از تأیید توسط تیم پشتیبانی، مبلغ طی ۲۴ ساعت کاری به حسابتان واریز می‌شود'
                }
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'خطای سرور: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ═══════════════════════════════════════════════════════════════════════════════
# GIFT CREDIT API (اعتبار هدیه)
# ═══════════════════════════════════════════════════════════════════════════════

class WalletRedeemGiftCodeAPIView(APIView):
    """
    استفاده از کد هدیه
    POST /wallet/api/v1/redeem/
    
    Body:
        - code: کد هدیه
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('code', '').strip().upper()
        
        if not code:
            return Response({
                'success': False,
                'error': 'کد هدیه الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # TODO: پیاده‌سازی سیستم کد هدیه
        # این بخش نیاز به مدل GiftCode دارد که بعداً می‌سازیم
        
        return Response({
            'success': False,
            'error': 'سیستم کد هدیه به زودی فعال می‌شود'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


# ═══════════════════════════════════════════════════════════════════════════════
# PAYMENT CHECK API (بررسی امکان پرداخت)
# ═══════════════════════════════════════════════════════════════════════════════

class WalletPaymentCheckAPIView(APIView):
    """
    بررسی امکان پرداخت با کیف پول
    POST /wallet/api/v1/payment/check/
    
    Body:
        - amount: مبلغ مورد نیاز
    
    Returns:
        - can_pay_full: آیا کامل از کیف پول قابل پرداخت است؟
        - from_wallet: مبلغ قابل پرداخت از کیف پول
        - from_gateway: مبلغ باقی‌مانده (نیاز به درگاه)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount')
        
        if not amount:
            return Response({
                'success': False,
                'error': 'مبلغ الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = Decimal(str(amount))
        except:
            return Response({
                'success': False,
                'error': 'مبلغ نامعتبر است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        wallet = WalletService.get_or_create_wallet(request.user)
        
        from_wallet = wallet.get_payable_amount(amount)
        from_gateway = wallet.get_remaining_amount(amount)
        can_pay_full = wallet.can_afford(amount)
        
        return Response({
            'success': True,
            'data': {
                'amount_requested': int(amount),
                'wallet_balance': int(wallet.total_balance),
                'can_pay_full': can_pay_full,
                'from_wallet': int(from_wallet),
                'from_gateway': int(from_gateway),
                'is_locked': wallet.is_locked,
            }
        })


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICS API (آمار کیف پول)
# ═══════════════════════════════════════════════════════════════════════════════

class WalletStatsAPIView(APIView):
    """
    آمار کیف پول کاربر
    GET /wallet/api/v1/stats/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = WalletService.get_or_create_wallet(request.user)
        
        # آمار تراکنش‌ها
        from django.db.models import Sum, Count
        from django.db.models.functions import TruncMonth
        from django.utils import timezone
        from datetime import timedelta
        
        # تراکنش‌های ۳۰ روز اخیر
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        recent_stats = WalletTransaction.objects.filter(
            wallet=wallet,
            created_at__gte=thirty_days_ago,
            status='completed'
        ).aggregate(
            total_deposits=Sum('amount', filter=Q(amount__gt=0)),
            total_withdrawals=Sum('amount', filter=Q(amount__lt=0)),
            transaction_count=Count('id')
        )
        
        return Response({
            'success': True,
            'data': {
                'current_balance': int(wallet.balance),
                'gift_balance': int(wallet.gift_balance),
                'total_balance': int(wallet.total_balance),
                'total_deposited_all_time': int(wallet.total_deposited),
                'total_spent_all_time': int(wallet.total_spent),
                'last_30_days': {
                    'deposits': int(recent_stats['total_deposits'] or 0),
                    'withdrawals': abs(int(recent_stats['total_withdrawals'] or 0)),
                    'transaction_count': recent_stats['transaction_count'],
                }
            }
        })