# apps/payments/serializers.py

"""
Payment Serializers Module
==========================
Comprehensive serializers for payment gateway operations,
transaction management, and API responses.
"""
from decimal import Decimal
from rest_framework import serializers
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import PaymentGateway, Transaction


# =============================================================================
# Gateway Serializers
# =============================================================================

class PaymentGatewaySerializer(serializers.ModelSerializer):
    """
    Full serializer for PaymentGateway model.
    Used in admin and detailed views.
    """
    
    gateway_type_display = serializers.CharField(
        source='get_gateway_type_display',
        read_only=True
    )
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentGateway
        fields = [
            'id',
            'name',
            'gateway_type',
            'gateway_type_display',
            'logo',
            'logo_url',
            'description',
            'is_active',
            'is_sandbox',
            'priority',
            'min_amount',
            'max_amount',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_logo_url(self, obj) -> str:
        """Get absolute URL for gateway logo."""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return ''


class PaymentGatewayListSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for listing available gateways.
    Used in checkout flow for gateway selection.
    """
    
    gateway_type_display = serializers.CharField(
        source='get_gateway_type_display',
        read_only=True
    )
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentGateway
        fields = [
            'id',
            'name',
            'gateway_type',
            'gateway_type_display',
            'logo_url',
            'description',
            'min_amount',
            'max_amount',
        ]
    
    def get_logo_url(self, obj) -> str:
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return ''


# =============================================================================
# Transaction Serializers
# =============================================================================

class TransactionSerializer(serializers.ModelSerializer):
    """
    Full serializer for Transaction model.
    Includes all details for transaction display.
    """
    
    # Display fields
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )
    
    # Related fields
    gateway_name = serializers.CharField(
        source='gateway.name',
        read_only=True,
        default=''
    )
    gateway_type = serializers.CharField(
        source='gateway.gateway_type',
        read_only=True,
        default=''
    )
    user_phone = serializers.CharField(
        source='user.phone',
        read_only=True,
        default=''
    )
    order_number = serializers.CharField(
        source='order.order_number',
        read_only=True,
        default=''
    )
    
    # Computed fields
    amount_display = serializers.SerializerMethodField()
    amount_rial = serializers.SerializerMethodField()
    is_successful = serializers.SerializerMethodField()
    is_pending = serializers.SerializerMethodField()
    is_refundable = serializers.SerializerMethodField()
    card_number_masked = serializers.SerializerMethodField()
    created_at_jalali = serializers.SerializerMethodField()
    paid_at_jalali = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            # Identifiers
            'id',
            'transaction_id',
            'authority',
            'reference_id',
            
            # Type & Status
            'transaction_type',
            'transaction_type_display',
            'status',
            'status_display',
            
            # Amounts
            'amount',
            'amount_display',
            'amount_rial',
            
            # Gateway info
            'gateway_name',
            'gateway_type',
            
            # User & Order
            'user_phone',
            'order_number',
            
            # Card info
            'card_number',
            'card_number_masked',
            
            # Timestamps
            'created_at',
            'created_at_jalali',
            'paid_at',
            'paid_at_jalali',
            'expired_at',
            
            # Computed
            'is_successful',
            'is_pending',
            'is_refundable',
            
            # Extra info
            'description',
            'error_code',
            'error_message',
            'ip_address',
        ]
        read_only_fields = fields
    
    def get_amount_display(self, obj) -> str:
        """Format amount with thousand separator."""
        return f"{obj.amount:,} تومان"
    
    def get_amount_rial(self, obj) -> int:
        """Return amount in Rial."""
        return obj.amount * 10
    
    def get_is_successful(self, obj) -> bool:
        """Check if transaction is successful."""
        return obj.status == 'completed'
    
    def get_is_pending(self, obj) -> bool:
        """Check if transaction is pending."""
        return obj.status == 'pending'
    
    def get_is_refundable(self, obj) -> bool:
        """
        Check if transaction can be refunded.
        Only completed transactions within 72 hours are refundable.
        """
        if obj.status != 'completed' or not obj.paid_at:
            return False
        hours_since_payment = (timezone.now() - obj.paid_at).total_seconds() / 3600
        return hours_since_payment <= 72
    
    def get_card_number_masked(self, obj) -> str:
        """Return masked card number for display."""
        if obj.card_number and len(obj.card_number) >= 10:
            return f"{obj.card_number[:6]}******{obj.card_number[-4:]}"
        return obj.card_number or ''
    
    def get_created_at_jalali(self, obj) -> str:
        """Return Jalali formatted creation date."""
        try:
            import jdatetime
            if obj.created_at:
                jdate = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
                return jdate.strftime('%Y/%m/%d %H:%M')
        except ImportError:
            pass
        return obj.created_at.strftime('%Y/%m/%d %H:%M') if obj.created_at else ''
    
    def get_paid_at_jalali(self, obj) -> str:
        """Return Jalali formatted payment date."""
        try:
            import jdatetime
            if obj.paid_at:
                jdate = jdatetime.datetime.fromgregorian(datetime=obj.paid_at)
                return jdate.strftime('%Y/%m/%d %H:%M')
        except ImportError:
            pass
        return obj.paid_at.strftime('%Y/%m/%d %H:%M') if obj.paid_at else ''


class TransactionListSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for transaction lists.
    Optimized for performance in list views.
    """
    
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )
    gateway_name = serializers.CharField(
        source='gateway.name',
        read_only=True,
        default=''
    )
    amount_display = serializers.SerializerMethodField()
    is_successful = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'transaction_id',
            'transaction_type',
            'transaction_type_display',
            'status',
            'status_display',
            'amount',
            'amount_display',
            'gateway_name',
            'reference_id',
            'is_successful',
            'created_at',
            'paid_at',
        ]
        read_only_fields = fields
    
    def get_amount_display(self, obj) -> str:
        return f"{obj.amount:,} تومان"
    
    def get_is_successful(self, obj) -> bool:
        return obj.status == 'completed'


class TransactionMinimalSerializer(serializers.ModelSerializer):
    """
    Ultra-minimal serializer for embedding in other responses.
    """
    
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = Transaction
        fields = [
            'transaction_id',
            'status',
            'status_display',
            'amount',
            'reference_id',
            'paid_at',
        ]
        read_only_fields = fields


# =============================================================================
# Input Serializers (Request Validation)
# =============================================================================

class PaymentInitiateSerializer(serializers.Serializer):
    """
    Serializer for initiating a new payment.
    Validates input data before creating transaction.
    """
    
    amount = serializers.IntegerField(
        min_value=1000,
        max_value=500000000,
        help_text=_('مبلغ به تومان (حداقل ۱,۰۰۰ - حداکثر ۵۰۰,۰۰۰,۰۰۰)')
    )
    transaction_type = serializers.ChoiceField(
        choices=[
            ('order', 'پرداخت سفارش'),
            ('wallet', 'شارژ کیف پول'),
            ('subscription', 'خرید اشتراک'),
        ],
        default='order',
        help_text=_('نوع تراکنش')
    )
    order_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text=_('شناسه سفارش (در صورت پرداخت سفارش)')
    )
    gateway_type = serializers.ChoiceField(
        choices=[
            ('zarinpal', 'زرین‌پال'),
            ('idpay', 'آیدی‌پی'),
        ],
        required=False,
        allow_null=True,
        help_text=_('نوع درگاه (اختیاری - در صورت عدم انتخاب، درگاه پیش‌فرض)')
    )
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        default='',
        help_text=_('توضیحات پرداخت')
    )
    callback_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text=_('آدرس بازگشت سفارشی (اختیاری)')
    )
    
    def validate_amount(self, value):
        """Validate payment amount."""
        if value < 1000:
            raise serializers.ValidationError(
                _('حداقل مبلغ پرداخت ۱,۰۰۰ تومان است')
            )
        if value > 500000000:
            raise serializers.ValidationError(
                _('حداکثر مبلغ پرداخت ۵۰۰ میلیون تومان است')
            )
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        transaction_type = attrs.get('transaction_type')
        order_id = attrs.get('order_id')
        
        # Order payment requires order_id
        if transaction_type == 'order' and not order_id:
            raise serializers.ValidationError({
                'order_id': _('برای پرداخت سفارش، شناسه سفارش الزامی است')
            })
        
        return attrs


class PaymentVerifySerializer(serializers.Serializer):
    """
    Serializer for payment verification callback.
    Handles data from gateway callback.
    """
    
    transaction_id = serializers.UUIDField(
        required=True,
        help_text=_('شناسه تراکنش')
    )
    
    # ZarinPal callback params
    Authority = serializers.CharField(
        required=False,
        allow_blank=True
    )
    Status = serializers.CharField(
        required=False,
        allow_blank=True
    )
    
    # IDPay callback params
    id = serializers.CharField(
        required=False,
        allow_blank=True
    )
    order_id = serializers.CharField(
        required=False,
        allow_blank=True
    )
    status = serializers.IntegerField(
        required=False,
        allow_null=True
    )
    track_id = serializers.CharField(
        required=False,
        allow_blank=True
    )
    payment_card_no = serializers.CharField(
        required=False,
        allow_blank=True
    )


class WalletDepositSerializer(serializers.Serializer):
    """
    Serializer for wallet deposit (top-up) request.
    """
    
    amount = serializers.IntegerField(
        min_value=10000,
        max_value=50000000,
        help_text=_('مبلغ شارژ به تومان (حداقل ۱۰,۰۰۰ - حداکثر ۵۰,۰۰۰,۰۰۰)')
    )
    gateway_type = serializers.ChoiceField(
        choices=[
            ('zarinpal', 'زرین‌پال'),
            ('idpay', 'آیدی‌پی'),
        ],
        required=False,
        allow_null=True,
        help_text=_('نوع درگاه (اختیاری)')
    )
    
    def validate_amount(self, value):
        """Validate deposit amount."""
        if value < 10000:
            raise serializers.ValidationError(
                _('حداقل مبلغ شارژ ۱۰,۰۰۰ تومان است')
            )
        if value > 50000000:
            raise serializers.ValidationError(
                _('حداکثر مبلغ شارژ ۵۰ میلیون تومان است')
            )
        return value


class RefundRequestSerializer(serializers.Serializer):
    """
    Serializer for refund requests.
    Used when user or admin requests partial/full refund
    for a completed payment transaction.
    """

    transaction_id = serializers.UUIDField(
        required=True,
        help_text=_('شناسه تراکنش برای استرداد')
    )

    # Optional partial refund amount
    amount = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1000,
        help_text=_(
            'مبلغ استرداد به تومان. اگر ارسال نشود، تمام مبلغ تراکنش بازگردانده می‌شود.'
        )
    )

    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text=_('دلیل استرداد (اختیاری)')
    )

    def validate(self, attrs):
        """
        Cross-field validation:
        - transaction must exist and be completed
        - refund must be within refund window
        - amount must not exceed original transaction amount
        """
        from apps.payments.models import Transaction

        transaction_id = attrs.get('transaction_id')
        amount = attrs.get('amount')

        # Retrieve transaction
        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
        except Transaction.DoesNotExist:
            raise serializers.ValidationError({
                'transaction_id': _('تراکنش یافت نشد')
            })

        # Must be completed
        if transaction.status != Transaction.Status.COMPLETED:
            raise serializers.ValidationError(
                _('این تراکنش در وضعیت قابل استرداد نیست')
            )

        # Time validation: 72 hours limit
        if transaction.paid_at:
            hours_passed = (
                timezone.now() - transaction.paid_at
            ).total_seconds() / 3600

            if hours_passed > 72:
                raise serializers.ValidationError(
                    _('مهلت استرداد تراکنش به پایان رسیده است (بیش از ۷۲ ساعت)')
                )

        # Validate refund amount
        if amount is not None:
            if amount > transaction.amount:
                raise serializers.ValidationError({
                    'amount': _('مبلغ استرداد نمی‌تواند بیشتر از مبلغ تراکنش باشد')
                })
        else:
            # If not provided → full refund
            attrs['amount'] = transaction.amount

        attrs['transaction'] = transaction
        return attrs
