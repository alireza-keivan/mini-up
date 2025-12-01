# apps/wallet/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Wallet, WalletTransaction, WalletDepositRequest


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """
    پنل مدیریت کیف پول‌ها
    """
    list_display = [
        'id',
        'user_display',
        'balance_display',
        'gift_balance_display',
        'total_balance_display',
        'is_locked_display',
        'created_at',
    ]
    list_filter = ['is_locked', 'created_at']
    search_fields = ['user__phone', 'user__first_name', 'user__last_name']
    readonly_fields = [
        'user',
        'balance',
        'gift_balance',
        'total_deposited',
        'total_spent',
        'created_at',
        'updated_at',
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user',)
        }),
        ('موجودی', {
            'fields': ('balance', 'gift_balance', 'total_deposited', 'total_spent')
        }),
        ('وضعیت', {
            'fields': ('is_locked', 'lock_reason')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_display(self, obj):
        return f"{obj.user.phone}"
    user_display.short_description = 'کاربر'

    def balance_display(self, obj):
        return format_html(
            '<span style="color: green; font-weight: bold;">{:,}</span> تومان',
            int(obj.balance)
        )
    balance_display.short_description = 'موجودی'

    def gift_balance_display(self, obj):
        if obj.gift_balance > 0:
            return format_html(
                '<span style="color: purple; font-weight: bold;">{:,}</span> تومان',
                int(obj.gift_balance)
            )
        return '-'
    gift_balance_display.short_description = 'اعتبار هدیه'

    def total_balance_display(self, obj):
        return format_html(
            '<span style="color: blue; font-weight: bold;">{:,}</span> تومان',
            int(obj.total_balance)
        )
    total_balance_display.short_description = 'موجودی کل'

    def is_locked_display(self, obj):
        if obj.is_locked:
            return format_html(
                '<span style="color: red;">🔒 قفل</span>'
            )
        return format_html('<span style="color: green;">✓ فعال</span>')
    is_locked_display.short_description = 'وضعیت'

    def has_add_permission(self, request):
        # کیف پول خودکار ساخته می‌شود
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    """
    پنل مدیریت تراکنش‌های کیف پول
    """
    list_display = [
        'short_id',
        'wallet_user',
        'transaction_type_display',
        'amount_display',
        'status_display',
        'created_at',
    ]
    list_filter = [
        'transaction_type',
        'status',
        'is_gift_credit',
        'created_at',
    ]
    search_fields = [
        'id',
        'wallet__user__phone',
        'description',
    ]
    readonly_fields = [
        'id',
        'wallet',
        'transaction_type',
        'status',
        'amount',
        'is_gift_credit',
        'balance_before',
        'balance_after',
        'order',
        'payment_transaction',
        'description',
        'metadata',
        'performed_by',
        'created_at',
        'updated_at',
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('id', 'wallet', 'transaction_type', 'status')
        }),
        ('مبالغ', {
            'fields': ('amount', 'is_gift_credit', 'balance_before', 'balance_after')
        }),
        ('ارتباطات', {
            'fields': ('order', 'payment_transaction', 'performed_by'),
            'classes': ('collapse',)
        }),
        ('جزئیات', {
            'fields': ('description', 'metadata'),
            'classes': ('collapse',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def short_id(self, obj):
        return str(obj.id)[:8] + '...'
    short_id.short_description = 'شناسه'

    def wallet_user(self, obj):
        return obj.wallet.user.phone
    wallet_user.short_description = 'کاربر'

    def transaction_type_display(self, obj):
        colors = {
            'deposit': '#28a745',
            'withdraw': '#dc3545',
            'purchase': '#fd7e14',
            'refund': '#17a2b8',
            'gift': '#6f42c1',
            'cashback': '#20c997',
            'admin_adjust': '#6c757d',
            'transfer_in': '#28a745',
            'transfer_out': '#dc3545',
        }
        color = colors.get(obj.transaction_type, '#000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_transaction_type_display()
        )
    transaction_type_display.short_description = 'نوع'

    def amount_display(self, obj):
        if obj.amount > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">+{:,}</span>',
                int(obj.amount)
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">{:,}</span>',
                int(obj.amount)
            )
    amount_display.short_description = 'مبلغ (تومان)'

    def status_display(self, obj):
        colors = {
            'pending': '#ffc107',
            'completed': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#6c757d',
            'reversed': '#17a2b8',
        }
        icons = {
            'pending': '⏳',
            'completed': '✓',
            'failed': '✗',
            'cancelled': '⊘',
            'reversed': '↩',
        }
        color = colors.get(obj.status, '#000')
        icon = icons.get(obj.status, '')
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color,
            icon,
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(WalletDepositRequest)
class WalletDepositRequestAdmin(admin.ModelAdmin):
    """
    پنل مدیریت درخواست‌های شارژ
    """
    list_display = [
        'short_id',
        'wallet_user',
        'amount_display',
        'status_display',
        'is_expired_display',
        'created_at',
    ]
    list_filter = [
        'status',
        'created_at',
    ]
    search_fields = [
        'id',
        'wallet__user__phone',
    ]
    readonly_fields = [
        'id',
        'wallet',
        'amount',
        'status',
        'payment_transaction',
        'wallet_transaction',
        'created_at',
        'updated_at',
        'expires_at',
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('id', 'wallet', 'amount', 'status')
        }),
        ('ارتباطات', {
            'fields': ('payment_transaction', 'wallet_transaction'),
            'classes': ('collapse',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at', 'expires_at'),
        }),
    )

    def short_id(self, obj):
        return str(obj.id)[:8] + '...'
    short_id.short_description = 'شناسه'

    def wallet_user(self, obj):
        return obj.wallet.user.phone
    wallet_user.short_description = 'کاربر'

    def amount_display(self, obj):
        return format_html(
            '<span style="font-weight: bold;">{:,}</span> تومان',
            int(obj.amount)
        )
    amount_display.short_description = 'مبلغ'

    def status_display(self, obj):
        colors = {
            'pending': '#ffc107',
            'paid': '#28a745',
            'failed': '#dc3545',
            'expired': '#6c757d',
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'

    def is_expired_display(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">منقضی شده</span>')
        if obj.status == 'pending':
            return format_html('<span style="color: green;">معتبر</span>')
        return '-'
    is_expired_display.short_description = 'اعتبار'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
