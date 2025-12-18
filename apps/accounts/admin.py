from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import User, Profile, OTP

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'id',
        'avatar_thumb',
        'get_identifier',
        'first_name',
        'last_name',
        'auth_provider_display',
        'is_phone_verified',
        'is_email_verified',
        'is_active',
        'is_staff',
        'date_joined',)
    list_filter = (
        'auth_provider',
        'is_active',
        'is_staff',
        'is_superuser',
        'is_phone_verified',
        'is_email_verified',
    )
    search_fields = (
        'phone',
        'email',
        'first_name',
        'last_name',
        'google_id',
        'referral_code',
    )
    ordering = ('-date_joined',)
    readonly_fields = (
        'date_joined',
        'last_login',
        'referral_code',
        'google_id',
        'avatar_preview',
        'cart_items_display',
        'wallet_transactions_display',
    )
    
    fieldsets = (
        (_('اطلاعات ورود'), {
            'fields': ('phone', 'email', 'password'),
        }),
        (_('اطلاعات شخصی'), {
            'fields': ('first_name', 'last_name', 'avatar', 'avatar_preview'),
        }),
        (_('احراز هویت گوگل'), {
            'fields': ('auth_provider', 'google_id', 'avatar_url'),
            'classes': ('collapse',),  # قابل باز/بسته شدن
        }),
        (_('وضعیت تأیید'), {
            'fields': ('is_phone_verified', 'is_email_verified'),
        }),
        (_('سیستم معرفی'), {
            'fields': ('referral_code', 'referred_by'),
        }),
        (_('سبد خرید'), {
            'fields': ('cart_items_display',),
            'classes': ('collapse',),
        }),
        (_('کیف پول و تراکنش‌ها'), {
            'fields': ('wallet_transactions_display',),
            'classes': ('collapse',),
        }),
        (_('دسترسی‌ها'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('تاریخ‌ها'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )
    
    add_fieldsets = (
        (_('اطلاعات اصلی'), {
            'classes': ('wide',),
            'fields': ('phone', 'email', 'auth_provider'),
        }),
        (_('رمز عبور'), {
            'classes': ('wide',),
            'fields': ('password1', 'password2'),
        }),
        (_('اطلاعات شخصی (اختیاری)'), {
            'classes': ('wide', 'collapse'),
            'fields': ('first_name', 'last_name'),
        }),
    )
    filter_horizontal = ('groups', 'user_permissions')
    
    @admin.display(description=_('شناسه کاربر'))
    def get_identifier(self, obj):
        """نمایش شماره تلفن یا ایمیل"""
        if obj.phone:
            return obj.phone
        elif obj.email:
            return obj.email
        return f"ID: {obj.id}"

    @admin.display(description=_('روش ثبت‌نام'))
    def auth_provider_display(self, obj):
        """نمایش روش احراز هویت با آیکون"""
        icons = {
            'phone': '📱 موبایل',
            'google': '🔷 گوگل',
        }
        return icons.get(obj.auth_provider, obj.auth_provider)
    
    @admin.display(description=_('تصویر پروفایل'))
    def avatar_thumb(self, obj):
        """نمایش تصویر مینیاتوری در لیست"""
        url = obj.get_avatar_url()
        if url:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; '
                'border-radius: 50%; object-fit: cover; border: 2px solid #ddd;" />',
                url
            )
        return format_html(
            '<div style="width: 40px; height: 40px; border-radius: 50%; '
            'background: #e0e0e0; display: flex; align-items: center; '
            'justify-content: center; color: #999; font-size: 12px;">👤</div>'
        )
    
    @admin.display(description=_('پیش‌نمایش آواتار'))
    def avatar_preview(self, obj):
        """نمایش تصویر آواتار بزرگتر در صفحه جزئیات"""
        url = obj.get_avatar_url()
        if url:
            return format_html(
                '<div style="text-align: center;">'
                '<img src="{}" style="width: 150px; height: 150px; '
                'border-radius: 50%; object-fit: cover; border: 3px solid #667eea; '
                'box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />'
                '</div>',
                url
            )
        return format_html(
            '<div style="width: 150px; height: 150px; border-radius: 50%; '
            'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
            'display: flex; align-items: center; justify-content: center; '
            'color: white; font-size: 48px; margin: 0 auto;">👤</div>'
        )
    
    @admin.display(description=_('تراکنش‌های کیف پول'))
    def wallet_transactions_display(self, obj):
        """نمایش تراکنش‌های اخیر کیف پول"""
        if not obj or not hasattr(obj, 'wallet'):
            return format_html('<p style="color: #999;">کیف پول وجود ندارد</p>')
        
        try:
            wallet = obj.wallet
            transactions = wallet.transactions.all().order_by('-created_at')[:10]
            
            if not transactions:
                return format_html('<p style="color: #999;">تراکنشی وجود ندارد</p>')
            
            # Build HTML table
            html = '<div style="margin-top: 10px;">'
            html += '<table style="width: 100%; border-collapse: collapse; font-size: 12px;">'
            html += '<thead><tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">'
            html += '<th style="padding: 8px; text-align: right;">شناسه</th>'
            html += '<th style="padding: 8px; text-align: right;">نوع</th>'
            html += '<th style="padding: 8px; text-align: right;">مبلغ</th>'
            html += '<th style="padding: 8px; text-align: right;">وضعیت</th>'
            html += '<th style="padding: 8px; text-align: right;">تاریخ</th>'
            html += '</tr></thead><tbody>'
            
            for txn in transactions:
                # Status colors
                status_colors = {
                    'pending': '#ffc107',
                    'completed': '#28a745',
                    'failed': '#dc3545',
                    'cancelled': '#6c757d',
                    'reversed': '#fd7e14',
                }
                status_color = status_colors.get(txn.status, '#6c757d')
                
                # Amount color
                amount_color = '#28a745' if txn.amount >= 0 else '#dc3545'
                amount_sign = '+' if txn.amount >= 0 else ''
                
                # Format date
                from django.utils import timezone
                import jdatetime
                created_jalali = jdatetime.datetime.fromgregorian(datetime=txn.created_at)
                date_str = created_jalali.strftime('%Y/%m/%d %H:%M')
                
                html += '<tr style="border-bottom: 1px solid #e9ecef;">'
                html += f'<td style="padding: 8px;"><code>{txn.transaction_id}</code></td>'
                html += f'<td style="padding: 8px;">{txn.get_transaction_type_display()}</td>'
                html += f'<td style="padding: 8px; font-weight: bold; color: {amount_color};">{amount_sign}{txn.amount:,} تومان</td>'
                html += f'<td style="padding: 8px;"><span style="background: {status_color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{txn.get_status_display()}</span></td>'
                html += f'<td style="padding: 8px; color: #6c757d;">{date_str}</td>'
                html += '</tr>'
            
            html += '</tbody></table>'
            
            # Add wallet balance info
            html += '<div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">'
            html += f'<strong>موجودی فعلی:</strong> <span style="color: #28a745; font-weight: bold;">{wallet.balance:,} تومان</span> | '
            html += f'<strong>اعتبار هدیه:</strong> <span style="color: #8a2be2; font-weight: bold;">{wallet.gift_balance:,} تومان</span>'
            html += '</div></div>'
            
            return format_html(html)
            
        except Exception as e:
            return format_html('<p style="color: #dc3545;">خطا در نمایش تراکنش‌ها: {}</p>', str(e))
    
    @admin.display(description=_('سبد خرید'))
    def cart_items_display(self, obj):
        """نمایش آیتم‌های سبد خرید کاربر"""
        if not obj or not hasattr(obj, 'cart'):
            return format_html('<p style="color: #999;">سبد خریدی وجود ندارد</p>')
        
        try:
            cart = obj.cart
            items = cart.items.select_related('product', 'variant').all()
            
            if not items:
                return format_html('<p style="color: #999;">سبد خرید خالی است</p>')
            
            # Build HTML table
            html = '<div style="margin-top: 10px;">'
            html += '<table style="width: 100%; border-collapse: collapse; font-size: 12px;">'
            html += '<thead><tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">'
            html += '<th style="padding: 8px; text-align: right;">محصول</th>'
            html += '<th style="padding: 8px; text-align: right;">نوع</th>'
            html += '<th style="padding: 8px; text-align: center;">تعداد</th>'
            html += '<th style="padding: 8px; text-align: right;">قیمت واحد</th>'
            html += '<th style="padding: 8px; text-align: right;">جمع</th>'
            html += '</tr></thead><tbody>'
            
            for item in items:
                variant_name = item.variant.name if item.variant else '-'
                unit_price = item.variant.final_price if item.variant else item.product.final_price
                line_total = unit_price * item.quantity
                
                html += '<tr style="border-bottom: 1px solid #e9ecef;">'
                html += f'<td style="padding: 8px;"><strong>{item.product.name}</strong></td>'
                html += f'<td style="padding: 8px; color: #6c757d;">{variant_name}</td>'
                html += f'<td style="padding: 8px; text-align: center;"><span style="background: #e9ecef; padding: 2px 8px; border-radius: 3px;">{item.quantity}</span></td>'
                html += f'<td style="padding: 8px;">{unit_price:,} تومان</td>'
                html += f'<td style="padding: 8px; font-weight: bold; color: #28a745;">{line_total:,} تومان</td>'
                html += '</tr>'
            
            html += '</tbody></table>'
            
            # Add cart total info
            html += '<div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px; text-align: left;">'
            html += f'<strong>تعداد کل آیتم‌ها:</strong> <span style="color: #007bff; font-weight: bold;">{cart.total_items}</span> | '
            html += f'<strong>جمع کل سبد:</strong> <span style="color: #28a745; font-weight: bold; font-size: 14px;">{cart.total:,} تومان</span>'
            html += '</div></div>'
            
            return format_html(html)
            
        except Exception as e:
            return format_html('<p style="color: #dc3545;">خطا در نمایش سبد خرید: {}</p>', str(e))
        
    def get_readonly_fields(self, request, obj=None):
        """فیلدهای فقط‌خواندنی بسته به وضعیت کاربر"""
        readonly = list(self.readonly_fields)
        if obj:
            # کاربر گوگل: تغییر auth_provider مجاز نیست
            if obj.auth_provider == User.AuthProvider.GOOGLE:
                readonly.extend(['auth_provider', 'email'])
        return readonly
    
    def save_model(self, request, obj, form, change):
        """ذخیره با اعتبارسنجی"""
        if not change:  # کاربر جدید
            if not obj.referral_code:
                obj.referral_code = obj._generate_referral_code()
        super().save_model(request, obj, form, change)

# ============================================
# Profile Admin (Inline + Standalone)
# ============================================
class ProfileInline(admin.StackedInline):
    """نمایش پروفایل به صورت Inline در User"""
    model = Profile
    can_delete = False
    verbose_name = _('پروفایل')
    verbose_name_plural = _('پروفایل')
        # این خط مهم است - از ایجاد خودکار جلوگیری می‌کند
    extra = 0
    min_num = 0
    max_num = 1
    # فقط برای کاربران موجود نمایش بده
    def has_add_permission(self, request, obj=None):
        """
        اگر کاربر قبلاً Profile دارد، اجازه اضافه کردن نده
        سیگنال خودکار Profile می‌سازد
        """
        if obj is not None:
            # کاربر موجود - چک کن Profile داره یا نه
            return not Profile.objects.filter(user=obj).exists()
        # کاربر جدید - سیگنال خودش می‌سازه
        return False
    fields = (
        'bio',
        'birth_date',
        'address',
        'city',
        'postal_code',
        'national_id',
    )


# ============================================
# Address Inline
# ============================================
class AddressInline(admin.TabularInline):
    """نمایش آدرس‌های کاربر به صورت Inline"""
    from .models import Address
    model = Address
    extra = 0
    fields = (
        'title',
        'recipient_name',
        'recipient_phone',
        'city',
        'postal_code',
        'is_default',
    )
    readonly_fields = ()
    can_delete = True
    verbose_name = _('آدرس')
    verbose_name_plural = _('آدرس‌های ارسال')


# ============================================
# BankCard Inline
# ============================================
class BankCardInline(admin.TabularInline):
    """نمایش کارت‌های بانکی کاربر به صورت Inline"""
    from .models import BankCard
    model = BankCard
    extra = 0
    fields = (
        'card_number_display',
        'bank_name',
        'is_default',
        'is_verified',
        'created_at',
    )
    readonly_fields = ('card_number_display', 'created_at')
    can_delete = True
    verbose_name = _('کارت بانکی')
    verbose_name_plural = _('کارت‌های بانکی')
    
    @admin.display(description=_('شماره کارت'))
    def card_number_display(self, obj):
        """نمایش شماره کارت با فرمت ماسک شده"""
        if obj and obj.card_number:
            return format_html(
                '<code style="background: #f0f0f0; padding: 2px 8px; '
                'border-radius: 4px; font-family: monospace; direction: ltr; display: inline-block;">{}</code>',
                obj.masked_number
            )
        return '-'


# ============================================
# Order Inline
# ============================================
class OrderInline(admin.TabularInline):
    """نمایش سفارشات کاربر به صورت Inline"""
    from apps.orders.models import Order
    model = Order
    extra = 0
    can_delete = False
    fields = (
        'order_number_link',
        'status_display',
        'total_amount_display',
        'created_at',
    )
    readonly_fields = ('order_number_link', 'status_display', 'total_amount_display', 'created_at')
    ordering = ['-created_at']
    verbose_name = _('سفارش')
    verbose_name_plural = _('سفارشات')
    
    @admin.display(description=_('شماره سفارش'))
    def order_number_link(self, obj):
        """لینک به صفحه سفارش"""
        if obj and obj.pk:
            from django.urls import reverse
            url = reverse('admin:orders_order_change', args=[obj.pk])
            return format_html(
                '<a href="{}" style="font-weight: bold; color: #0066cc;">{}</a>',
                url, obj.order_number
            )
        return '-'
    
    @admin.display(description=_('وضعیت'))
    def status_display(self, obj):
        """نمایش وضعیت با رنگ"""
        if not obj:
            return '-'
        
        status_colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'confirmed': '#28a745',
            'preparing': '#007bff',
            'shipped': '#6610f2',
            'delivered': '#20c997',
            'completed': '#28a745',
            'cancelled': '#dc3545',
            'refunded': '#fd7e14',
            'failed': '#dc3545',
        }
        
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    
    @admin.display(description=_('مبلغ کل'))
    def total_amount_display(self, obj):
        """نمایش مبلغ کل"""
        if obj and obj.total:
            return format_html(
                '<span style="font-weight: bold; color: #28a745;">{:,} تومان</span>',
                obj.total
            )
        return '-'


# ============================================
# CartItem Inline - Via Cart relationship
# ============================================
# Note: CartItem cannot be shown as inline directly since it relates to Cart, not User.
# To display cart items, we access them through the user's cart (user.cart.items)


# ============================================
# SupportTicket Inline - DISABLED (consulting app removed from INSTALLED_APPS)
# ============================================
# class SupportTicketInline(admin.TabularInline):
#     """نمایش تیکت‌های پشتیبانی کاربر به صورت Inline"""
#     from apps.consulting.models import SupportTicket
#     model = SupportTicket
#     extra = 0
#     can_delete = False
#     fk_name = 'user'  # Specify which FK to use (user vs assigned_to)
#     fields = (
#         'ticket_id_link',
#         'subject',
#         'status_display',
#         'message_count',
#         'created_at',
#     )
#     readonly_fields = ('ticket_id_link', 'subject', 'status_display', 'message_count', 'created_at')
#     ordering = ['-created_at']
#     verbose_name = _('تیکت پشتیبانی')
#     verbose_name_plural = _('تیکت‌های پشتیبانی')
#     
#     @admin.display(description=_('شماره تیکت'))
#     def ticket_id_link(self, obj):
#         """لینک به صفحه تیکت"""
#         if obj and obj.pk:
#             from django.urls import reverse
#             url = reverse('admin:consulting_supportticket_change', args=[obj.pk])
#             return format_html(
#                 '<a href="{}" style="font-weight: bold; color: #0066cc;">#{}</a>',
#                 url, obj.ticket_id
#             )
#         return '-'
#     
#     @admin.display(description=_('وضعیت'))
#     def status_display(self, obj):
#         """نمایش وضعیت با رنگ"""
#         if not obj:
#             return '-'
#         
#         status_colors = {
#             'pending': '#ffc107',
#             'in_progress': '#00f5ff',
#             'answered': '#28a745',
#             'closed': '#6c757d',
#         }
#         
#         color = status_colors.get(obj.status, '#6c757d')
#         return format_html(
#             '<span style="background: {}; color: white; padding: 3px 8px; '
#             'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
#             color, obj.get_status_display()
#         )

# ============================================
# WalletTransaction Inline
# ============================================
class WalletTransactionInline(admin.TabularInline):
    """نمایش تراکنش‌های کیف پول کاربر به صورت Inline"""
    from apps.wallet.models import WalletTransaction, Wallet
    model = WalletTransaction
    extra = 0
    can_delete = False
    fields = (
        'transaction_id',
        'transaction_type',
        'amount_display',
        'status_display',
        'created_at',
    )
    readonly_fields = ('transaction_id', 'transaction_type', 'amount_display', 'status_display', 'created_at')
    ordering = ['-created_at']
    verbose_name = _('تراکنش')
    verbose_name_plural = _('تراکنش‌های کیف پول')
    
    def get_queryset(self, request):
        """دریافت تراکنش‌ها از طریق wallet کاربر"""
        qs = super().get_queryset(request)
        return qs.select_related('wallet__user')
    
    def has_add_permission(self, request, obj=None):
        """غیرفعال کردن افزودن تراکنش از اینجا"""
        return False
    
    @admin.display(description=_('مبلغ'))
    def amount_display(self, obj):
        """نمایش مبلغ با رنگ"""
        if not obj:
            return '-'
        
        color = '#28a745' if obj.amount >= 0 else '#dc3545'
        sign = '+' if obj.amount >= 0 else ''
        return format_html(
            '<span style="font-weight: bold; color: {};">{}{:,} تومان</span>',
            color, sign, obj.amount
        )
    
    @admin.display(description=_('وضعیت'))
    def status_display(self, obj):
        """نمایش وضعیت با رنگ"""
        if not obj:
            return '-'
        
        status_colors = {
            'pending': '#ffc107',
            'completed': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#6c757d',
            'reversed': '#fd7e14',
        }
        
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )


UserAdmin.inlines = [
    ProfileInline, 
    AddressInline, 
    BankCardInline,
    OrderInline,
    # SupportTicketInline,  # Disabled - consulting app removed
]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """ادمین مستقل برای مدیریت پروفایل‌ها"""
    
    list_display = (
        'user',
        'get_user_phone',
        'get_user_email',
        'city',
        'birth_date',
    )
    
    list_filter = ('city',)
    
    search_fields = (
        'user__phone',
        'user__email',
        'user__first_name',
        'user__last_name',
        'national_id',
        'city',
    )
    
    raw_id_fields = ('user',)
    
    readonly_fields = ('user',)
    
    fieldsets = (
        (_('کاربر'), {
            'fields': ('user',),
        }),
        (_('اطلاعات شخصی'), {
            'fields': ('bio', 'birth_date', 'national_id'),
        }),
        (_('آدرس'), {
            'fields': ('address', 'city', 'postal_code'),
        }),
    )
    
    @admin.display(description=_('تلفن'))
    def get_user_phone(self, obj):
        return obj.user.phone or '-'
    
    @admin.display(description=_('ایمیل'))
    def get_user_email(self, obj):
        return obj.user.email or '-'



# ============================================
# OTP Admin
# ============================================
@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    """ادمین برای مدیریت کدهای یکبار مصرف"""
    
    list_display = (
        'phone',
        'code_display',
        'is_used',
        'is_expired_display',
        'created_at',
        'expires_at',
    )
    
    list_filter = (
        'is_used',
        'created_at',
    )
    
    search_fields = ('phone',)
    
    readonly_fields = ('created_at', 'code')
    
    ordering = ('-created_at',)
    
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('اطلاعات OTP'), {
            'fields': ('phone', 'code', 'is_used'),
        }),
        (_('زمان‌بندی'), {
            'fields': ('created_at', 'expires_at'),
        }),
    )
    
    @admin.display(description=_('کد'))
    def code_display(self, obj):
        """نمایش کد با فرمت خاص"""
        return format_html(
            '<code style="background: #f0f0f0; padding: 2px 8px; '
            'border-radius: 4px; font-family: monospace;">{}</code>',
            obj.code
        )
    
    @admin.display(description=_('منقضی شده؟'), boolean=True)
    def is_expired_display(self, obj):
        """نمایش وضعیت انقضا"""
        from django.utils import timezone
        return obj.expires_at < timezone.now()
    
    def has_add_permission(self, request):
        """OTP نباید دستی اضافه شود"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """فقط مشاهده و حذف"""
        return False


# ============================================
# تنظیمات عنوان پنل ادمین
# ============================================
admin.site.site_header = _('پنل مدیریت فروشگاه')
admin.site.site_title = _('مدیریت')
admin.site.index_title = _('داشبورد')