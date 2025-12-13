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


UserAdmin.inlines = [ProfileInline, AddressInline, BankCardInline]


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