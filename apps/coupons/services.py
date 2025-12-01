# apps/coupons/services.py

"""
Coupon Service Layer
Handles all coupon-related business logic
"""

from decimal import Decimal
from typing import Tuple, Optional, Dict, Any, List
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.core.cache import cache
from django.core.exceptions import ValidationError

from .models import Coupon, CouponUsage

import logging

logger = logging.getLogger(__name__)


class CouponService:
    """
    سرویس مدیریت کوپن‌های تخفیف
    
    این سرویس تمام عملیات مربوط به کوپن‌ها را مدیریت می‌کند:
    - اعتبارسنجی کوپن
    - محاسبه تخفیف
    - اعمال کوپن به سبد خرید
    - ثبت استفاده از کوپن
    """
    
    # Cache settings
    CACHE_TIMEOUT = 60 * 5  # 5 minutes
    COUPON_CACHE_KEY = 'coupon:{code}'
    
    # ─────────────────────────────────────────────────────────────────────────
    # COUPON RETRIEVAL
    # ─────────────────────────────────────────────────────────────────────────
    
    @classmethod
    def get_coupon_by_code(cls, code: str) -> Optional[Coupon]:
        """
        دریافت کوپن با کد
        
        Args:
            code: کد کوپن (case-insensitive)
            
        Returns:
            Coupon or None
        """
        code = code.strip().upper()
        
        # Check cache first
        cache_key = cls.COUPON_CACHE_KEY.format(code=code)
        coupon = cache.get(cache_key)
        
        if coupon is None:
            try:
                coupon = Coupon.objects.prefetch_related(
                    'allowed_users',
                    'allowed_categories',
                    'allowed_products'
                ).get(code__iexact=code)
                
                # Cache the coupon
                cache.set(cache_key, coupon, cls.CACHE_TIMEOUT)
            except Coupon.DoesNotExist:
                return None
        
        return coupon
    
    @classmethod
    def get_active_coupons(cls) -> List[Coupon]:
        """
        دریافت لیست کوپن‌های فعال
        
        Returns:
            List[Coupon]
        """
        now = timezone.now()
        
        return Coupon.objects.filter(
            is_active=True,
            valid_from__lte=now,
            valid_until__gte=now
        ).filter(
            Q(max_uses__isnull=True) | Q(used_count__lt=Q('max_uses'))
        ).order_by('-created_at')
    
    @classmethod
    def get_user_available_coupons(cls, user) -> List[Coupon]:
        """
        دریافت کوپن‌های قابل استفاده برای کاربر
        
        Args:
            user: کاربر
            
        Returns:
            List[Coupon]
        """
        now = timezone.now()
        
        # Base query for active coupons
        queryset = Coupon.objects.filter(
            is_active=True,
            valid_from__lte=now,
            valid_until__gte=now
        )
        
        # Filter by max uses
        queryset = queryset.filter(
            Q(max_uses__isnull=True) | Q(used_count__lt=Q('max_uses'))
        )
        
        # Filter by allowed users (public coupons or user-specific)
        queryset = queryset.filter(
            Q(allowed_users__isnull=True) | Q(allowed_users=user)
        ).distinct()
        
        # Get user's usage counts
        user_usages = CouponUsage.objects.filter(
            user=user
        ).values('coupon_id').annotate(
            usage_count=Count('id')
        )
        
        usage_map = {u['coupon_id']: u['usage_count'] for u in user_usages}
        
        # Filter coupons where user hasn't exceeded max_uses_per_user
        available = []
        for coupon in queryset:
            user_usage = usage_map.get(coupon.id, 0)
            if user_usage < coupon.max_uses_per_user:
                available.append(coupon)
        
        return available
    
    # ─────────────────────────────────────────────────────────────────────────
    # VALIDATION
    # ─────────────────────────────────────────────────────────────────────────
    
    @classmethod
    def validate_coupon(
        cls,
        code: str,
        user,
        cart_total: Decimal,
        cart_items: Optional[List] = None
    ) -> Tuple[bool, str, Optional[Coupon]]:
        """
        اعتبارسنجی کامل کوپن
        
        Args:
            code: کد کوپن
            user: کاربر
            cart_total: مجموع سبد خرید (تومان)
            cart_items: آیتم‌های سبد خرید (اختیاری)
            
        Returns:
            Tuple[bool, str, Optional[Coupon]]:
                - is_valid: آیا معتبر است
                - message: پیام
                - coupon: شیء کوپن (در صورت معتبر بودن)
        """
        # Get coupon
        coupon = cls.get_coupon_by_code(code)
        
        if not coupon:
            return False, 'کد کوپن یافت نشد', None
        
        # Check basic validity
        if not coupon.is_valid:
            status = coupon.status
            if status == Coupon.Status.EXPIRED:
                return False, 'کوپن منقضی شده است', None
            elif status == Coupon.Status.INACTIVE:
                return False, 'کوپن غیرفعال است', None
            else:
                return False, 'کوپن نامعتبر است', None
        
        # Check date range
        now = timezone.now()
        if now < coupon.valid_from:
            return False, f'این کوپن از {coupon.valid_from.strftime("%Y/%m/%d")} فعال می‌شود', None
        
        if now > coupon.valid_until:
            return False, 'کوپن منقضی شده است', None
        
        # Check global usage limit
        if coupon.max_uses and coupon.used_count >= coupon.max_uses:
            return False, 'ظرفیت استفاده از این کوپن تمام شده است', None
        
        # Check minimum purchase
        if cart_total < coupon.min_purchase:
            remaining = coupon.min_purchase - cart_total
            return False, f'حداقل خرید {coupon.min_purchase:,.0f} تومان (کسری: {remaining:,.0f} تومان)', None
        
        # Check user restrictions
        if coupon.allowed_users.exists():
            if not coupon.allowed_users.filter(id=user.id).exists():
                return False, 'این کوپن برای شما فعال نیست', None
        
        # Check per-user usage limit
        user_usage_count = CouponUsage.objects.filter(
            coupon=coupon,
            user=user
        ).count()
        
        if user_usage_count >= coupon.max_uses_per_user:
            return False, 'شما قبلاً از این کوپن استفاده کرده‌اید', None
        
        # Check first purchase only
        if coupon.first_purchase_only:
            from apps.orders.models import Order
            has_previous_orders = Order.objects.filter(
                user=user,
                status__in=['completed', 'processing', 'shipped', 'delivered']
            ).exists()
            
            if has_previous_orders:
                return False, 'این کوپن فقط برای اولین خرید قابل استفاده است', None
        
        # Check category/product restrictions
        if cart_items and (coupon.allowed_categories.exists() or coupon.allowed_products.exists()):
            is_applicable, message = cls._check_product_restrictions(coupon, cart_items)
            if not is_applicable:
                return False, message, None
        
        return True, 'کوپن معتبر است', coupon
    
    @classmethod
    def _check_product_restrictions(
        cls,
        coupon: Coupon,
        cart_items: List
    ) -> Tuple[bool, str]:
        """
        بررسی محدودیت‌های محصول/دسته‌بندی
        
        Args:
            coupon: کوپن
            cart_items: آیتم‌های سبد خرید
            
        Returns:
            Tuple[bool, str]
        """
        allowed_category_ids = set(
            coupon.allowed_categories.values_list('id', flat=True)
        )
        allowed_product_ids = set(
            coupon.allowed_products.values_list('id', flat=True)
        )
        
        # If no restrictions, allow all
        if not allowed_category_ids and not allowed_product_ids:
            return True, ''
        
        # Check if at least one item matches
        has_applicable_item = False
        
        for item in cart_items:
            product = item.product if hasattr(item, 'product') else item.get('product')
            
            if not product:
                continue
            
            # Check product restriction
            if allowed_product_ids and product.id in allowed_product_ids:
                has_applicable_item = True
                break
            
            # Check category restriction
            if allowed_category_ids and product.category_id in allowed_category_ids:
                has_applicable_item = True
                break
        
        if not has_applicable_item:
            return False, 'هیچ محصولی در سبد شما مشمول این کوپن نیست'
        
        return True, ''
    
    # ─────────────────────────────────────────────────────────────────────────
    # DISCOUNT CALCULATION
    # ─────────────────────────────────────────────────────────────────────────
    
    @classmethod
    def calculate_discount(
        cls,
        coupon: Coupon,
        cart_total: Decimal,
        cart_items: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        محاسبه مبلغ تخفیف
        
        Args:
            coupon: کوپن
            cart_total: مجموع سبد خرید
            cart_items: آیتم‌های سبد (برای تخفیف محصول-محور)
            
        Returns:
            dict: {
                'discount_amount': Decimal,
                'applicable_amount': Decimal,
                'final_total': Decimal,
                'discount_percent': float
            }
        """
        cart_total = Decimal(str(cart_total))
        
        # Calculate applicable amount (considering product restrictions)
        applicable_amount = cls._get_applicable_amount(coupon, cart_total, cart_items)
        
        # Calculate discount
        if coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
            discount = applicable_amount * coupon.discount_value / 100
            
            # Apply max discount cap
            if coupon.max_discount:
                discount = min(discount, coupon.max_discount)
        else:
            # Fixed amount discount
            discount = min(coupon.discount_value, applicable_amount)
        
        # Ensure discount doesn't exceed cart total
        discount = min(discount, cart_total)
        
        final_total = cart_total - discount
        
        # Calculate effective discount percentage
        discount_percent = float(discount / cart_total * 100) if cart_total > 0 else 0
        
        return {
            'discount_amount': discount,
            'applicable_amount': applicable_amount,
            'final_total': final_total,
            'discount_percent': round(discount_percent, 2),
            'coupon_code': coupon.code,
            'coupon_description': coupon.description,
        }
    
    @classmethod
    def _get_applicable_amount(
        cls,
        coupon: Coupon,
        cart_total: Decimal,
        cart_items: Optional[List]
    ) -> Decimal:
        """
        محاسبه مبلغ قابل تخفیف
        
        اگر کوپن محدودیت محصول/دسته دارد، فقط مبلغ آیتم‌های مجاز حساب می‌شود
        """
        allowed_category_ids = set(
            coupon.allowed_categories.values_list('id', flat=True)
        )
        allowed_product_ids = set(
            coupon.allowed_products.values_list('id', flat=True)
        )
        
        # If no restrictions, apply to entire cart
        if not allowed_category_ids and not allowed_product_ids:
            return cart_total
        
        if not cart_items:
            return cart_total
        
        applicable_amount = Decimal('0')
        
        for item in cart_items:
            product = item.product if hasattr(item, 'product') else item.get('product')
            item_total = item.total_price if hasattr(item, 'total_price') else item.get('total_price', 0)
            
            if not product:
                continue
            
            is_applicable = False
            
            # Check product match
            if allowed_product_ids and product.id in allowed_product_ids:
                is_applicable = True
            
            # Check category match
            if allowed_category_ids and product.category_id in allowed_category_ids:
                is_applicable = True
            
            if is_applicable:
                applicable_amount += Decimal(str(item_total))
        
        return applicable_amount
    
    # ─────────────────────────────────────────────────────────────────────────
    # APPLY COUPON
    # ─────────────────────────────────────────────────────────────────────────
    
    @classmethod
    @transaction.atomic
    def apply_coupon(
        cls,
        code: str,
        user,
        cart_total: Decimal,
        cart_items: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        اعمال کوپن به سبد خرید
        
        این متد:
        1. کوپن را *اعتبارسنجی* می‌کند
        2. در صورت معتبر بودن، *مبلغ تخفیف* را محاسبه می‌کند
        3. نتیجه را در قالب یک دیکشنری استاندارد بازمی‌گرداند
        
        توجه: این متد هیچ «ثبت استفاده» انجام نمی‌دهد.
               ثبت استفاده فقط باید پس از ثبت نهایی سفارش انجام شود.
        """
        
        # 1) Validate coupon
        is_valid, message, coupon = cls.validate_coupon(
            code=code,
            user=user,
            cart_total=cart_total,
            cart_items=cart_items
        )
        
        if not is_valid:
            return {
                "success": False,
                "message": message,
                "coupon": None,
                "discount": Decimal('0'),
                "final_total": Decimal(cart_total),
                "details": {}
            }

        # 2) Calculate discount
        discount_info = cls.calculate_discount(
            coupon=coupon,
            cart_total=cart_total,
            cart_items=cart_items
        )
        
        return {
            "success": True,
            "message": "کوپن با موفقیت اعمال شد",
            "coupon": coupon,
            "discount": discount_info["discount_amount"],
            "final_total": discount_info["final_total"],
            "details": discount_info
        }

    @classmethod
    @transaction.atomic
    def use(cls, coupon: Coupon, user, order=None) -> CouponUsage:
        """
        ثبت استفاده از کوپن (فقط پس از پرداخت موفق سفارش)

        Args:
            coupon: شی کوپن
            user: کاربر
            order: سفارش نهایی (اختیاری)

        Returns:
            CouponUsage
        """
        
        usage = CouponUsage.objects.create(
            coupon=coupon,
            user=user,
            order=order
        )

        # Increase global usage count
        coupon.used_count = coupon.used_count + 1
        coupon.save(update_fields=['used_count'])

        # Invalidate cache for accuracy
        cache.delete(cls.COUPON_CACHE_KEY.format(code=coupon.code.upper()))

        return usage
