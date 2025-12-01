from django.contrib import admin
from .models import Coupon, CouponUsage


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'status', 'used_count', 'valid_until')
    list_filter = ('discount_type', 'is_active', 'valid_until')
    search_fields = ('code', 'description')
    filter_horizontal = ('allowed_users', 'allowed_categories', 'allowed_products')
    
    fieldsets = (
        ('اطلاعات کوپن', {
            'fields': ('code', 'description')
        }),
        ('تخفیف', {
            'fields': ('discount_type', 'discount_value', 'max_discount')
        }),
        ('محدودیت‌ها', {
            'fields': ('min_purchase', 'max_uses', 'max_uses_per_user', 'first_purchase_only')
        }),
        ('اعتبار', {
            'fields': ('valid_from', 'valid_until', 'is_active')
        }),
        ('محدودیت کاربران', {
            'fields': ('allowed_users',),
            'classes': ('collapse',)
        }),
        ('محدودیت محصولات', {
            'fields': ('allowed_categories', 'allowed_products'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'user', 'order', 'discount_amount', 'used_at')
    list_filter = ('used_at', 'coupon')
    search_fields = ('coupon__code', 'user__phone')
