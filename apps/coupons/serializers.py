# apps/coupons/serializers.py

"""
Coupon Serializers
Handles serialization/deserialization for coupon-related data
"""

from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone

from .models import Coupon, CouponUsage


# ═══════════════════════════════════════════════════════════════════════════════
# COUPON SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class CouponSerializer(serializers.ModelSerializer):
    """
    سریالایزر کامل کوپن
    برای نمایش جزئیات کوپن به کاربر
    """
    
    discount_type_display = serializers.CharField(
        source='get_discount_type_display', 
        read_only=True
    )
    status = serializers.CharField(read_only=True)
    status_display = serializers.SerializerMethodField()
    is_valid = serializers.BooleanField(read_only=True)
    remaining_uses = serializers.SerializerMethodField()
    discount_display = serializers.SerializerMethodField()
    
    # Restrictions info
    has_product_restrictions = serializers.SerializerMethodField()
    has_category_restrictions = serializers.SerializerMethodField()
    allowed_categories_names = serializers.SerializerMethodField()
    allowed_products_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = [
            'id',
            'code',
            'description',
            'discount_type',
            'discount_type_display',
            'discount_value',
            'discount_display',
            'max_discount',
            'min_purchase',
            'valid_from',
            'valid_until',
            'status',
            'status_display',
            'is_valid',
            'remaining_uses',
            'max_uses_per_user',
            'first_purchase_only',
            'has_product_restrictions',
            'has_category_restrictions',
            'allowed_categories_names',
            'allowed_products_names',
        ]
        read_only_fields = fields
    
    def get_status_display(self, obj) -> str:
        """نمایش فارسی وضعیت"""
        status_map = {
            'active': 'فعال',
            'expired': 'منقضی شده',
            'depleted': 'تمام شده',
            'inactive': 'غیرفعال',
            'upcoming': 'در انتظار',
        }
        return status_map.get(obj.status, obj.status)
    
    def get_remaining_uses(self, obj) -> int | None:
        """تعداد استفاده باقی‌مانده"""
        if obj.max_uses:
            return max(0, obj.max_uses - obj.used_count)
        return None  # Unlimited
    
    def get_discount_display(self, obj) -> str:
        """نمایش تخفیف به صورت خوانا"""
        if obj.discount_type == Coupon.DiscountType.PERCENTAGE:
            text = f'{obj.discount_value:.0f}% تخفیف'
            if obj.max_discount:
                text += f' (حداکثر {obj.max_discount:,.0f} تومان)'
            return text
        else:
            return f'{obj.discount_value:,.0f} تومان تخفیف'
    
    def get_has_product_restrictions(self, obj) -> bool:
        return obj.allowed_products.exists()
    
    def get_has_category_restrictions(self, obj) -> bool:
        return obj.allowed_categories.exists()
    
    def get_allowed_categories_names(self, obj) -> list:
        return list(obj.allowed_categories.values_list('name', flat=True)[:5])
    
    def get_allowed_products_names(self, obj) -> list:
        return list(obj.allowed_products.values_list('name', flat=True)[:5])


class CouponMinimalSerializer(serializers.ModelSerializer):
    """
    سریالایزر ساده کوپن
    برای لیست کوپن‌ها یا نمایش سریع
    """
    
    discount_display = serializers.SerializerMethodField()
    is_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Coupon
        fields = [
            'id',
            'code',
            'description',
            'discount_display',
            'min_purchase',
            'valid_until',
            'is_valid',
        ]
        read_only_fields = fields
    
    def get_discount_display(self, obj) -> str:
        if obj.discount_type == Coupon.DiscountType.PERCENTAGE:
            return f'{obj.discount_value:.0f}%'
        return f'{obj.discount_value:,.0f} تومان'


# ═══════════════════════════════════════════════════════════════════════════════
# COUPON USAGE SERIALIZER
# ═══════════════════════════════════════════════════════════════════════════════

class CouponUsageSerializer(serializers.ModelSerializer):
    """
    سریالایزر استفاده از کوپن
    """
    
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    coupon_description = serializers.CharField(source='coupon.description', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = CouponUsage
        fields = [
            'id',
            'coupon_code',
            'coupon_description',
            'order_number',
            'discount_amount',
            'used_at',
        ]
        read_only_fields = fields


# ═══════════════════════════════════════════════════════════════════════════════
# INPUT SERIALIZERS (برای درخواست‌های API)
# ═══════════════════════════════════════════════════════════════════════════════

class CouponValidateSerializer(serializers.Serializer):
    """
    سریالایزر اعتبارسنجی کوپن
    POST /coupons/api/v1/validate/
    """
    
    code = serializers.CharField(
        max_length=50,
        required=True,
        help_text='کد کوپن'
    )
    cart_total = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        required=True,
        min_value=Decimal('0'),
        help_text='مجموع سبد خرید (تومان)'
    )
    
    def validate_code(self, value):
        """نرمال‌سازی کد کوپن"""
        return value.strip().upper()


class CouponApplySerializer(serializers.Serializer):
    """
    سریالایزر اعمال کوپن به سبد خرید
    POST /coupons/api/v1/apply/
    """
    
    code = serializers.CharField(
        max_length=50,
        required=True,
        help_text='کد کوپن'
    )
    
    def validate_code(self, value):
        return value.strip().upper()


class CouponRemoveSerializer(serializers.Serializer):
    """
    سریالایزر حذف کوپن از سبد خرید
    POST /coupons/api/v1/remove/
    """
    pass  # No input needed, just removes the applied coupon


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class CouponApplyResponseSerializer(serializers.Serializer):
    """
    سریالایزر پاسخ اعمال کوپن
    """
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    coupon = CouponMinimalSerializer(allow_null=True)
    discount_amount = serializers.DecimalField(
        max_digits=12, 
        decimal_places=0
    )
    final_total = serializers.DecimalField(
        max_digits=12, 
        decimal_places=0
    )
    discount_percent = serializers.FloatField()


class CouponValidateResponseSerializer(serializers.Serializer):
    """
    سریالایزر پاسخ اعتبارسنجی کوپن
    """
    
    is_valid = serializers.BooleanField()
    message = serializers.CharField()
    coupon = CouponSerializer(allow_null=True)
    estimated_discount = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        allow_null=True
    )
