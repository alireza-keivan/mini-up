# apps/orders/serializers.py

from rest_framework import serializers
from decimal import Decimal
from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory


# ═══════════════════════════════════════════════════════════════════════════════
# CART SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class CartItemProductSerializer(serializers.Serializer):
    """سریالایزر محصول داخل آیتم سبد"""
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    image = serializers.SerializerMethodField()
    product_type = serializers.CharField()

    def get_image(self, obj):
        if obj.primary_image:
            return obj.primary_image.url
        return None


class CartItemVariantSerializer(serializers.Serializer):
    """سریالایزر واریانت داخل آیتم سبد"""
    id = serializers.UUIDField()
    name = serializers.CharField()
    price = serializers.IntegerField()
    original_price = serializers.IntegerField(allow_null=True)


class CartItemSerializer(serializers.ModelSerializer):
    """سریالایزر آیتم سبد خرید"""
    product = CartItemProductSerializer(read_only=True)
    variant = CartItemVariantSerializer(read_only=True, allow_null=True)
    unit_price = serializers.SerializerMethodField()
    original_price = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'variant',
            'quantity', 'game_user_id', 'currency_amount',
            'unit_price', 'original_price', 'line_total', 'discount_amount',
            'is_available', 'created_at'
        ]

    def get_unit_price(self, obj):
        return int(obj.unit_price)

    def get_original_price(self, obj):
        return int(obj.original_price)

    def get_line_total(self, obj):
        return int(obj.line_total)

    def get_discount_amount(self, obj):
        return int(obj.discount_amount)

    def get_is_available(self, obj):
        return obj.is_available()


class CartSerializer(serializers.ModelSerializer):
    """سریالایزر سبد خرید"""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    subtotal = serializers.SerializerMethodField()
    total_discount = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id', 'items', 'total_items',
            'subtotal', 'total_discount', 'total',
            'created_at', 'updated_at'
        ]

    def get_subtotal(self, obj):
        return int(obj.subtotal)

    def get_total_discount(self, obj):
        return int(obj.total_discount)

    def get_total(self, obj):
        return int(obj.total)


class AddToCartSerializer(serializers.Serializer):
    """سریالایزر افزودن به سبد"""
    product_id = serializers.UUIDField()
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1)
    game_user_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    currency_amount = serializers.IntegerField(required=False, allow_null=True, min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    """سریالایزر بروزرسانی آیتم سبد"""
    quantity = serializers.IntegerField(min_value=1)


# ═══════════════════════════════════════════════════════════════════════════════
# ORDER SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class OrderItemProductSerializer(serializers.Serializer):
    """سریالایزر محصول داخل آیتم سفارش"""
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        if obj.primary_image:
            return obj.primary_image.url
        return None


class OrderItemSerializer(serializers.ModelSerializer):
    """سریالایزر آیتم سفارش"""
    product = OrderItemProductSerializer(read_only=True)
    variant_name = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'variant_name',
            'quantity', 'unit_price', 'original_price',
            'total_price', 'discount_amount',
            'currency_amount', 'game_user_id',
            'delivery_data', 'created_at'
        ]

    def get_variant_name(self, obj):
        return obj.variant.name if obj.variant else None


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """سریالایزر تاریخچه وضعیت"""
    old_status_display = serializers.SerializerMethodField()
    new_status_display = serializers.SerializerMethodField()

    class Meta:
        model = OrderStatusHistory
        fields = [
            'id', 'old_status', 'old_status_display',
            'new_status', 'new_status_display',
            'changed_at', 'note'
        ]

    def get_old_status_display(self, obj):
        return dict(Order.Status.choices).get(obj.old_status, obj.old_status)

    def get_new_status_display(self, obj):
        return dict(Order.Status.choices).get(obj.new_status, obj.new_status)


class OrderListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست سفارشات"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'tracking_code',
            'status', 'status_display',
            'total', 'amount_payable',
            'items_count', 'created_at', 'paid_at'
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """سریالایزر جزئیات سفارش"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    is_paid = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    is_cancelled = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'tracking_code',
            'status', 'status_display',
            'payment_method', 'payment_method_display',
            'subtotal', 'discount_amount', 'coupon_discount',
            'shipping_cost', 'wallet_used',
            'total', 'amount_payable',
            'shipping_data', 'customer_note',
            'is_paid', 'is_completed', 'is_cancelled',
            'items', 'status_history',
            'created_at', 'paid_at', 'shipped_at',
            'delivered_at', 'completed_at', 'cancelled_at',
            'expires_at'
        ]


class CheckoutSerializer(serializers.Serializer):
    """سریالایزر ثبت سفارش"""
    shipping_address_id = serializers.UUIDField(required=False, allow_null=True)
    coupon_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    use_wallet = serializers.BooleanField(default=False)
    wallet_amount = serializers.IntegerField(required=False, min_value=0, default=0)
    payment_method = serializers.ChoiceField(
        choices=['zarinpal', 'idpay', 'wallet'],
        default='zarinpal'
    )
    customer_note = serializers.CharField(max_length=500, required=False, allow_blank=True)


class CheckoutPreviewSerializer(serializers.Serializer):
    """سریالایزر پیش‌نمایش سفارش"""
    coupon_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    use_wallet = serializers.BooleanField(default=False)
    wallet_amount = serializers.IntegerField(required=False, min_value=0, default=0)
