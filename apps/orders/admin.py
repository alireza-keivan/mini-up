from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory


# ==================== CART ====================
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('line_total', 'discount_amount')
    
    def line_total(self, obj):
        return f"{obj.line_total:,} تومان"
    line_total.short_description = 'جمع کل'
    
    def discount_amount(self, obj):
        return f"{obj.discount_amount:,} تومان"
    discount_amount.short_description = 'تخفیف'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'total_items', 'total_display', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__phone', 'session_key')
    readonly_fields = ('total_items', 'subtotal', 'total_discount', 'total')
    inlines = [CartItemInline]
    
    def total_display(self, obj):
        return f"{obj.total:,} تومان"
    total_display.short_description = 'مبلغ کل'


# ==================== ORDER ====================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('unit_price_display', 'total_price_display', 'discount_display')
    fields = (
        'product', 'variant', 'quantity', 
        'unit_price_display', 'discount_display', 'total_price_display',
        'game_user_id', 'currency_amount'
    )
    
    def unit_price_display(self, obj):
        # ✅ بررسی وجود آیتم و مقدار
        if obj and obj.pk and obj.unit_price is not None:
            return f"{obj.unit_price:,} تومان"
        return "-"
    unit_price_display.short_description = 'قیمت واحد'
    
    def total_price_display(self, obj):
        if obj and obj.pk and obj.total_price is not None:
            return f"{obj.total_price:,} تومان"
        return "-"
    total_price_display.short_description = 'قیمت کل'
    
    def discount_display(self, obj):
        if obj and obj.pk and obj.discount_amount is not None:
            return f"{obj.discount_amount:,} تومان"
        return "-"
    discount_display.short_description = 'تخفیف'

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'note', 'changed_by', 'changed_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'user', 'status', 'total_display', 
        'payment_method', 'is_paid_display', 'created_at'
    )
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'tracking_code', 'user__phone', 'user__email')
    readonly_fields = (
        'order_number', 'tracking_code', 'created_at', 'updated_at',
        'paid_at', 'shipped_at', 'delivered_at', 'completed_at', 'cancelled_at',
        'subtotal', 'discount_amount', 'coupon_discount', 'shipping_cost',
        'wallet_used', 'total', 'amount_payable', 'ip_address', 'user_agent'
    )
    
    fieldsets = (
        ('اطلاعات سفارش', {
            'fields': ('order_number', 'tracking_code', 'user', 'status')
        }),
        ('مبالغ', {
            'fields': (
                'subtotal', 'discount_amount', 'coupon_discount', 
                'shipping_cost', 'wallet_used', 'total', 'amount_payable'
            )
        }),
        ('پرداخت', {
            'fields': ('payment_method', 'coupon', 'paid_at')
        }),
        ('ارسال', {
            'fields': ('shipping_address', 'shipping_data', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
        ('یادداشت‌ها', {
            'fields': ('customer_note', 'admin_note'),
            'classes': ('collapse',)
        }),
        ('اطلاعات فنی', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at', 'expires_at'),
            'classes': ('collapse',)
        }),
        ('تاریخ‌ها', {
            'fields': ('completed_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    def total_display(self, obj):
        return f"{obj.total:,} تومان"
    total_display.short_description = 'مبلغ کل'
    
    def is_paid_display(self, obj):
        return obj.is_paid
    is_paid_display.boolean = True
    is_paid_display.short_description = 'پرداخت شده'
    
    actions = ['mark_confirmed', 'mark_shipped', 'mark_completed', 'mark_cancelled']
    
    @admin.action(description='تایید سفارشات انتخاب شده')
    def mark_confirmed(self, request, queryset):
        updated = queryset.filter(status=Order.Status.PENDING).update(
            status=Order.Status.CONFIRMED
        )
        self.message_user(request, f'{updated} سفارش تایید شد.')
    
    @admin.action(description='ارسال سفارشات انتخاب شده')
    def mark_shipped(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status=Order.Status.CONFIRMED).update(
            status=Order.Status.SHIPPED,
            shipped_at=timezone.now()
        )
        self.message_user(request, f'{updated} سفارش ارسال شد.')
    
    @admin.action(description='تکمیل سفارشات انتخاب شده')
    def mark_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(
            status__in=[Order.Status.SHIPPED, Order.Status.DELIVERED]
        ).update(
            status=Order.Status.COMPLETED,
            completed_at=timezone.now()
        )
        self.message_user(request, f'{updated} سفارش تکمیل شد.')
    
    @admin.action(description='لغو سفارشات انتخاب شده')
    def mark_cancelled(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(
            status__in=[Order.Status.PENDING, Order.Status.CONFIRMED]
        ).update(
            status=Order.Status.CANCELLED,
            cancelled_at=timezone.now()
        )
        self.message_user(request, f'{updated} سفارش لغو شد.')


# ❌ این بخش را حذف کنید - دیگر نیازی به ثبت مستقل OrderItem نیست
# @admin.register(OrderItem)
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ('order', 'product', 'quantity')
#     search_fields = ('order__order_number', 'product__name')


# ==================== STATUS HISTORY (اختیاری) ====================
# اگر می‌خواهید تاریخچه را هم به صورت مستقل ببینید:
@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('new_status', 'changed_at')
    search_fields = ('order__order_number',)
    readonly_fields = ('order', 'old_status', 'new_status', 'note', 'changed_by', 'changed_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
