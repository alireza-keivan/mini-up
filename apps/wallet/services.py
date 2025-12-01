# apps/wallet/services.py

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.conf import settings

from .models import Wallet, WalletTransaction, WalletDepositRequest


class WalletService:
    """
    سرویس مدیریت کیف پول
    
    این سرویس تمام عملیات مربوط به کیف پول را مدیریت می‌کند:
    - شارژ کیف پول
    - برداشت از کیف پول
    - پرداخت ترکیبی (کیف پول + درگاه)
    - اعتبار هدیه
    - استرداد وجه
    - انتقال بین کاربران
    """
    
    # تنظیمات از settings یا مقادیر پیش‌فرض
    MIN_DEPOSIT = Decimal(getattr(settings, 'MIN_WALLET_TOPUP', 10000))
    MAX_DEPOSIT = Decimal(getattr(settings, 'MAX_WALLET_TOPUP', 50000000))
    
    # ─────────────────────────────────────────────────────────────────────────
    # WALLET MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────────
    
    @staticmethod
    def get_or_create_wallet(user):
        """
        دریافت یا ایجاد کیف پول برای کاربر
        
        Args:
            user: کاربر
            
        Returns:
            Wallet: کیف پول کاربر
        """
        wallet, created = Wallet.objects.get_or_create(user=user)
        return wallet
    
    @staticmethod
    def get_wallet(user):
        """
        دریافت کیف پول کاربر (بدون ایجاد)
        
        Args:
            user: کاربر
            
        Returns:
            Wallet or None
        """
        try:
            return user.wallet
        except Wallet.DoesNotExist:
            return None
    
    @staticmethod
    def check_wallet_locked(wallet):
        """
        بررسی قفل بودن کیف پول
        
        Args:
            wallet: کیف پول
            
        Raises:
            ValidationError: اگر کیف پول قفل باشد
        """
        if wallet.is_locked:
            raise ValidationError(
                f"کیف پول قفل شده است. دلیل: {wallet.lock_reason or 'نامشخص'}"
            )
    
    @staticmethod
    def lock_wallet(wallet, reason, performed_by=None):
        """
        قفل کردن کیف پول
        
        Args:
            wallet: کیف پول
            reason: دلیل قفل
            performed_by: ادمین انجام‌دهنده
        """
        wallet.is_locked = True
        wallet.lock_reason = reason
        wallet.save(update_fields=['is_locked', 'lock_reason', 'updated_at'])
        
        # ثبت در تراکنش‌ها
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=WalletTransaction.TransactionType.ADMIN_ADJUST,
            status=WalletTransaction.TransactionStatus.COMPLETED,
            amount=Decimal('0'),
            balance_before=wallet.total_balance,
            balance_after=wallet.total_balance,
            description=f"قفل کیف پول: {reason}",
            performed_by=performed_by
        )
    
    @staticmethod
    def unlock_wallet(wallet, performed_by=None):
        """
        باز کردن قفل کیف پول
        
        Args:
            wallet: کیف پول
            performed_by: ادمین انجام‌دهنده
        """
        old_reason = wallet.lock_reason
        wallet.is_locked = False
        wallet.lock_reason = ''
        wallet.save(update_fields=['is_locked', 'lock_reason', 'updated_at'])
        
        # ثبت در تراکنش‌ها
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=WalletTransaction.TransactionType.ADMIN_ADJUST,
            status=WalletTransaction.TransactionStatus.COMPLETED,
            amount=Decimal('0'),
            balance_before=wallet.total_balance,
            balance_after=wallet.total_balance,
            description=f"رفع قفل کیف پول (دلیل قبلی: {old_reason})",
            performed_by=performed_by
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # DEPOSIT (شارژ کیف پول)
    # ─────────────────────────────────────────────────────────────────────────
    
    @classmethod
    @transaction.atomic
    def deposit(cls, wallet, amount, description='', payment_transaction=None,
                is_gift=False, performed_by=None, metadata=None):
        """
        شارژ کیف پول
        
        Args:
            wallet: کیف پول
            amount: مبلغ (تومان) - باید مثبت باشد
            description: توضیحات
            payment_transaction: تراکنش پرداخت مرتبط (اختیاری)
            is_gift: آیا اعتبار هدیه است؟
            performed_by: ادمین انجام‌دهنده (اختیاری)
            metadata: اطلاعات اضافی (dict)
            
        Returns:
            WalletTransaction: تراکنش ایجاد شده
            
        Raises:
            ValidationError: در صورت خطا
        """
        cls.check_wallet_locked(wallet)
        
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValidationError("مبلغ شارژ باید مثبت باشد")
        
        # قفل کردن رکورد برای جلوگیری از race condition
        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
        
        # تعیین نوع تراکنش و فیلد مقصد
        if is_gift:
            balance_before = wallet.gift_balance
            wallet.gift_balance += amount
            balance_after = wallet.gift_balance
            trans_type = WalletTransaction.TransactionType.GIFT
        else:
            balance_before = wallet.balance
            wallet.balance += amount
            balance_after = wallet.balance
            wallet.total_deposited += amount
            trans_type = WalletTransaction.TransactionType.DEPOSIT
        
        wallet.save()
        
        # ایجاد تراکنش
        wallet_transaction = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=trans_type,
            status=WalletTransaction.TransactionStatus.COMPLETED,
            amount=amount,  # مثبت برای واریز
            is_gift_credit=is_gift,
            balance_before=balance_before,
            balance_after=balance_after,
            payment_transaction=payment_transaction,
            description=description or ('اعتبار هدیه' if is_gift else 'شارژ کیف پول'),
            performed_by=performed_by,
            metadata=metadata or {}
        )
        
        return wallet_transaction
    
    @classmethod
    @transaction.atomic
    def add_gift_credit(cls, wallet, amount, description='', performed_by=None, 
                        expiry_days=None, metadata=None):
        """
        اضافه کردن اعتبار هدیه به کیف پول
        
        Args:
            wallet: کیف پول
            amount: مبلغ (تومان)
            description: توضیحات
            performed_by: ادمین انجام‌دهنده
            expiry_days: روزهای اعتبار (اختیاری)
            metadata: اطلاعات اضافی
            
        Returns:
            WalletTransaction
        """
        meta = metadata or {}
        if expiry_days:
            meta['expires_at'] = (timezone.now() + timedelta(days=expiry_days)).isoformat()
        
        return cls.deposit(
            wallet=wallet,
            amount=amount,
            description=description or 'اعتبار هدیه',
            is_gift=True,
            performed_by=performed_by,
            metadata=meta
        )
    
    @classmethod
    @transaction.atomic
    def add_cashback(cls, wallet, amount, order=None, description='', metadata=None):
        """
        اضافه کردن کش‌بک به کیف پول
        
        Args:
            wallet: کیف پول
            amount: مبلغ کش‌بک (تومان)
            order: سفارش مرتبط (اختیاری)
            description: توضیحات
            metadata: اطلاعات اضافی
            
        Returns:
            WalletTransaction
        """
        cls.check_wallet_locked(wallet)
        
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValidationError("مبلغ کش‌بک باید مثبت باشد")
        
        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
        
        balance_before = wallet.balance
        wallet.balance += amount
        wallet.save()
        
        wallet_transaction = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=WalletTransaction.TransactionType.CASHBACK,
            status=WalletTransaction.TransactionStatus.COMPLETED,
            amount=amount,
            is_gift_credit=False,
            balance_before=balance_before,
            balance_after=wallet.balance,
            order=order,
            description=description or 'کش‌بک خرید',
            metadata=metadata or {}
        )
        
        return wallet_transaction
    
    # ─────────────────────────────────────────────────────────────────────────
    # WITHDRAW (برداشت از کیف پول)
    # ─────────────────────────────────────────────────────────────────────────
    
    @classmethod
    @transaction.atomic
    def withdraw(cls, wallet, amount, description='', order=None, 
                 performed_by=None, metadata=None):
        """
        برداشت از کیف پول
        
        ترتیب کسر:
        1. اول از اعتبار هدیه
        2. سپس از موجودی اصلی
        
        Args:
            wallet: کیف پول
            amount: مبلغ برداشت (تومان) - باید مثبت باشد
            description: توضیحات
            order: سفارش مرتبط (اختیاری)
            performed_by: ادمین انجام‌دهنده (اختیاری)
            metadata: اطلاعات اضافی
            
        Returns:
            WalletTransaction: تراکنش ایجاد شده
            
        Raises:
            ValidationError: در صورت موجودی ناکافی یا خطا
        """
        cls.check_wallet_locked(wallet)
        
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValidationError("مبلغ برداشت باید مثبت باشد")
        
        # قفل کردن رکورد
        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
        
        # بررسی موجودی
        if wallet.total_balance < amount:
            raise ValidationError(
                f"موجودی کیف پول کافی نیست. "
                f"موجودی: {wallet.total_balance:,} تومان، "
                f"مبلغ درخواستی: {amount:,} تومان"
            )
        
        balance_before = wallet.total_balance
        remaining = amount
        used_gift = Decimal('0')
        used_balance = Decimal('0')
        
        # 1. کم کردن از اعتبار هدیه
        if wallet.gift_balance > 0 and remaining > 0:
            use_from_gift = min(wallet.gift_balance, remaining)
            wallet.gift_balance -= use_from_gift
            used_gift = use_from_gift
            remaining -= use_from_gift
        
        # 2. کم کردن باقی‌مانده از موجودی اصلی
        if remaining > 0:
            wallet.balance -= remaining
            used_balance = remaining
        
        # بروزرسانی آمار
        wallet.total_spent += amount
        wallet.save()
        
        # ایجاد تراکنش
        wallet_transaction = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=WalletTransaction.TransactionType.PURCHASE,
            status=WalletTransaction.TransactionStatus.COMPLETED,
            amount=-amount,  # منفی برای برداشت
            is_gift_credit=(used_gift > 0),
            balance_before=balance_before,
            balance_after=wallet.total_balance,
            order=order,
            description=description or 'برداشت از کیف پول',
            performed_by=performed_by,
            metadata={
                'used_gift': int(used_gift),
                'used_balance': int(used_balance),
                **(metadata or {})
            }
        )
        
        return wallet_transaction
    
    # ─────────────────────────────────────────────────────────────────────────
    # REFUND (استرداد به کیف پول)
    # ─────────────────────────────────────────────────────────────────────────
    
    @classmethod
    @transaction.atomic
    def refund(cls, wallet, amount, order=None, original_transaction=None,
            description='', performed_by=None, metadata=None):
        """
        استرداد وجه به کیف پول

        Args:
            wallet: کیف پول
            amount: مبلغ استرداد (تومان)
            order: سفارش مرتبط (اختیاری)
            original_transaction: تراکنش اصلی که برگشت می‌خورد (اختیاری)
            description: توضیحات
            performed_by: ادمین انجام‌دهنده
            metadata: اطلاعات اضافی

        Returns:
            WalletTransaction
        """
        cls.check_wallet_locked(wallet)

        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValidationError("مبلغ استرداد باید مثبت باشد")

        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

        balance_before = wallet.balance
        wallet.balance += amount

        if wallet.total_spent >= amount:
            wallet.total_spent -= amount

        wallet.save()

        # ✅ تورفتگی اصلاح شده
        wallet_transaction = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=WalletTransaction.TransactionType.REFUND,
            status=WalletTransaction.TransactionStatus.COMPLETED,
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            order=order,
            description=description or 'استرداد وجه',
            performed_by=performed_by,
            metadata={
                'original_transaction_id': str(original_transaction.id) if original_transaction else None,
                **(metadata or {})
            }
        )

        return wallet_transaction


    # ─────────────────────────────────────────────────────────────────────────
    # TRANSFER (انتقال بین دو کاربر)
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    @transaction.atomic
    def transfer(cls, sender_wallet, receiver_wallet, amount, description='', performed_by=None):
        """
        انتقال وجه بین دو کاربر
        
        Args:
            sender_wallet: کیف پول فرستنده
            receiver_wallet: کیف پول گیرنده
            amount: مبلغ انتقال
            description: توضیحات
            performed_by: ادمین (اختیاری)
        """
        if sender_wallet.pk == receiver_wallet.pk:
            raise ValidationError("انتقال به خود امکان‌پذیر نیست")

        # اول از فرستنده کم می‌کنیم
        withdrawal_tx = cls.withdraw(
            wallet=sender_wallet,
            amount=amount,
            description=description or 'انتقال وجه به کاربر دیگر',
            performed_by=performed_by
        )

        # سپس به گیرنده اضافه می‌کنیم
        deposit_tx = cls.deposit(
            wallet=receiver_wallet,
            amount=amount,
            description=description or 'دریافت انتقال از کاربر',
            performed_by=performed_by,
            metadata={'transfer_from': sender_wallet.user_id}
        )

        return {
            'withdraw_transaction': withdrawal_tx,
            'deposit_transaction': deposit_tx
        }

    # ─────────────────────────────────────────────────────────────────────────
    # COMBINED PAYMENT (پرداخت ترکیبی)
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    @transaction.atomic
    def combined_payment(cls, wallet, amount, order, description='پرداخت سفارش'):
        """
        پرداخت ترکیبی (کیف پول + درگاه)

        اگر موجودی کافی باشد → کامل از کیف پول
        اگر ناکافی باشد → بخشی از کیف، باقی از درگاه

        Returns:
            dict {from_wallet, from_gateway, need_gateway, wallet_transaction}
        """
        amount = Decimal(str(amount))
        cls.check_wallet_locked(wallet)

        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

        wallet_balance = wallet.total_balance
        from_wallet = min(wallet_balance, amount)
        from_gateway = amount - from_wallet
        need_gateway = from_gateway > 0

        wallet_tx = None
        if from_wallet > 0:
            wallet_tx = cls.withdraw(
                wallet=wallet,
                amount=from_wallet,
                order=order,
                description=description
            )

        return {
            'from_wallet': from_wallet,
            'from_gateway': from_gateway,
            'need_gateway': need_gateway,
            'wallet_transaction': wallet_tx
        }

    # ─────────────────────────────────────────────────────────────────────────
    # DEPOSIT REQUESTS (درخواست رسمـی شارژ — قبل از پرداخت)
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def create_deposit_request(cls, user, amount):
        """
        ساخت درخواست شارژ برای اتصال به درگاه پرداخت
        
        معمولاً قبل از redirect به زرین‌پال استفاده می‌شود.
        """
        amount = Decimal(str(amount))

        if amount < cls.MIN_DEPOSIT:
            raise ValidationError(f"حداقل مبلغ شارژ {cls.MIN_DEPOSIT:,} تومان است")

        if amount > cls.MAX_DEPOSIT:
            raise ValidationError(f"حداکثر مبلغ شارژ {cls.MAX_DEPOSIT:,} تومان است")

        wallet = cls.get_or_create_wallet(user)

        deposit_request = WalletDepositRequest.objects.create(
            user=user,
            wallet=wallet,
            amount=amount,
            status=WalletDepositRequest.Status.PENDING
        )

        return deposit_request

    @classmethod
    @transaction.atomic
    def complete_deposit_request(cls, deposit_request, payment_transaction):
        """
        تکمیل درخواست شارژ پس از تایید پرداخت درگاه
        """
        if deposit_request.status == WalletDepositRequest.Status.COMPLETED:
            return deposit_request

        wallet = deposit_request.wallet

        cls.deposit(
            wallet=wallet,
            amount=deposit_request.amount,
            payment_transaction=payment_transaction,
            description='شارژ کیف پول از طریق درگاه'
        )

        deposit_request.status = WalletDepositRequest.Status.COMPLETED
        deposit_request.payment_transaction = payment_transaction
        deposit_request.save(update_fields=['status', 'payment_transaction'])

        return deposit_request

    @classmethod
    @transaction.atomic
    def fail_deposit_request(cls, deposit_request):
        """
        ثبت وضعیت ناموفق بودن پرداخت
        """
        deposit_request.status = WalletDepositRequest.Status.FAILED
        deposit_request.save(update_fields=['status'])
        return deposit_request
