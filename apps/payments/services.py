# apps/payments/services.py

"""
Payment Services Module
=======================
Unified payment service layer for handling multiple payment gateways.
Supports ZarinPal, IDPay, and extensible for future gateways.
"""

import logging
import requests
from decimal import Decimal
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.urls import reverse

from .models import PaymentGateway, Transaction

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes & Enums
# =============================================================================

class PaymentError(Exception):
    """Base exception for payment errors."""
    def __init__(self, message: str, code: str = 'UNKNOWN', details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class GatewayError(PaymentError):
    """Gateway-specific errors."""
    pass


class ValidationError(PaymentError):
    """Payment validation errors."""
    pass


@dataclass
class PaymentRequest:
    """Data class for payment request."""
    user: Any
    amount: int  # Toman
    transaction_type: str
    description: str = ''
    order: Any = None
    callback_url: str = ''
    mobile: str = ''
    email: str = ''
    ip_address: str = ''
    user_agent: str = ''


@dataclass
class PaymentResult:
    """Data class for payment result."""
    success: bool
    transaction: Optional[Transaction] = None
    redirect_url: str = ''
    error_code: str = ''
    error_message: str = ''
    
    @classmethod
    def success_result(cls, transaction: Transaction, redirect_url: str):
        return cls(
            success=True,
            transaction=transaction,
            redirect_url=redirect_url
        )
    
    @classmethod
    def error_result(cls, code: str, message: str, transaction: Transaction = None):
        return cls(
            success=False,
            transaction=transaction,
            error_code=code,
            error_message=message
        )


@dataclass
class VerifyResult:
    """Data class for verification result."""
    success: bool
    transaction: Optional[Transaction] = None
    reference_id: str = ''
    card_number: str = ''
    error_code: str = ''
    error_message: str = ''


# =============================================================================
# ZarinPal Gateway Service
# =============================================================================

class ZarinPalService:
    """
    ZarinPal Payment Gateway Service.
    Supports both sandbox and production environments.
    """
    
    # API Endpoints
    SANDBOX_REQUEST_URL = 'https://sandbox.zarinpal.com/pg/v4/payment/request.json'
    SANDBOX_VERIFY_URL = 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json'
    PRODUCTION_REQUEST_URL = 'https://api.zarinpal.com/pg/v4/payment/request.json'
    PRODUCTION_VERIFY_URL = 'https://api.zarinpal.com/pg/v4/payment/verify.json'
    
    # Error codes mapping
    ERROR_CODES = {
        -1: 'اطلاعات ارسالی ناقص است',
        -2: 'IP یا مرچنت کد صحیح نیست',
        -3: 'با توجه به محدودیت‌های شاپرک، امکان پرداخت وجود ندارد',
        -4: 'سطح تایید پذیرنده پایین‌تر از حد مجاز است',
        -11: 'درخواست مورد نظر یافت نشد',
        -12: 'امکان ویرایش درخواست وجود ندارد',
        -21: 'هیچ نوع عملیات مالی برای این تراکنش یافت نشد',
        -22: 'تراکنش ناموفق است',
        -33: 'رقم تراکنش با رقم پرداخت شده مطابقت ندارد',
        -34: 'سقف تقسیم تراکنش از رقم پرداخت بیشتر است',
        -40: 'اجازه دسترسی به متد مربوطه وجود ندارد',
        -41: 'اطلاعات ارسال شده غیرمعتبر است',
        -42: 'مدت زمان معتبر طول عمر شناسه پرداخت باید بین 30 دقیقه تا 45 روز باشد',
        -54: 'درخواست مورد نظر آرشیو شده است',
        100: 'عملیات با موفقیت انجام شد',
        101: 'عملیات پرداخت موفق بوده و قبلا تایید شده است',
    }
    
    def __init__(self, gateway: PaymentGateway):
        """Initialize with gateway configuration."""
        self.gateway = gateway
        self.merchant_id = gateway.merchant_id
        self.is_sandbox = gateway.is_sandbox
        self.timeout = 30
    
    @property
    def request_url(self) -> str:
        return self.SANDBOX_REQUEST_URL if self.is_sandbox else self.PRODUCTION_REQUEST_URL
    
    @property
    def verify_url(self) -> str:
        return self.SANDBOX_VERIFY_URL if self.is_sandbox else self.PRODUCTION_VERIFY_URL
    
    def _get_error_message(self, code: int) -> str:
        """Get Persian error message for error code."""
        return self.ERROR_CODES.get(code, f'خطای ناشناخته ({code})')
    
    def request_payment(
        self,
        amount_rial: int,
        callback_url: str,
        description: str,
        mobile: str = '',
        email: str = ''
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Request a new payment from ZarinPal.
        
        Args:
            amount_rial: Amount in Rial
            callback_url: URL to redirect after payment
            description: Payment description
            mobile: Customer mobile (optional)
            email: Customer email (optional)
        
        Returns:
            Tuple of (success, response_data)
        """
        payload = {
            'merchant_id': self.merchant_id,
            'amount': amount_rial,
            'callback_url': callback_url,
            'description': description,
        }
        
        # Add optional metadata
        metadata = {}
        if mobile:
            metadata['mobile'] = mobile
        if email:
            metadata['email'] = email
        if metadata:
            payload['metadata'] = metadata
        
        try:
            logger.info(f"ZarinPal payment request: {amount_rial} Rial")
            
            response = requests.post(
                self.request_url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('data') and data['data'].get('code') == 100:
                return True, {
                    'authority': data['data']['authority'],
                    'fee': data['data'].get('fee', 0),
                    'fee_type': data['data'].get('fee_type', ''),
                }
            else:
                error_code = data.get('errors', {}).get('code', -1)
                return False, {
                    'error_code': str(error_code),
                    'error_message': self._get_error_message(error_code),
                    'raw_response': data,
                }
        
        except requests.RequestException as e:
            logger.error(f"ZarinPal request error: {e}")
            return False, {
                'error_code': 'CONNECTION_ERROR',
                'error_message': 'خطا در ارتباط با درگاه پرداخت',
                'raw_response': str(e),
            }
    
    def verify_payment(
        self,
        authority: str,
        amount_rial: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify a payment with ZarinPal.
        
        Args:
            authority: Authority code from payment request
            amount_rial: Original amount in Rial
        
        Returns:
            Tuple of (success, response_data)
        """
        payload = {
            'merchant_id': self.merchant_id,
            'authority': authority,
            'amount': amount_rial,
        }
        
        try:
            logger.info(f"ZarinPal verify request: {authority}")
            
            response = requests.post(
                self.verify_url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('data') and data['data'].get('code') in [100, 101]:
                return True, {
                    'ref_id': str(data['data']['ref_id']),
                    'card_pan': data['data'].get('card_pan', ''),
                    'card_hash': data['data'].get('card_hash', ''),
                    'fee': data['data'].get('fee', 0),
                    'fee_type': data['data'].get('fee_type', ''),
                }
            else:
                error_code = data.get('errors', {}).get('code', -1)
                return False, {
                    'error_code': str(error_code),
                    'error_message': self._get_error_message(error_code),
                    'raw_response': data,
                }
        
        except requests.RequestException as e:
            logger.error(f"ZarinPal verify error: {e}")
            return False, {
                'error_code': 'CONNECTION_ERROR',
                'error_message': 'خطا در ارتباط با درگاه پرداخت',
                'raw_response': str(e),
            }


# =============================================================================
# IDPay Gateway Service
# =============================================================================

class IDPayService:
    """
    IDPay Payment Gateway Service.
    Supports both sandbox and production environments.
    """
    
    # API Endpoints
    SANDBOX_REQUEST_URL = 'https://sandbox.idpay.ir/v1.1/payment'
    SANDBOX_VERIFY_URL = 'https://sandbox.idpay.ir/v1.1/payment/verify'
    PRODUCTION_REQUEST_URL = 'https://api.idpay.ir/v1.1/payment'
    PRODUCTION_VERIFY_URL = 'https://api.idpay.ir/v1.1/payment/verify'
    
    # Status codes
    STATUS_CODES = {
        1: 'پرداخت انجام نشده است',
        2: 'پرداخت ناموفق بوده است',
        3: 'خطا رخ داده است',
        4: 'بلوکه شده',
        5: 'برگشت به پرداخت کننده',
        6: 'برگشت خورده سیستمی',
        7: 'انصراف از پرداخت',
        8: 'به درگاه پرداخت منتقل شد',
        10: 'در انتظار تایید پرداخت',
        100: 'پرداخت تایید شده است',
        101: 'پرداخت قبلا تایید شده است',
        200: 'به دریافت کننده واریز شد',
    }
    
    ERROR_CODES = {
        11: 'کاربر مسدود شده است',
        12: 'API Key یافت نشد',
        13: 'درخواست شما از IP نامعتبر ارسال شده است',
        14: 'وب سرویس شما در حال بررسی است',
        21: 'حساب بانکی متصل نیست',
        22: 'وب‌سرویس یافت نشد',
        23: 'اعتبارسنجی وب سرویس ناموفق بود',
        24: 'حساب بانکی تایید نشده است',
        31: 'کد تراکنش id نباید خالی باشد',
        32: 'مبلغ نباید خالی باشد',
        33: 'مبلغ باید بین 1,000 تا 500,000,000 ریال باشد',
        34: 'مبلغ نامعتبر است',
        35: 'تعداد تراکنش‌های این IP بیش از حد مجاز است',
        36: 'callback نمی‌تواند خالی باشد',
        37: 'callback نامعتبر است',
        41: 'فیلتر تراکنش‌ها نامعتبر است',
        42: 'خطا در ارتباط با درگاه بانک',
        51: 'تراکنش ایجاد نشد',
        52: 'استعلام نتیجه انجام نشد',
        53: 'تایید پرداخت امکان پذیر نیست',
        54: 'مدت زمان تایید پرداخت سپری شده است',
    }
    
    def __init__(self, gateway: PaymentGateway):
        """Initialize with gateway configuration."""
        self.gateway = gateway
        self.api_key = gateway.merchant_id  # IDPay uses API Key
        self.is_sandbox = gateway.is_sandbox
        self.timeout = 30
    
    @property
    def request_url(self) -> str:
        return self.SANDBOX_REQUEST_URL if self.is_sandbox else self.PRODUCTION_REQUEST_URL
    
    @property
    def verify_url(self) -> str:
        return self.SANDBOX_VERIFY_URL if self.is_sandbox else self.PRODUCTION_VERIFY_URL
    
    @property
    def headers(self) -> Dict[str, str]:
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': self.api_key,
        }
        if self.is_sandbox:
            headers['X-SANDBOX'] = '1'
        return headers
    
    def _get_error_message(self, code: int) -> str:
        """Get Persian error message for error code."""
        return self.ERROR_CODES.get(code, self.STATUS_CODES.get(code, f'خطای ناشناخته ({code})'))
    
    def request_payment(self,
        order_id: str,
        amount_rial: int,
        callback_url: str,
        name: str = '',
        phone: str = '',
        email: str = '',
        description: str = ''
    ) ->Tuple[bool, Dict[str, Any]]:
        """
        Request a new payment from IDPay.
        
        Args:
            order_id: Unique order identifier
            amount_rial: Amount in Rial
            callback_url: URL to redirect after payment
            name: Customer name (optional)
            phone: Customer phone (optional)
            email: Customer email (optional)
            description: Payment description (optional)
        
            Returns:
            Tuple of (success, response_data) """
        payload = {
            'order_id': order_id,
            'amount': amount_rial,
            'callback': callback_url,
        }
    
        if name:
            payload['name'] = name
        if phone:
            payload['phone'] = phone
        if email:
            payload['mail'] = email
        if description:
            payload['desc'] = description
        
        try:
            logger.info(f"IDPay payment request: {amount_rial} Rial, order: {order_id}")
            
            response = requests.post(
                self.request_url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            
            data = response.json()
            
            if response.status_code == 201 and data.get('id'):
                return True, {
                    'id': data['id'],
                    'link': data['link'],
                }
            else:
                error_code = data.get('error_code', 0)
                return False, {
                    'error_code': str(error_code),
                    'error_message': data.get('error_message', self._get_error_message(error_code)),
                    'raw_response': data,
                }
        
        except requests.RequestException as e:
            logger.error(f"IDPay request error: {e}")
            return False, {
                'error_code': 'CONNECTION_ERROR',
                'error_message': 'خطا در ارتباط با درگاه پرداخت',
                'raw_response': str(e),
            }
    
    def verify_payment(
        self,
        transaction_id: str,
        order_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify a payment with IDPay.
        
        Args:
            transaction_id: IDPay transaction ID
            order_id: Original order ID
        
        Returns:
            Tuple of (success, response_data)
        """
        payload = {
            'id': transaction_id,
            'order_id': order_id,
        }
        
        try:
            logger.info(f"IDPay verify request: {transaction_id}")
            
            response = requests.post(
                self.verify_url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            
            data = response.json()
            
            if response.status_code == 200 and data.get('status') in [100, 101]:
                return True, {
                    'track_id': str(data.get('track_id', '')),
                    'card_no': data.get('payment', {}).get('card_no', ''),
                    'hashed_card_no': data.get('payment', {}).get('hashed_card_no', ''),
                    'amount': data.get('amount', 0),
                    'status': data.get('status'),
                    'date': data.get('date'),
                    'verify_date': data.get('verify', {}).get('date'),
                }
            else:
                error_code = data.get('error_code', data.get('status', 0))
                return False, {
                    'error_code': str(error_code),
                    'error_message': data.get('error_message', self._get_error_message(error_code)),
                    'raw_response': data,
                }
        
        except requests.RequestException as e:
            logger.error(f"IDPay verify error: {e}")
            return False, {
                'error_code': 'CONNECTION_ERROR',
                'error_message': 'خطا در ارتباط با درگاه پرداخت',
                'raw_response': str(e),
            }


# =============================================================================
# Unified Payment Service
# =============================================================================

class PaymentService:
    """
    Unified Payment Service.
    Handles gateway selection, transaction creation, and payment flow.
    """
    
    @staticmethod
    def get_active_gateway(gateway_type: str = None) -> Optional[PaymentGateway]:
        """Get active payment gateway, optionally filtered by type."""
        queryset = PaymentGateway.objects.filter(is_active=True)
        
        if gateway_type:
            queryset = queryset.filter(gateway_type=gateway_type)
        
        return queryset.order_by('-priority').first()
    
    @staticmethod
    def get_available_gateways() -> list:
        """Get all available payment gateways."""
        return list(
            PaymentGateway.objects.filter(is_active=True)
            .order_by('-priority')
            .values('id', 'name', 'gateway_type', 'logo', 'description')
        )
    
    @staticmethod
    def get_gateway_service(gateway: PaymentGateway):
        """
        Get appropriate service instance for gateway.
        
        Returns:
            ZarinPalService or IDPayService instance
        """
        if gateway.gateway_type == 'zarinpal':
            return ZarinPalService(gateway)
        elif gateway.gateway_type == 'idpay':
            return IDPayService(gateway)
        else:
            raise GatewayError(
                f"Unsupported gateway type: {gateway.gateway_type}",
                code='UNSUPPORTED_GATEWAY'
            )
    
    @classmethod
    @transaction.atomic
    def initiate_payment(
        cls,
        request,
        amount: int,
        transaction_type: str = 'order',
        order=None,
        gateway_type: str = None,
        description: str = ''
    ) -> PaymentResult:
        """
        Initiate a new payment transaction.
        
        Args:
            request: Django HTTP request
            amount: Amount in Toman
            transaction_type: Type of transaction (order, deposit, etc.)
            order: Related order instance (optional)
            gateway_type: Preferred gateway type (optional)
            description: Payment description
        
        Returns:
            PaymentResult with transaction and redirect URL
        """
        from django.urls import reverse
        
        # Get user info
        user = request.user if request.user.is_authenticated else None
        
        if not user:
            return PaymentResult.error_result(
                'AUTH_REQUIRED',
                'برای پرداخت باید وارد حساب کاربری شوید'
            )
        
        # Validate amount
        if amount < 1000:
            return PaymentResult.error_result(
                'INVALID_AMOUNT',
                'حداقل مبلغ پرداخت ۱,۰۰۰ تومان است'
            )
        
        if amount > 500_000_000:
            return PaymentResult.error_result(
                'AMOUNT_EXCEEDED',
                'حداکثر مبلغ پرداخت ۵۰۰ میلیون تومان است'
            )
        
        # Get active gateway
        gateway = cls.get_active_gateway(gateway_type)
        if not gateway:
            return PaymentResult.error_result(
                'NO_GATEWAY',
                'درگاه پرداخت فعالی یافت نشد'
            )
        
        # Get client info
        ip_address = cls._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        # Create transaction record
        transaction_obj = Transaction.objects.create(
            user=user,
            order=order,
            gateway=gateway,
            transaction_type=transaction_type,
            amount=amount,
            status='pending',
            ip_address=ip_address,
            user_agent=user_agent,
            description=description or f'پرداخت {transaction_type}'
        )
        
        # Build callback URL
        callback_url = request.build_absolute_uri(
            reverse('payments:callback', kwargs={'transaction_id': transaction_obj.transaction_id})
        )
        
        # Get gateway service
        try:
            service = cls.get_gateway_service(gateway)
        except GatewayError as e:
            transaction_obj.status = 'failed'
            transaction_obj.error_code = e.code
            transaction_obj.error_message = e.message
            transaction_obj.save()
            return PaymentResult.error_result(e.code, e.message, transaction_obj)
        
        # Request payment from gateway
        amount_rial = amount * 10  # Convert Toman to Rial
        
        if gateway.gateway_type == 'zarinpal':
            success, response = service.request_payment(
                amount_rial=amount_rial,
                callback_url=callback_url,
                description=description or f'سفارش {order.order_number if order else transaction_obj.transaction_id}',
                mobile=user.phone if hasattr(user, 'phone') else '',
                email=user.email or ''
            )
            
            if success:
                transaction_obj.authority = response['authority']
                transaction_obj.gateway_data = response
                transaction_obj.save()
                
                # Build redirect URL
                if gateway.is_sandbox:
                    redirect_url = f"https://sandbox.zarinpal.com/pg/StartPay/{response['authority']}"
                else:
                    redirect_url = f"https://www.zarinpal.com/pg/StartPay/{response['authority']}"
                
                return PaymentResult.success_result(transaction_obj, redirect_url)
            else:
                transaction_obj.status = 'failed'
                transaction_obj.error_code = response.get('error_code', 'UNKNOWN')
                transaction_obj.error_message = response.get('error_message', 'خطای ناشناخته')
                transaction_obj.gateway_data = response
                transaction_obj.save()
                
                return PaymentResult.error_result(
                    transaction_obj.error_code,
                    transaction_obj.error_message,
                    transaction_obj
                )
        
        elif gateway.gateway_type == 'idpay':
            success, response = service.request_payment(
                order_id=str(transaction_obj.transaction_id),
                amount_rial=amount_rial,
                callback_url=callback_url,
                name=user.get_full_name() if hasattr(user, 'get_full_name') else '',
                phone=user.phone if hasattr(user, 'phone') else '',
                email=user.email or '',
                description=description
            )
            
            if success:
                transaction_obj.authority = response['id']
                transaction_obj.gateway_data = response
                transaction_obj.save()
                
                return PaymentResult.success_result(transaction_obj, response['link'])
            else:
                transaction_obj.status = 'failed'
                transaction_obj.error_code = response.get('error_code', 'UNKNOWN')
                transaction_obj.error_message = response.get('error_message', 'خطای ناشناخته')
                transaction_obj.gateway_data = response
                transaction_obj.save()
                
                return PaymentResult.error_result(
                    transaction_obj.error_code,
                    transaction_obj.error_message,
                    transaction_obj
                )
        
        return PaymentResult.error_result('UNKNOWN_GATEWAY', 'نوع درگاه پشتیبانی نمی‌شود')
    
    @classmethod
    @transaction.atomic
    def verify_payment(
        cls,
        transaction_obj: Transaction,
        gateway_data: dict = None
    ) -> VerifyResult:
        """
        Verify a payment transaction.
        
        Args:
            transaction_obj: Transaction to verify
            gateway_data: Additional data from gateway callback
        
        Returns:
            VerifyResult with verification status
        """
        # Check if already verified
        if transaction_obj.status == 'completed':
            return VerifyResult(
                success=True,
                transaction=transaction_obj,
                reference_id=transaction_obj.reference_id or '',
                error_code='ALREADY_VERIFIED',
                error_message='این تراکنش قبلاً تأیید شده است'
            )
        
        # Check if expired
        if transaction_obj.is_expired:
            transaction_obj.status = 'expired'
            transaction_obj.save()
            return VerifyResult(
                success=False,
                transaction=transaction_obj,
                error_code='EXPIRED',
                error_message='زمان پرداخت منقضی شده است'
            )
        
        # Get gateway service
        gateway = transaction_obj.gateway
        try:
            service = cls.get_gateway_service(gateway)
        except GatewayError as e:
            return VerifyResult(
                success=False,
                transaction=transaction_obj,
                error_code=e.code,
                error_message=e.message
            )
        
        amount_rial = transaction_obj.amount * 10
        
        # Verify with gateway
        if gateway.gateway_type == 'zarinpal':
            success, response = service.verify_payment(
                authority=transaction_obj.authority,
                amount_rial=amount_rial
            )
            
            if success:
                transaction_obj.status = 'completed'
                transaction_obj.reference_id = response.get('ref_id', '')
                transaction_obj.card_number = response.get('card_pan', '')
                transaction_obj.paid_at = timezone.now()
                transaction_obj.gateway_data = {
                    **transaction_obj.gateway_data,
                    'verify_response': response
                }
                transaction_obj.save()
                
                # Process post-payment actions
                cls._process_successful_payment(transaction_obj)
                
                return VerifyResult(
                    success=True,
                    transaction=transaction_obj,
                    reference_id=response.get('ref_id', ''),
                    card_number=response.get('card_pan', '')
                )
            else:
                transaction_obj.status = 'failed'
                transaction_obj.error_code = response.get('error_code', 'UNKNOWN')
                transaction_obj.error_message = response.get('error_message', 'تأیید پرداخت ناموفق')
                transaction_obj.gateway_data = {
                    **transaction_obj.gateway_data,
                    'verify_response': response
                }
                transaction_obj.save()
                
                return VerifyResult(
                    success=False,
                    transaction=transaction_obj,
                    error_code=transaction_obj.error_code,
                    error_message=transaction_obj.error_message
                )
        
        elif gateway.gateway_type == 'idpay':
                # IDPay sends transaction ID in callback
            idpay_id = gateway_data.get('id') if gateway_data else transaction_obj.authority

            success, response = service.verify_payment(
                transaction_id=idpay_id,
                order_id=str(transaction_obj.transaction_id)
            )

            if success:
                transaction_obj.status = 'completed'
                transaction_obj.reference_id = response.get('track_id', '')
                transaction_obj.card_number = response.get('card_no', '')
                transaction_obj.paid_at = timezone.now()
                transaction_obj.gateway_data = {
                    **transaction_obj.gateway_data,
                    'verify_response': response
                }
                transaction_obj.save()

                # Finalize order or wallet
                cls._process_successful_payment(transaction_obj)

                return VerifyResult(
                    success=True,
                    transaction=transaction_obj,
                    reference_id=response.get('track_id', ''),
                    card_number=response.get('card_no', '')
                )
            else:
                transaction_obj.status = 'failed'
                transaction_obj.error_code = response.get('error_code', 'UNKNOWN')
                transaction_obj.error_message = response.get('error_message', 'تأیید پرداخت ناموفق')
                transaction_obj.gateway_data = {
                    **transaction_obj.gateway_data,
                    'verify_response': response
                }
                transaction_obj.save()

                return VerifyResult(
                    success=False,
                    transaction=transaction_obj,
                    error_code=transaction_obj.error_code,
                    error_message=transaction_obj.error_message
                )

        return VerifyResult(
            success=False,
            transaction=transaction_obj,
            error_code='UNSUPPORTED_GATEWAY',
            error_message='نوع درگاه پشتیبانی نمی‌شود'
        )

    # -------------------------------------------------------------------------
    # Process user order or wallet after verified payment
    # -------------------------------------------------------------------------

    @staticmethod
    def _process_successful_payment(transaction: Transaction):
        """
        Trigger order completion or wallet deposit after successful payment.
        """

        if transaction.transaction_type == 'order' and transaction.order:
            order = transaction.order
            order.status = 'paid'
            order.payment = transaction
            order.paid_at = timezone.now()
            order.save()

        elif transaction.transaction_type == 'wallet':
            user = transaction.user
            profile = user.profile
            profile.wallet_balance += transaction.amount
            profile.save()

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    @staticmethod
    def _get_client_ip(request) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
