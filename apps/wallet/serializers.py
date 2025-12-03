# apps/wallet/serializers.py

from rest_framework import serializers
from decimal import Decimal
from .models import Wallet, WalletTransaction, WalletDepositRequest
from .services import WalletService


class WalletSerializer(serializers.ModelSerializer):
    """سریالایزر کیف پول"""

    total_balance = serializers.DecimalField(
        max_digits=12, decimal_places=0, read_only=True
    )
    user_phone = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = Wallet
        fields = [
            'id',
            'user_phone',
            'balance',
            'gift_balance',
            'total_balance',
            'total_deposited',
            'total_spent',
            'is_locked',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields


class WalletTransactionSerializer(serializers.ModelSerializer):
    """سریالایزر تراکنش کیف پول"""

    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = WalletTransaction
        fields = [
            'id',  # UUID است - کافی برای شناسایی
            # 'transaction_id',  ← حذف شد (در مدل وجود ندارد)
            'transaction_type',
            'transaction_type_display',
            'status',
            'status_display',
            'amount',
            'is_gift_credit',
            'balance_before',
            'balance_after',
            'description',
            'created_at'
        ]
        read_only_fields = fields


class WalletDepositRequestSerializer(serializers.ModelSerializer):
    """سریالایزر درخواست شارژ"""

    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = WalletDepositRequest
        fields = [
            'id',  # UUID است - کافی برای شناسایی
            # 'request_id',  ← حذف شد (در مدل وجود ندارد)
            'amount',
            'status',
            'status_display',
            'created_at'
        ]
        read_only_fields = fields


class DepositRequestCreateSerializer(serializers.Serializer):
    """سریالایزر ایجاد درخواست شارژ"""

    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        min_value=Decimal('10000'),
        max_value=Decimal('50000000')
    )
    gateway = serializers.CharField(max_length=20, required=False, default='zarinpal')

    def validate_amount(self, value):
        if value < WalletService.MIN_DEPOSIT:
            raise serializers.ValidationError(
                f"حداقل مبلغ شارژ {WalletService.MIN_DEPOSIT:,} تومان است"
            )
        if value > WalletService.MAX_DEPOSIT:
            raise serializers.ValidationError(
                f"حداکثر مبلغ شارژ {WalletService.MAX_DEPOSIT:,} تومان است"
            )
        return value


class TransferSerializer(serializers.Serializer):
    """سریالایزر انتقال وجه"""

    receiver_phone = serializers.CharField(max_length=11)
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        min_value=Decimal('1000')
    )
    description = serializers.CharField(max_length=255, required=False, default='')

    def validate_receiver_phone(self, value):
        from apps.accounts.models import User

        if not value.startswith('09') or len(value) != 11:
            raise serializers.ValidationError("شماره موبایل نامعتبر است")

        try:
            User.objects.get(phone=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("کاربری با این شماره یافت نشد")

        return value

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user.phone == attrs['receiver_phone']:
            raise serializers.ValidationError({
                'receiver_phone': 'انتقال به حساب خودتان امکان‌پذیر نیست'
            })
        return attrs


class WithdrawSerializer(serializers.Serializer):
    """سریالایزر درخواست برداشت"""

    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        min_value=Decimal('50000')
    )
    iban = serializers.CharField(max_length=26)
    card_number = serializers.CharField(max_length=16, required=False, default='')

    def validate_iban(self, value):
        # حذف فاصله‌ها و نرمال‌سازی
        value = value.replace(' ', '').upper()

        if not value.startswith('IR'):
            value = 'IR' + value

        if len(value) != 26:
            raise serializers.ValidationError(
                "شماره شبا باید ۲۴ رقم باشد (بدون IR)"
            )

        return value

    def validate_card_number(self, value):
        if value:
            value = value.replace(' ', '').replace('-', '')
            if len(value) != 16 or not value.isdigit():
                raise serializers.ValidationError("شماره کارت نامعتبر است")
        return value


class WalletBalanceSerializer(serializers.Serializer):
    """سریالایزر ساده موجودی"""

    balance = serializers.DecimalField(max_digits=12, decimal_places=0)
    gift_balance = serializers.DecimalField(max_digits=12, decimal_places=0)
    total_balance = serializers.DecimalField(max_digits=12, decimal_places=0)
    is_locked = serializers.BooleanField()


class PaymentCheckSerializer(serializers.Serializer):
    """سریالایزر بررسی امکان پرداخت"""

    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        min_value=Decimal('1000')
    )


class GiftCodeRedeemSerializer(serializers.Serializer):
    """سریالایزر کد هدیه"""

    code = serializers.CharField(max_length=20, min_length=4)

    def validate_code(self, value):
        return value.strip().upper()
