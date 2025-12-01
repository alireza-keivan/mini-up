# apps/payments/models.py

import uuid
import secrets
from decimal import Decimal
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator


class PaymentGateway(models.Model):
    """
    Payment gateway configuration.
    Allows enabling/disabling gateways and storing credentials.
    """
    
    class GatewayType(models.TextChoices):
        ZARINPAL = 'zarinpal', 'زرین‌پال'
        IDPAY = 'idpay', 'آیدی‌پی'
    
    name = models.CharField(max_length=50, verbose_name='نام درگاه')
    gateway_type = models.CharField(
        max_length=20,
        choices=GatewayType.choices,
        unique=True,
        verbose_name='نوع درگاه'
    )
    
    # Credentials (encrypted in production)
    merchant_id = models.CharField(
        max_length=100,
        verbose_name='کد پذیرنده',
        help_text='Merchant ID یا API Key'
    )
    api_key = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='کلید API',
        help_text='در صورت نیاز درگاه'
    )
    
    # Settings
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_sandbox = models.BooleanField(
        default=True,
        verbose_name='حالت تست',
        help_text='برای تست درگاه فعال کنید'
    )
    
    # Priority (for fallback)
    priority = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='اولویت',
        help_text='درگاه با اولویت بالاتر ابتدا نمایش داده می‌شود'
    )
    
    # Limits
    min_amount = models.PositiveIntegerField(
        default=1000,
        verbose_name='حداقل مبلغ (تومان)'
    )
    max_amount = models.PositiveIntegerField(
        default=50000000,
        verbose_name='حداکثر مبلغ (تومان)'
    )
    
    # Stats
    total_transactions = models.PositiveIntegerField(default=0, verbose_name='تعداد تراکنش')
    successful_transactions = models.PositiveIntegerField(default=0, verbose_name='تراکنش موفق')
    total_amount = models.BigIntegerField(default=0, verbose_name='مجموع مبلغ')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'درگاه پرداخت'
        verbose_name_plural = 'درگاه‌های پرداخت'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        status = '✓' if self.is_active else '✗'
        return f'{self.name} [{status}]'
    
    @property
    def success_rate(self):
        """Calculate success rate percentage."""
        if self.total_transactions == 0:
            return 0
        return round((self.successful_transactions / self.total_transactions) * 100, 1)
    
    def increment_stats(self, amount, is_successful=True):
        """Update gateway statistics."""
        self.total_transactions += 1
        if is_successful:
            self.successful_transactions += 1
            self.total_amount += amount
        self.save(update_fields=[
            'total_transactions', 
            'successful_transactions', 
            'total_amount',
            'updated_at'
        ])
    
    @classmethod
    def get_active_gateways(cls):
        """Get all active gateways ordered by priority."""
        return cls.objects.filter(is_active=True).order_by('-priority')
    
    @classmethod
    def get_default_gateway(cls):
        """Get the highest priority active gateway."""
        return cls.objects.filter(is_active=True).order_by('-priority').first()


class Transaction(models.Model):
    """
    Payment transaction record.
    Tracks all payment attempts through gateways.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار'
        PROCESSING = 'processing', 'در حال پردازش'
        SUCCESS = 'success', 'موفق'
        FAILED = 'failed', 'ناموفق'
        CANCELLED = 'cancelled', 'لغو شده'
        REFUNDED = 'refunded', 'مسترد شده'
        EXPIRED = 'expired', 'منقضی شده'
    
    class TransactionType(models.TextChoices):
        ORDER_PAYMENT = 'order', 'پرداخت سفارش'
        WALLET_TOPUP = 'topup', 'شارژ کیف پول'
        CONSULTATION = 'consultation', 'پرداخت مشاوره'
    
    # Identification
    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='شناسه تراکنش'
    )
    tracking_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='کد پیگیری'
    )
    
    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name='کاربر'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='سفارش'
    )
    gateway = models.ForeignKey(
        PaymentGateway,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name='درگاه'
    )
    
    # Transaction details
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        default=TransactionType.ORDER_PAYMENT,
        verbose_name='نوع تراکنش'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='وضعیت'
    )
    
    # Amounts
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(1000)],
        verbose_name='مبلغ (تومان)'
    )
    amount_rial = models.PositiveIntegerField(
        verbose_name='مبلغ (ریال)',
        help_text='مبلغ به ریال برای ارسال به درگاه'
    )
    
    # Gateway response data
    authority = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name='کد Authority',
        help_text='کد دریافتی از درگاه برای هدایت کاربر'
    )
    reference_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name='شماره مرجع',
        help_text='شماره پیگیری بانکی پس از پرداخت موفق'
    )
    
    # Gateway raw responses (for debugging)
    gateway_request = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='درخواست به درگاه'
    )
    gateway_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='پاسخ درگاه'
    )
    verify_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='پاسخ تایید'
    )
    
    # Card info (masked)
    card_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='شماره کارت',
        help_text='به صورت ماسک شده: 6037-****-****-1234'
    )
    card_hash = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='هش کارت'
    )
    
    # Metadata
    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='توضیحات'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='آدرس IP'
    )
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    
    # Error handling
    error_code = models.CharField(max_length=20, blank=True, verbose_name='کد خطا')
    error_message = models.TextField(blank=True, verbose_name='پیام خطا')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پرداخت')
    expires_at = models.DateTimeField(verbose_name='تاریخ انقضا')
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تایید')
    
    class Meta:
        verbose_name = 'تراکنش'
        verbose_name_plural = 'تراکنش‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['gateway', 'status']),
        ]
    
    def __str__(self):
        return f'{self.tracking_code} - {self.get_status_display()}'
    
    def save(self, *args, **kwargs):
        # Generate tracking code
        if not self.tracking_code:
            self.tracking_code = self._generate_tracking_code()
        
        # Convert Toman to Rial
        if not self.amount_rial:
            self.amount_rial = self.amount * 10
        
        # Set expiry (15 minutes from creation)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=15)
        
        super().save(*args, **kwargs)
    
    def _generate_tracking_code(self):
        """Generate unique tracking code: TXN-XXXXXXXX"""
        while True:
            code = f'TXN-{secrets.token_hex(4).upper()}'
            if not Transaction.objects.filter(tracking_code=code).exists():
                return code
    
    @property
    def is_expired(self):
        """Check if transaction has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_successful(self):
        """Check if transaction was successful."""
        return self.status == self.Status.SUCCESS
    
    @property
    def can_verify(self):
        """Check if transaction can be verified."""
        return (
            self.status == self.Status.PENDING and
            not self.is_expired and
            self.authority
        )
    
    def mark_success(self, reference_id, card_number='', card_hash=''):
        """Mark transaction as successful."""
        self.status = self.Status.SUCCESS
        self.reference_id = reference_id
        self.card_number = card_number
        self.card_hash = card_hash
        self.paid_at = timezone.now()
        self.verified_at = timezone.now()
        self.save()
        
        # Update gateway stats
        self.gateway.increment_stats(self.amount, is_successful=True)
        
        # Process order payment if applicable
        if self.order:
            self._process_order_payment()
        
        # Process wallet topup if applicable
        if self.transaction_type == self.TransactionType.WALLET_TOPUP:
            self._process_wallet_topup()
    
    def mark_failed(self, error_code='', error_message=''):
        """Mark transaction as failed."""
        self.status = self.Status.FAILED
        self.error_code = error_code
        self.error_message = error_message
        self.save()
        
        # Update gateway stats
        self.gateway.increment_stats(self.amount, is_successful=False)
    
    def mark_cancelled(self):
        """Mark transaction as cancelled by user."""
        self.status = self.Status.CANCELLED
        self.save()
    
    def mark_expired(self):
        """Mark transaction as expired."""
        if self.status == self.Status.PENDING:
            self.status = self.Status.EXPIRED
            self.save()
    
    def _process_order_payment(self):
        """Process order after successful payment."""
        if not self.order:
            return
        
        with transaction.atomic():
            # Mark order as paid
            self.order.mark_paid()
            
            # Capture inventory
            self.order.capture_inventory()
            
            # Bind digital delivery data
            for item in self.order.items.filter(
                product__product_type='virtual'
            ):
                item.bind_inventory()
    
    def _process_wallet_topup(self):
        """Process wallet topup after successful payment."""
        from apps.wallet.models import Wallet, WalletTransaction
        
        with transaction.atomic():
            wallet, _ = Wallet.objects.get_or_create(user=self.user)
            wallet.deposit(
                amount=self.amount,
                transaction_type=WalletTransaction.TransactionType.TOPUP,
                reference=f'تراکنش {self.tracking_code}',
                payment_transaction=self
            )
    
    def get_gateway_url(self):
        """Return redirect URL for user based on selected gateway."""
        
        # ------------------------------
        # ZARINPAL
        # ------------------------------
        if self.gateway.gateway_type == PaymentGateway.GatewayType.ZARINPAL:
            base = (
                'https://sandbox.zarinpal.com/pg/StartPay/'
                if self.gateway.is_sandbox
                else 'https://www.zarinpal.com/pg/StartPay/'
            )
            return f'{base}{self.authority}'
        
        # ------------------------------
        # IDPAY
        # ------------------------------
        elif self.gateway.gateway_type == PaymentGateway.GatewayType.IDPAY:
            base = (
                'https://sandbox.idpay.ir/p/ws/'
                if self.gateway.is_sandbox
                else 'https://idpay.ir/p/ws/'
            )
            return f'{base}{self.authority}'
        
        # ------------------------------
        # Unknown gateway fallback
        # ------------------------------
        return None
