# apps/payments/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import PaymentGateway, Transaction


@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    """
    Admin configuration for Payment Gateways.
    """
    
    list_display = [
        'name',
        'gateway_type',
        'is_active',        # ✅ اضافه شد - برای list_editable لازم است
        'is_sandbox',
        'priority',
        'display_success_rate',
        'total_transactions',
        'display_status_badge',
    ]
    
    list_display_links = ['name']  # فقط name قابل کلیک باشد
    
    list_editable = [
        'is_active',        # ✅ حالا در list_display هم هست
        'is_sandbox',
        'priority',
    ]
    
    list_filter = [
        'is_active',
        'is_sandbox',
        'gateway_type',
    ]
    
    search_fields = ['name', 'merchant_id']
    
    readonly_fields = [
        'total_transactions',
        'successful_transactions',
        'total_amount',
        'success_rate',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'gateway_type', 'priority')
        }),
        ('احراز هویت', {
            'fields': ('merchant_id', 'api_key'),
            'classes': ('collapse',),
        }),
        ('تنظیمات', {
            'fields': ('is_active', 'is_sandbox', 'min_amount', 'max_amount')
        }),
        ('آمار', {
            'fields': (
                'total_transactions',
                'successful_transactions', 
                'total_amount',
                'success_rate',
            ),
            'classes': ('collapse',),
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def display_status_badge(self, obj):
        """نمایش وضعیت با badge رنگی"""
        if obj.is_active:
            color = 'green'
            text = 'فعال'
        else:
            color = 'red'
            text = 'غیرفعال'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, text
        )
    display_status_badge.short_description = 'وضعیت'
    
    def display_success_rate(self, obj):
        """نمایش نرخ موفقیت با رنگ"""
        rate = obj.success_rate
        if rate >= 90:
            color = 'green'
        elif rate >= 70:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, rate
        )
    display_success_rate.short_description = 'نرخ موفقیت'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Transactions.
    """
    
    list_display = [
        'tracking_code',
        'user',
        'display_amount',
        'gateway',
        'transaction_type',
        'display_status_badge',
        'created_at',
        'paid_at',
    ]
    
    list_display_links = ['tracking_code']
    
    list_filter = [
        'status',
        'transaction_type',
        'gateway',
        ('created_at', admin.DateFieldListFilter),
        ('paid_at', admin.DateFieldListFilter),
    ]
    
    search_fields = [
        'tracking_code',
        'reference_id',
        'authority',
        'user__phone',
        'user__email',
        'card_number',
    ]
    
    readonly_fields = [
        'transaction_id',
        'tracking_code',
        'amount_rial',
        'authority',
        'reference_id',
        'card_number',
        'card_hash',
        'gateway_request',
        'gateway_response',
        'verify_response',
        'ip_address',
        'user_agent',
        'created_at',
        'updated_at',
        'paid_at',
        'verified_at',
        'expires_at',
    ]
    
    fieldsets = (
        ('شناسایی', {
            'fields': ('transaction_id', 'tracking_code', 'user', 'order')
        }),
        ('مبلغ و درگاه', {
            'fields': ('amount', 'amount_rial', 'gateway', 'transaction_type')
        }),
        ('وضعیت', {
            'fields': ('status', 'description')
        }),
        ('اطلاعات درگاه', {
            'fields': ('authority', 'reference_id', 'card_number', 'card_hash'),
            'classes': ('collapse',),
        }),
        ('خطاها', {
            'fields': ('error_code', 'error_message'),
            'classes': ('collapse',),
        }),
        ('داده‌های خام', {
            'fields': ('gateway_request', 'gateway_response', 'verify_response'),
            'classes': ('collapse',),
        }),
        ('اطلاعات فنی', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',),
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'verified_at', 'expires_at'),
            'classes': ('collapse',),
        }),
    )
    
    date_hierarchy = 'created_at'
    
    ordering = ['-created_at']
    
    def display_amount(self, obj):
        """نمایش مبلغ با فرمت"""
        return format_html(
            '<span style="font-weight: bold;">{:,}</span> <small>تومان</small>',
            obj.amount
        )
    display_amount.short_description = 'مبلغ'
    display_amount.admin_order_field = 'amount'
    
    def display_status_badge(self, obj):
        """نمایش وضعیت با badge رنگی"""
        colors = {
            'pending': '#f0ad4e',      # زرد
            'processing': '#5bc0de',   # آبی
            'success': '#5cb85c',      # سبز
            'failed': '#d9534f',       # قرمز
            'cancelled': '#777',       # خاکستری
            'refunded': '#9b59b6',     # بنفش
            'expired': '#95a5a6',      # خاکستری روشن
        }
        color = colors.get(obj.status, '#777')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    display_status_badge.short_description = 'وضعیت'
    display_status_badge.admin_order_field = 'status'
    
    def has_add_permission(self, request):
        """تراکنش‌ها فقط از طریق سیستم ایجاد می‌شوند"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """تراکنش‌ها قابل حذف نیستند"""
        return False
