# apps/payments/api_views.py

"""
Payment API Views Module
========================
Comprehensive API endpoints for payment operations including:
- Payment initiation and verification
- Transaction management and history
- Gateway selection and status
- Wallet deposit via payment gateway
- Refund processing
"""

import logging
from decimal import Decimal
from uuid import UUID

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction as db_transaction
from django.db.models import Q
from django.core.exceptions import ValidationError as DjangoValidationError
from django.urls import reverse
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from .models import PaymentGateway, Transaction
from .services import PaymentService, ZarinPalService, IDPayService
from .serializers import (
    # Gateway serializers
    PaymentGatewaySerializer,
    PaymentGatewayListSerializer,
    # Transaction serializers
    TransactionSerializer,
    TransactionListSerializer,
    TransactionMinimalSerializer,
    # Input serializers
    PaymentInitiateSerializer,
    PaymentVerifySerializer,
    WalletDepositSerializer,
    RefundRequestSerializer,
)

logger = logging.getLogger(__name__)


# =============================================================================
# HELPER MIXIN
# =============================================================================

class ClientIPMixin:
    """Mixin to extract client IP address from request."""
    
    def get_client_ip(self, request) -> str:
        """Extract real client IP considering proxy headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        
        x_real_ip = request.META.get('HTTP_X_REAL_IP')
        if x_real_ip:
            return x_real_ip.strip()
        
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


# =============================================================================
# GATEWAY APIs
# =============================================================================

class AvailableGatewaysAPIView(APIView):
    """
    لیست درگاه‌های پرداخت فعال
    
    GET /api/v1/payments/gateways/
    
    Query Parameters:
        - amount (optional): Filter gateways supporting this amount
    
    Response:
        {
            "success": true,
            "count": 2,
            "data": [
                {
                    "id": "uuid",
                    "name": "زرین‌پال",
                    "gateway_type": "zarinpal",
                    "gateway_type_display": "زرین‌پال",
                    "logo_url": "/media/gateways/zarinpal.png",
                    "description": "درگاه پرداخت زرین‌پال",
                    "min_amount": 1000,
                    "max_amount": 500000000
                }
            ]
        }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Base queryset: active gateways ordered by priority
        gateways = PaymentGateway.objects.filter(
            is_active=True
        ).order_by('priority', 'name')
        
        # Filter by amount if provided
        amount = request.query_params.get('amount')
        if amount:
            try:
                amount_int = int(amount)
                gateways = gateways.filter(
                    Q(min_amount__lte=amount_int) | Q(min_amount__isnull=True),
                    Q(max_amount__gte=amount_int) | Q(max_amount__isnull=True)
                )
            except (ValueError, TypeError):
                pass
        
        serializer = PaymentGatewayListSerializer(
            gateways,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'count': gateways.count(),
            'data': serializer.data
        })


class GatewayDetailAPIView(APIView):
    """
    جزئیات یک درگاه پرداخت خاص
    
    GET /api/v1/payments/gateways/<gateway_type>/
    
    Path Parameters:
        - gateway_type: zarinpal | idpay
    
    Response:
        Full gateway details including configuration info
    """
    permission_classes = [AllowAny]
    
    def get(self, request, gateway_type):
        gateway = get_object_or_404(
            PaymentGateway,
            gateway_type=gateway_type,
            is_active=True
        )
        
        serializer = PaymentGatewaySerializer(
            gateway,
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'data': serializer.data
        })


class DefaultGatewayAPIView(APIView):
    """
    دریافت درگاه پیش‌فرض
    
    GET /api/v1/payments/gateways/default/
    
    Returns the highest priority active gateway
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        gateway = PaymentGateway.objects.filter(
            is_active=True
        ).order_by('priority').first()
        
        if not gateway:
            return Response({
                'success': False,
                'error': 'هیچ درگاه پرداخت فعالی وجود ندارد'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        serializer = PaymentGatewayListSerializer(
            gateway,
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'data': serializer.data
        })


# =============================================================================
# PAYMENT INITIATION APIs
# =============================================================================

class PaymentInitiateAPIView(APIView, ClientIPMixin):
    """
    شروع فرآیند پرداخت جدید
    
    POST /api/v1/payments/initiate/
    
    Request Body:
        {
            "amount": 150000,
            "transaction_type": "order",  // order | wallet | subscription
            "order_id": "uuid",           // required for order type
            "gateway_type": "zarinpal",   // optional
            "description": "توضیحات",     // optional
            "callback_url": "https://..."  // optional custom callback
        }
    
    Response:
        {
            "success": true,
            "message": "تراکنش با موفقیت ایجاد شد",
            "data": {
                "transaction_id": "uuid",
                "amount": 150000,
                "amount_display": "150,000 تومان",
                "gateway": "zarinpal",
                "payment_url": "https://zarinpal.com/pg/StartPay/...",
                "authority": "A00000000000000000000000000123456789",
                "expires_at": "2024-01-15T12:30:00Z"
            }
        }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Validate input
        serializer = PaymentInitiateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        amount = data['amount']
        transaction_type = data['transaction_type']
        order_id = data.get('order_id')
        gateway_type = data.get('gateway_type')
        description = data.get('description', '')
        custom_callback = data.get('callback_url')
        
        try:
            # Handle order payment
            order = None
            if transaction_type == 'order':
                if not order_id:
                    return Response({
                        'success': False,
                        'error': 'شناسه سفارش الزامی است'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                from apps.orders.models import Order
                
                try:
                    order = Order.objects.get(
                        id=order_id,
                        user=request.user
                    )
                except Order.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'سفارش یافت نشد'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Validate order status
                valid_statuses = ['pending', 'awaiting_payment']
                if order.status not in valid_statuses:
                    return Response({
                        'success': False,
                        'error': f'سفارش در وضعیت {order.get_status_display()} قابل پرداخت نیست'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check for pending transactions
                pending_tx = Transaction.objects.filter(
                    order=order,
                    status='pending'
                ).first()
                
                if pending_tx:
                    # Return existing pending transaction
                    return Response({
                        'success': True,
                        'message': 'تراکنش در انتظار پرداخت وجود دارد',
                        'data': {
                            'transaction_id': str(pending_tx.transaction_id),
                            'amount': pending_tx.amount,
                            'amount_display': f'{pending_tx.amount:,} تومان',
                            'gateway': pending_tx.gateway.gateway_type if pending_tx.gateway else None,
                            'payment_url': self._build_payment_url(pending_tx),
                            'authority': pending_tx.authority or '',
                            'existing': True,
                        }
                    })
                
                # Auto-set amount from order if not specified
                if not amount:
                    amount = int(order.final_amount)
                
                # Auto-generate description
                if not description:
                    description = f'پرداخت سفارش شماره {order.order_number}'
            
            # Handle wallet deposit
            elif transaction_type == 'wallet':
                if not description:
                    description = f'شارژ کیف پول - مبلغ {amount:,} تومان'
            
            # Build callback URL
            callback_url = custom_callback or request.build_absolute_uri(
                reverse('payments:verify_callback')
            )
            
            # Initiate payment via PaymentService
            result = PaymentService.initiate_payment(
                user=request.user,
                amount=amount,
                transaction_type=transaction_type,
                order=order,
                gateway_type=gateway_type,
                description=description,
                callback_url=callback_url,
                ip_address=self.get_client_ip(request)
            )
            
            if result['success']:
                transaction = result['transaction']
                expires_at = timezone.now() + timezone.timedelta(minutes=15)
                
                return Response({
                    'success': True,
                    'message': 'تراکنش با موفقیت ایجاد شد',
                    'data': {
                        'transaction_id': str(transaction.transaction_id),
                        'amount': transaction.amount,
                        'amount_display': f'{transaction.amount:,} تومان',
                        'gateway': result.get('gateway_type', ''),
                        'gateway_name': transaction.gateway.name if transaction.gateway else '',
                        'payment_url': result['payment_url'],
                        'authority': result.get('authority', ''),
                        'expires_at': expires_at.isoformat(),
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'خطا در ایجاد تراکنش'),
                    'error_code': result.get('error_code')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except DjangoValidationError as e:
            return Response({
                'success': False,
                'error': str(e.message) if hasattr(e, 'message') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception(f"Payment initiation error: {e}")
            return Response({
                'success': False,
                'error': 'خطای سرور در ایجاد تراکنش'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _build_payment_url(self, transaction) -> str:
        """Build payment URL for existing transaction."""
        if not transaction.authority:
            return ''
        
        gateway = transaction.gateway
        if not gateway:
            return ''
        
        if gateway.gateway_type == 'zarinpal':
            if gateway.is_sandbox:
                return f'https://sandbox.zarinpal.com/pg/StartPay/{transaction.authority}'
            return f'https://www.zarinpal.com/pg/StartPay/{transaction.authority}'
        
        elif gateway.gateway_type == 'idpay':
            return f'https://idpay.ir/p/ws-sandbox/{transaction.authority}' if gateway.is_sandbox else f'https://idpay.ir/p/ws/{transaction.authority}'
        
        return ''


class WalletDepositInitiateAPIView(APIView, ClientIPMixin):
    """
    شروع شارژ کیف پول از طریق درگاه
    
    POST /api/v1/payments/wallet/deposit/
    
    Request Body:
        {
            "amount": 100000,
            "gateway_type": "zarinpal"  // optional
        }
    
    Response:
        Same as PaymentInitiateAPIView
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = WalletDepositSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        amount = data['amount']
        gateway_type = data.get('gateway_type')
        
        try:
            # Build callback URL
            callback_url = request.build_absolute_uri(
                reverse('payments:verify_callback')
            )
            
            # Create wallet deposit request first
            from apps.wallet.services import WalletService
            deposit_request = WalletService.create_deposit_request(
                user=request.user,
                amount=amount
            )
            
            # Initiate payment
            result = PaymentService.initiate_payment(
                user=request.user,
                amount=amount,
                transaction_type='wallet',
                order=None,
                gateway_type=gateway_type,
                description=f'شارژ کیف پول - مبلغ {amount:,} تومان',
                callback_url=callback_url,
                ip_address=self.get_client_ip(request),
                metadata={
                    'deposit_request_id': str(deposit_request.id)
                }
            )
            
            if result['success']:
                transaction = result['transaction']
                
                # Link deposit request to transaction
                deposit_request.payment_transaction = transaction
                deposit_request.save(update_fields=['payment_transaction'])
                
                return Response({
                    'success': True,
                    'message': 'درخواست شارژ کیف پول ایجاد شد',
                    'data': {
                        'transaction_id': str(transaction.transaction_id),
                        'deposit_request_id': str(deposit_request.id),
                        'amount': transaction.amount,
                        'amount_display': f'{transaction.amount:,} تومان',
                        'gateway': result.get('gateway_type', ''),
                        'gateway_name': transaction.gateway.name if transaction.gateway else '',
                        'payment_url': result['payment_url'],
                        'authority': result.get('authority', ''),
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                # Cleanup failed deposit request
                deposit_request.status = 'failed'
                deposit_request.save(update_fields=['status'])
                
                return Response({
                    'success': False,
                    'error': result.get('error', 'خطا در ایجاد درخواست پرداخت'),
                    'error_code': result.get('error_code')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception(f"Wallet deposit initiation error: {e}")
            return Response({
                'success': False,
                'error': 'خطای سرور در ایجاد درخواست شارژ'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderPaymentInitiateAPIView(APIView, ClientIPMixin):
    """
    شروع پرداخت یک سفارش خاص
    
    POST /api/v1/payments/orders/<order_id>/pay/
    
    Request Body:
        {
            "gateway_type": "zarinpal",     // optional
            "use_wallet_balance": true,     // optional - use wallet first
            "wallet_amount": 50000          // optional - specific wallet amount
        }
    
    Response:
        Mixed payment response with wallet + gateway breakdown
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, order_id):
        from apps.orders.models import Order
        from apps.wallet.models import Wallet
        
        # Get order
        try:
            order = Order.objects.select_related('user').get(
                id=order_id,
                user=request.user
            )
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'سفارش یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate order status
        valid_statuses = ['pending', 'awaiting_payment']
        if order.status not in valid_statuses:
            return Response({
                'success': False,
                                'error': f'سفارش در وضعیت «{order.get_status_display()}» قابل پرداخت نیست'
            }, status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        gateway_type = data.get('gateway_type')
        use_wallet = data.get('use_wallet_balance', False)
        wallet_amount = data.get('wallet_amount')

        try:
            # Prepare amounts
            payable_amount = int(order.final_amount)
            wallet_used = 0
            remaining_amount = payable_amount

            # Optional wallet usage
            if use_wallet:
                wallet = Wallet.objects.get(user=request.user)
                available = int(wallet.balance)

                if wallet_amount is not None:
                    wallet_amount = int(wallet_amount)
                    if wallet_amount < 0:
                        return Response({
                            'success': False,
                            'error': 'مبلغ کیف پول نمی‌تواند منفی باشد'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    wallet_used = min(wallet_amount, available, payable_amount)
                else:
                    wallet_used = min(available, payable_amount)

                remaining_amount = payable_amount - wallet_used

            # If wallet covers entire order → auto complete without gateway
            if remaining_amount == 0:
                from apps.wallet.services import WalletService

                with db_transaction.atomic():
                    WalletService.consume_balance(
                        user=request.user,
                        amount=wallet_used,
                        reason=f'پرداخت سفارش {order.order_number}'
                    )
                    order.mark_as_paid(payment_method='wallet')

                return Response({
                    'success': True,
                    'message': 'سفارش با موفقیت از طریق کیف پول پرداخت شد',
                    'data': {
                        'order_id': str(order.id),
                        'order_number': order.order_number,
                        'wallet_used': wallet_used,
                        'payment_method': 'wallet'
                    }
                }, status=status.HTTP_200_OK)

            # Otherwise → initiate gateway payment for the remaining amount
            callback_url = request.build_absolute_uri(
                reverse('payments:verify_callback')
            )

            result = PaymentService.initiate_payment(
                user=request.user,
                amount=remaining_amount,
                transaction_type='order',
                order=order,
                gateway_type=gateway_type,
                description=f'پرداخت سفارش {order.order_number}',
                callback_url=callback_url,
                ip_address=self.get_client_ip(request),
                metadata={
                    'wallet_used': wallet_used
                }
            )

            if result['success']:
                transaction = result['transaction']

                return Response({
                    'success': True,
                    'message': 'درخواست پرداخت ثبت شد',
                    'data': {
                        'order_id': str(order.id),
                        'order_number': order.order_number,
                        'wallet_used': wallet_used,
                        'payable_amount': remaining_amount,
                        'transaction_id': str(transaction.transaction_id),
                        'payment_url': result['payment_url'],
                        'gateway': result.get('gateway_type', ''),
                        'gateway_name': transaction.gateway.name if transaction.gateway else ''
                    }
                }, status=status.HTTP_201_CREATED)

            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'خطا در ایجاد درخواست پرداخت'),
                    'error_code': result.get('error_code')
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception(f"Order payment initiation error: {e}")
            return Response({
                'success': False,
                'error': 'خطای سرور در شروع پرداخت سفارش'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================================================================
# PAYMENT VERIFICATION (CALLBACK HANDLER)
# ===================================================================================

class PaymentVerifyAPIView(APIView, ClientIPMixin):
    """
    Callback endpoint for gateway verification.
    
    GET/POST /api/v1/payments/verify/
    
    Expected gateway parameters:
        - Zarinpal: Status, Authority
        - IDPay: status, track_id, id, order_id
    
    Response:
        - success/failure with order/wallet update status
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return self._handle_verification(request)

    def post(self, request):
        return self._handle_verification(request)

    def _handle_verification(self, request):
        try:
            serializer = PaymentVerifySerializer(data=request.query_params or request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            data = serializer.validated_data
            transaction_id = data['transaction_id']

            try:
                tx = Transaction.objects.select_related('gateway', 'order', 'user').get(transaction_id=transaction_id)
            except Transaction.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'تراکنش یافت نشد'
                }, status=status.HTTP_404_NOT_FOUND)

            result = PaymentService.verify_payment(
                transaction=tx,
                gateway_response=request.query_params or request.data,
                ip_address=self.get_client_ip(request)
            )

            if result['success']:
                response_data = {
                    'success': True,
                    'message': 'پرداخت با موفقیت انجام شد',
                    'transaction_id': str(tx.transaction_id),
                    'amount': tx.amount,
                    'amount_display': f'{tx.amount:,} تومان',
                    'order_id': str(tx.order.id) if tx.order else None,
                    'wallet_deposit': tx.transaction_type == 'wallet',
                    'paid_at': tx.paid_at.isoformat() if tx.paid_at else None
                }
                return Response(response_data, status=status.HTTP_200_OK)

            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'پرداخت ناموفق بود'),
                    'error_code': result.get('error_code')
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception(f"Payment verification error: {e}")
            return Response({
                'success': False,
                'error': 'خطای سرور در تأیید پرداخت'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================================================================
# TRANSACTION HISTORY
# ===================================================================================

class TransactionHistoryAPIView(APIView):
    """
    لیست تراکنش‌های کاربر
    
    GET /api/v1/payments/transactions/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Transaction.objects.filter(user=request.user).order_by('-created_at')
        serializer = TransactionListSerializer(qs, many=True, context={'request': request})
        return Response({
            'success': True,
            'count': qs.count(),
            'data': serializer.data
        })


# ===================================================================================
# REFUND REQUEST
# ===================================================================================

class RefundRequestAPIView(APIView):
    """
    درخواست بازگشت وجه
    
    POST /api/v1/payments/refund/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RefundRequestSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        refund = serializer.save()

        return Response({
            'success': True,
            'message': 'درخواست بازگشت وجه ثبت شد',
            'data': {
                'refund_id': str(refund.id),
                'amount': refund.amount,
                'status': refund.status
            }
        }, status=status.HTTP_201_CREATED)


# ===================================================================================
# TRANSACTION DETAIL & STATUS APIs
# ===================================================================================

class TransactionDetailAPIView(APIView):
    """
    جزئیات کامل یک تراکنش
    
    GET /api/v1/payments/transactions/<transaction_id>/
    
    Response:
        {
            "success": true,
            "data": {
                "transaction_id": "uuid",
                "amount": 150000,
                "status": "completed",
                "gateway": {...},
                "order": {...},
                "created_at": "...",
                "paid_at": "..."
            }
        }
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, transaction_id):
        try:
            transaction = Transaction.objects.select_related(
                'gateway', 'order', 'user'
            ).get(
                transaction_id=transaction_id,
                user=request.user
            )
        except Transaction.DoesNotExist:
            return Response({
                'success': False,
                'error': 'تراکنش یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TransactionSerializer(
            transaction,
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'data': serializer.data
        })


class TransactionStatusAPIView(APIView):
    """
    وضعیت فعلی تراکنش (برای polling)
    
    GET /api/v1/payments/transactions/<transaction_id>/status/
    
    Response:
        {
            "success": true,
            "data": {
                "transaction_id": "uuid",
                "status": "pending",
                "status_display": "در انتظار پرداخت",
                "is_final": false,
                "can_retry": true
            }
        }
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, transaction_id):
        try:
            transaction = Transaction.objects.get(
                transaction_id=transaction_id,
                user=request.user
            )
        except Transaction.DoesNotExist:
            return Response({
                'success': False,
                'error': 'تراکنش یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # تعیین وضعیت نهایی بودن
        final_statuses = ['completed', 'failed', 'cancelled', 'refunded']
        is_final = transaction.status in final_statuses
        
        # تعیین قابلیت تلاش مجدد
        can_retry = transaction.status in ['failed', 'cancelled']
        
        # نمایش فارسی وضعیت
        status_display_map = {
            'pending': 'در انتظار پرداخت',
            'processing': 'در حال پردازش',
            'completed': 'موفق',
            'failed': 'ناموفق',
            'cancelled': 'لغو شده',
            'refunded': 'بازگشت داده شده',
            'expired': 'منقضی شده',
        }
        
        return Response({
            'success': True,
            'data': {
                'transaction_id': str(transaction.transaction_id),
                'status': transaction.status,
                'status_display': status_display_map.get(
                    transaction.status, 
                    transaction.status
                ),
                'is_final': is_final,
                'can_retry': can_retry,
                'amount': transaction.amount,
                'paid_at': transaction.paid_at.isoformat() if transaction.paid_at else None,
                'updated_at': transaction.updated_at.isoformat() if hasattr(transaction, 'updated_at') else None,
            }
        })


# ===================================================================================
# REFUND STATUS API
# ===================================================================================

class RefundStatusAPIView(APIView):
    """
    وضعیت درخواست بازگشت وجه
    
    GET /api/v1/payments/refund/<refund_id>/status/
    
    Response:
        {
            "success": true,
            "data": {
                "refund_id": "uuid",
                "status": "pending",
                "status_display": "در انتظار بررسی",
                "amount": 50000,
                "reason": "...",
                "admin_note": "...",
                "created_at": "...",
                "processed_at": null
            }
        }
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, refund_id):
        from .models import RefundRequest
        
        try:
            refund = RefundRequest.objects.select_related(
                'transaction', 'user'
            ).get(
                id=refund_id,
                user=request.user
            )
        except RefundRequest.DoesNotExist:
            return Response({
                'success': False,
                'error': 'درخواست بازگشت وجه یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # نمایش فارسی وضعیت
        status_display_map = {
            'pending': 'در انتظار بررسی',
            'approved': 'تأیید شده',
            'processing': 'در حال پردازش',
            'completed': 'انجام شده',
            'rejected': 'رد شده',
            'cancelled': 'لغو شده',
        }
        
        return Response({
            'success': True,
            'data': {
                'refund_id': str(refund.id),
                'status': refund.status,
                'status_display': status_display_map.get(
                    refund.status,
                    refund.status
                ),
                'amount': refund.amount,
                'reason': getattr(refund, 'reason', ''),
                'admin_note': getattr(refund, 'admin_note', ''),
                'transaction_id': str(refund.transaction.transaction_id) if refund.transaction else None,
                'created_at': refund.created_at.isoformat() if hasattr(refund, 'created_at') else None,
                'processed_at': refund.processed_at.isoformat() if hasattr(refund, 'processed_at') and refund.processed_at else None,
            }
        })
