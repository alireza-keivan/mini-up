# apps/consulting/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg

from .models import (
    ConsultingCategory,
    Consultant,
    TimeSlot,
    Appointment,
    ConsultantReview
)


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

@admin.register(ConsultingCategory)
class ConsultingCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'is_active', 'consultant_count', 'order']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    
    def consultant_count(self, obj):
        return obj.consultants.filter(is_active=True).count()
    consultant_count.short_description = 'تعداد مشاوران'


# ═══════════════════════════════════════════════════════════════════════════════
# CONSULTANT ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

class TimeSlotInline(admin.TabularInline):
    model = TimeSlot
    extra = 0
    fields = ['date', 'start_time', 'end_time', 'duration', 'status', 'custom_price']
    readonly_fields = []
    ordering = ['date', 'start_time']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status='available')[:20]


@admin.register(Consultant)
class ConsultantAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'phone', 'title', 'rating_display',
        'price_per_minute', 'is_online', 'is_verified', 'is_active'
    ]
    list_filter = ['is_active', 'is_verified', 'is_online', 'categories']
    list_editable = ['is_online', 'is_verified', 'is_active']
    search_fields = ['user__phone', 'user__first_name', 'user__last_name', 'title']
    filter_horizontal = ['categories']
    readonly_fields = ['rating', 'review_count', 'total_sessions', 'total_hours', 'created_at']
    inlines = [TimeSlotInline]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('user', 'title', 'bio', 'categories')
        }),
        ('تصاویر', {
            'fields': ('profile_image', 'cover_image'),
            'classes': ('collapse',)
        }),
        ('قیمت‌گذاری', {
            'fields': (
                'price_per_minute',
                ('min_session_duration', 'max_session_duration'),
            )
        }),
        ('سوابق', {
            'fields': ('experience_years', 'education', 'certifications'),
            'classes': ('collapse',)
        }),
        ('آمار', {
            'fields': ('rating', 'review_count', 'total_sessions', 'total_hours'),
        }),
        ('وضعیت', {
            'fields': ('is_active', 'is_verified', 'is_online', 'is_available')
        }),
    )
    
    def display_name(self, obj):
        return obj.display_name
    display_name.short_description = 'نام'
    
    def phone(self, obj):
        return obj.user.phone
    phone.short_description = 'موبایل'
    
    def rating_display(self, obj):
        if obj.rating:
            stars = '★' * int(obj.rating) + '☆' * (5 - int(obj.rating))
            return format_html(
                '<span style="color: #f59e0b;">{}</span> <small>({})</small>',
                stars,
                obj.review_count
            )
        return '-'
    rating_display.short_description = 'امتیاز'


# ═══════════════════════════════════════════════════════════════════════════════
# TIME SLOT ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['consultant', 'date', 'start_time', 'end_time', 'duration', 'status', 'price']
    list_filter = ['status', 'date', 'consultant']
    list_editable = ['status']
    search_fields = ['consultant__user__phone', 'consultant__user__first_name']
    date_hierarchy = 'date'
    ordering = ['-date', 'start_time']
    
    def price(self, obj):
        return f"{obj.price:,} تومان"
    price.short_description = 'قیمت'


# ═══════════════════════════════════════════════════════════════════════════════
# APPOINTMENT ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'id_short', 'user_phone', 'consultant_name', 'slot_info',
        'status_badge', 'price_display', 'has_review', 'created_at'
    ]
    list_filter = ['status', 'has_review', 'created_at', 'consultant']
    search_fields = [
        'user__phone', 'user__first_name',
        'consultant__user__phone', 'consultant__user__first_name',
        'id'
    ]
    readonly_fields = [
        'id', 'user', 'consultant', 'slot', 'price',
        'payment_transaction', 'session_link',
        'started_at', 'finished_at', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    raw_id_fields = ['user', 'consultant', 'slot', 'payment_transaction']
    
    fieldsets = (
        ('اطلاعات نوبت', {
            'fields': ('id', 'user', 'consultant', 'slot', 'description')
        }),
        ('پرداخت', {
            'fields': ('price', 'payment_transaction')
        }),
        ('وضعیت', {
            'fields': ('status', 'has_review')
        }),
        ('جلسه', {
            'fields': ('session_link', 'started_at', 'finished_at'),
            'classes': ('collapse',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_cancelled']
    
    def id_short(self, obj):
        """نمایش کوتاه UUID"""
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'شناسه'
    
    def user_phone(self, obj):
        return obj.user.phone
    user_phone.short_description = 'کاربر'
    user_phone.admin_order_field = 'user__phone'
    
    def consultant_name(self, obj):
        return obj.consultant.display_name
    consultant_name.short_description = 'مشاور'
    
    def slot_info(self, obj):
        if obj.slot:
            return format_html(
                '{}<br><small>{} - {}</small>',
                obj.slot.date,
                obj.slot.start_time.strftime('%H:%M'),
                obj.slot.end_time.strftime('%H:%M')
            )
        return '-'
    slot_info.short_description = 'زمان'
    
    def status_badge(self, obj):
        """نمایش وضعیت با رنگ"""
        colors = {
            'pending': '#f59e0b',      # زرد - در انتظار پرداخت
            'waiting': '#3b82f6',      # آبی - در انتظار جلسه
            'in_progress': '#8b5cf6',  # بنفش - در حال برگزاری
            'completed': '#10b981',    # سبز - تکمیل شده
            'cancelled': '#ef4444',    # قرمز - لغو شده
        }
        labels = {
            'pending': 'در انتظار پرداخت',
            'waiting': 'در انتظار جلسه',
            'in_progress': 'در حال برگزاری',
            'completed': 'تکمیل شده',
            'cancelled': 'لغو شده',
        }
        color = colors.get(obj.status, '#6b7280')
        label = labels.get(obj.status, obj.status)
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color, label
        )
    status_badge.short_description = 'وضعیت'
    
    def price_display(self, obj):
        return format_html(
            '<span style="color: #10b981; font-weight: bold;">{:,}</span>',
            obj.price
        )
    price_display.short_description = 'مبلغ (تومان)'
    
    # ─────────────────────────────────────────────────────────────
    # ADMIN ACTIONS
    # ─────────────────────────────────────────────────────────────
    
    @admin.action(description='تکمیل شده')
    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status='in_progress').update(status='completed')
        self.message_user(request, f'{updated} نوبت به تکمیل شده تغییر یافت.')
    
    @admin.action(description='لغو شده')
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.exclude(status__in=['completed', 'cancelled']).update(status='cancelled')
        self.message_user(request, f'{updated} نوبت لغو شد.')


# ═══════════════════════════════════════════════════════════════════════════════
# REVIEW ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

@admin.register(ConsultantReview)
class ConsultantReviewAdmin(admin.ModelAdmin):
    list_display = [
        'id_short', 'consultant_name', 'user_phone', 'rating_stars',
        'comment_preview', 'is_approved', 'created_at'
    ]
    list_filter = ['is_approved', 'rating', 'created_at', 'consultant']
    list_editable = ['is_approved']
    search_fields = [
        'comment', 'user__phone', 'user__first_name',
        'consultant__user__first_name'
    ]
    readonly_fields = ['appointment', 'consultant', 'user', 'rating', 'created_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    raw_id_fields = ['appointment', 'consultant', 'user']
    
    fieldsets = (
        ('اطلاعات نظر', {
            'fields': ('appointment', 'consultant', 'user')
        }),
        ('محتوا', {
            'fields': ('rating', 'comment')
        }),
        ('وضعیت', {
            'fields': ('is_approved',)
        }),
        ('تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_reviews', 'reject_reviews']
    
    def id_short(self, obj):
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'شناسه'
    
    def consultant_name(self, obj):
        return obj.consultant.display_name
    consultant_name.short_description = 'مشاور'
    
    def user_phone(self, obj):
        return obj.user.phone
    user_phone.short_description = 'کاربر'
    
    def rating_stars(self, obj):
        """نمایش ستاره‌ای امتیاز"""
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        color = '#10b981' if obj.rating >= 4 else '#f59e0b' if obj.rating >= 3 else '#ef4444'
        return format_html(
            '<span style="color: {}; font-size: 14px;">{}</span>',
            color, stars
        )
    rating_stars.short_description = 'امتیاز'
    
    def comment_preview(self, obj):
        """پیش‌نمایش کوتاه نظر"""
        if obj.comment:
            text = obj.comment[:50]
            if len(obj.comment) > 50:
                text += '...'
            return text
        return '-'
    comment_preview.short_description = 'نظر'
    
    # ─────────────────────────────────────────────────────────────
    # ADMIN ACTIONS
    # ─────────────────────────────────────────────────────────────
    
    @admin.action(description='تأیید نظرات انتخاب شده')
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} نظر تأیید شد.')
    
    @admin.action(description='رد نظرات انتخاب شده')
    def reject_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} نظر رد شد.')
