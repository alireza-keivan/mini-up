"""
Coupon & Discount Models for Mini-up
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Coupon(models.Model):
    """کوپن تخفیف"""
    
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'درصدی'
        FIXED = 'fixed', 'مبلغ ثابت'
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'فعال'
        INACTIVE = 'inactive', 'غیرفعال'
        EXPIRED = 'expired', 'منقضی شده'
    
    # Basic Info
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='کد کوپن'
    )
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    
    # Discount Settings
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE,
        verbose_name='نوع تخفیف'
    )
    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='مقدار تخفیف'
    )
    max_discount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name='حداکثر تخفیف',
        help_text='فقط برای تخفیف درصدی'
    )
    
    # Constraints
    min_purchase = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='حداقل خرید'
    )
    max_uses = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='حداکثر تعداد استفاده'
    )
    max_uses_per_user = models.PositiveIntegerField(
        default=1,
        verbose_name='حداکثر استفاده هر کاربر'
    )
    used_count = models.PositiveIntegerField(
        default=0,
        verbose_name='تعداد استفاده شده'
    )
    
    # Validity
    valid_from = models.DateTimeField(
        verbose_name='معتبر از'
    )
    valid_until = models.DateTimeField(
        verbose_name='معتبر تا'
    )
    
    # Restrictions
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    first_purchase_only = models.BooleanField(
        default=False,
        verbose_name='فقط اولین خرید'
    )
    
    # User Restrictions (optional)
    allowed_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='allowed_coupons',
        verbose_name='کاربران مجاز'
    )
    
    # Category/Product Restrictions
    allowed_categories = models.ManyToManyField(
        'products.Category',
        blank=True,
        related_name='coupons',
        verbose_name='دسته‌بندی‌های مجاز'
    )
    allowed_products = models.ManyToManyField(
        'products.Product',
        blank=True,
        related_name='coupons',
        verbose_name='محصولات مجاز'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'کوپن'
        verbose_name_plural = 'کوپن‌ها'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.get_discount_display()}"
    
    def get_discount_display(self):
        """نمایش مقدار تخفیف"""
        if self.discount_type == self.DiscountType.PERCENTAGE:
            return f"{self.discount_value}%"
        return f"{self.discount_value:,.0f} تومان"
    
    @property
    def status(self):
        """وضعیت فعلی کوپن"""
        now = timezone.now()
        if not self.is_active:
            return self.Status.INACTIVE
        if now > self.valid_until:
            return self.Status.EXPIRED
        if now < self.valid_from:
            return self.Status.INACTIVE
        if self.max_uses and self.used_count >= self.max_uses:
            return self.Status.EXPIRED
        return self.Status.ACTIVE
    
    @property
    def is_valid(self):
        """آیا کوپن قابل استفاده است؟"""
        return self.status == self.Status.ACTIVE
    
    def can_use(self, user, cart_total):
        """بررسی امکان استفاده توسط کاربر"""
        # Check basic validity
        if not self.is_valid:
            return False, 'کوپن نامعتبر است'
        
        # Check minimum purchase
        if cart_total < self.min_purchase:
            return False, f'حداقل خرید {self.min_purchase:,.0f} تومان'
        
        # For guest users, skip user-specific checks
        if user is None or not user.is_authenticated:
            # Guest users can't use user-restricted coupons
            if self.allowed_users.exists():
                return False, 'این کوپن نیاز به ورود دارد'
            if self.first_purchase_only:
                return False, 'این کوپن نیاز به ورود دارد'
            return True, 'معتبر'
        
        # Check user restrictions
        if self.allowed_users.exists() and user not in self.allowed_users.all():
            return False, 'این کوپن برای شما فعال نیست'
        
        # Check per-user usage
        user_usage = self.usages.filter(user=user).count()
        if user_usage >= self.max_uses_per_user:
            return False, 'شما قبلاً از این کوپن استفاده کرده‌اید'
        
        # Check first purchase only
        if self.first_purchase_only:
            from apps.orders.models import Order
            if Order.objects.filter(user=user, status__in=['completed', 'processing']).exists():
                return False, 'این کوپن فقط برای اولین خرید است'
        
        return True, 'معتبر'
    
    def calculate_discount(self, amount):
        """محاسبه مبلغ تخفیف"""
        if self.discount_type == self.DiscountType.PERCENTAGE:
            discount = amount * self.discount_value / 100
            if self.max_discount:
                discount = min(discount, self.max_discount)
        else:
            discount = min(self.discount_value, amount)
        return discount
    
    def use(self):
        """ثبت یک استفاده"""
        self.used_count += 1
        self.save(update_fields=['used_count'])


class CouponUsage(models.Model):
    """تاریخچه استفاده از کوپن"""
    
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='usages',
        verbose_name='کوپن'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coupon_usages',
        verbose_name='کاربر'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        related_name='coupon_usages',
        verbose_name='سفارش'
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='مبلغ تخفیف'
    )
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'استفاده از کوپن'
        verbose_name_plural = 'استفاده‌های کوپن'
        ordering = ['-used_at']
    
    def __str__(self):
        return f"{self.user} - {self.coupon.code}"
