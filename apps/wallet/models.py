# apps/wallet/models.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid


class Wallet(models.Model):
    """
    کیف پول کاربر
    هر کاربر فقط یک کیف پول دارد
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name='کاربر'
    )
    
    # موجودی اصلی (قابل برداشت)
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='موجودی (تومان)'
    )
    
    # اعتبار هدیه (غیرقابل برداشت، فقط خرید)
    gift_balance = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='اعتبار هدیه (تومان)'
    )
    
    # مجموع شارژ شده
    total_deposited = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        default=Decimal('0'),
        verbose_name='مجموع شارژ'
    )
    
    # مجموع خرج شده
    total_spent = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        default=Decimal('0'),
        verbose_name='مجموع خرج شده'
    )
    
    # قفل کیف پول
    is_locked = models.BooleanField(
        default=False,
        verbose_name='قفل شده'
    )
    lock_reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='دلیل قفل'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'کیف پول'
        verbose_name_plural = 'کیف پول‌ها'
        
    def __str__(self):
        return f"کیف پول {self.user} - {self.total_balance:,} تومان"
    
    @property
    def total_balance(self):
        """موجودی کل (اصلی + هدیه)"""
        return self.balance + self.gift_balance
    
    def can_afford(self, amount):
        """آیا موجودی کافی برای خرید دارد؟"""
        return self.total_balance >= Decimal(str(amount))
    
    def get_payable_amount(self, amount):
        """
        محاسبه مقداری که از کیف پول قابل پرداخت است
        اول از اعتبار هدیه، بعد از موجودی اصلی
        """
        amount = Decimal(str(amount))
        return min(self.total_balance, amount)
    
    def get_remaining_amount(self, amount):
        """مبلغی که باید از درگاه پرداخت شود"""
        amount = Decimal(str(amount))
        payable = self.get_payable_amount(amount)
        return amount - payable


class WalletTransaction(models.Model):
    transaction_id = models.CharField(
    max_length=20,
    unique=True,
    blank=True,
    verbose_name='شناسه تراکنش'
)
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            import random
            self.transaction_id = f"TXN-{random.randint(100000, 999999)}"
        super().save(*args, **kwargs)

    
    class TransactionType(models.TextChoices):
        DEPOSIT = 'deposit', 'شارژ'
        WITHDRAW = 'withdraw', 'برداشت'
        PURCHASE = 'purchase', 'خرید'
        REFUND = 'refund', 'استرداد'
        GIFT = 'gift', 'هدیه'
        CASHBACK = 'cashback', 'کش‌بک'
        ADMIN_ADJUST = 'admin_adjust', 'تنظیم ادمین'
        TRANSFER_IN = 'transfer_in', 'انتقال دریافتی'
        TRANSFER_OUT = 'transfer_out', 'انتقال ارسالی'
    
    class TransactionStatus(models.TextChoices):
        PENDING = 'pending', 'در انتظار'
        COMPLETED = 'completed', 'تکمیل شده'
        FAILED = 'failed', 'ناموفق'
        CANCELLED = 'cancelled', 'لغو شده'
        REVERSED = 'reversed', 'برگشت خورده'
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='کیف پول'
    )
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        verbose_name='نوع تراکنش'
    )
    
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        verbose_name='وضعیت'
    )
    
    # مبلغ (مثبت برای واریز، منفی برای برداشت)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='مبلغ (تومان)'
    )
    
    # آیا از اعتبار هدیه استفاده شده؟
    is_gift_credit = models.BooleanField(
        default=False,
        verbose_name='اعتبار هدیه'
    )
    
    # موجودی قبل و بعد
    balance_before = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='موجودی قبل'
    )
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='موجودی بعد'
    )
    
    # ارتباط با سفارش (اختیاری)
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions',
        verbose_name='سفارش'
    )
    
    # ارتباط با تراکنش پرداخت (اختیاری)
    payment_transaction = models.ForeignKey(
        'payments.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions',
        verbose_name='تراکنش پرداخت'
    )
    
    # توضیحات
    description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='توضیحات'
    )
    
    # متادیتا (JSON)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='اطلاعات اضافی'
    )
    
    # ادمین انجام‌دهنده (برای تنظیمات دستی)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performed_wallet_transactions',
        verbose_name='انجام‌دهنده'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'تراکنش کیف پول'
        verbose_name_plural = 'تراکنش‌های کیف پول'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', '-created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['status']),
        ]
        
    def __str__(self):
        sign = '+' if self.amount > 0 else ''
        return f"{self.wallet.user} | {sign}{self.amount:,} | {self.get_transaction_type_display()}"
    
    @property
    def is_credit(self):
        """آیا تراکنش واریزی است؟"""
        return self.amount > 0
    
    @property
    def is_debit(self):
        """آیا تراکنش برداشتی است؟"""
        return self.amount < 0


class WalletDepositRequest(models.Model):
    """
    درخواست شارژ کیف پول
    """
    authority = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='کد Authority زرین‌پال'
    )
    ref_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='کد پیگیری'
    )

    gateway = models.CharField(
        max_length=20,
        default='zarinpal',
        verbose_name='درگاه پرداخت'
    )
    
    class DepositStatus(models.TextChoices):
        PENDING = 'pending', 'در انتظار پرداخت'
        PAID = 'paid', 'پرداخت شده'
        FAILED = 'failed', 'ناموفق'
        EXPIRED = 'expired', 'منقضی'
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='deposit_requests',
        verbose_name='کیف پول'
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('10000'))],  # حداقل 10,000 تومان
        verbose_name='مبلغ (تومان)'
    )
    
    status = models.CharField(
        max_length=20,
        choices=DepositStatus.choices,
        default=DepositStatus.PENDING,
        verbose_name='وضعیت'
    )
    
    # ارتباط با تراکنش پرداخت
    payment_transaction = models.OneToOneField(
        'payments.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_deposit',
        verbose_name='تراکنش پرداخت'
    )
    
    # تراکنش کیف پول ایجاد شده
    wallet_transaction = models.OneToOneField(
        WalletTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deposit_request',
        verbose_name='تراکنش کیف پول'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(verbose_name='تاریخ انقضا')

    class Meta:
        verbose_name = 'درخواست شارژ'
        verbose_name_plural = 'درخواست‌های شارژ'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"شارژ {self.amount:,} - {self.wallet.user}"
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at and self.status == self.DepositStatus.PENDING
