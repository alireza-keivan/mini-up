# apps/consulting/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    ConsultingCategory,
    SupportTicket,
    TicketMessage,
    TicketAttachment
)


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

@admin.register(ConsultingCategory)
class ConsultingCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'is_active', 'ticket_count_display', 'order']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    
    @admin.display(description='تعداد تیکت‌ها')
    def ticket_count_display(self, obj):
        count = obj.ticket_count
        if count > 0:
            return format_html('<strong style="color: #28a745;">{}</strong>', count)
        return count


# ═══════════════════════════════════════════════════════════════════════════════
# TICKET MESSAGE INLINE
# ═══════════════════════════════════════════════════════════════════════════════

class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0
    fields = ['file', 'file_size_display', 'uploaded_at']
    readonly_fields = ['file_size_display', 'uploaded_at']
    can_delete = True
    
    @admin.display(description='حجم فایل')
    def file_size_display(self, obj):
        if obj.file_size:
            return f'{obj.file_size_mb} MB'
        return '-'


class TicketMessageInline(admin.StackedInline):
    model = TicketMessage
    extra = 0
    fields = ['sender', 'message', 'is_staff_reply', 'is_read', 'created_at']
    readonly_fields = ['sender', 'created_at']
    can_delete = False
    ordering = ['created_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('sender').prefetch_related('attachments')


# ═══════════════════════════════════════════════════════════════════════════════
# SUPPORT TICKET ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = [
        'ticket_id_display',
        'subject',
        'user_display',
        'category',
        'status_display',
        'priority_display',
        'message_count',
        'created_at',
        'last_response_at'
    ]
    list_filter = ['status', 'priority', 'category', 'created_at']
    search_fields = ['ticket_id', 'subject', 'user__phone', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = [
        'ticket_id',
        'created_at',
        'updated_at',
        'last_response_at',
        'closed_at',
        'message_count',
        'response_time_display'
    ]
    
    fieldsets = (
        ('اطلاعات تیکت', {
            'fields': ('ticket_id', 'user', 'category', 'subject', 'initial_message')
        }),
        ('وضعیت', {
            'fields': ('status', 'priority', 'assigned_to')
        }),
        ('آمار و زمان‌بندی', {
            'fields': (
                'message_count',
                'response_time_display',
                'created_at',
                'last_response_at',
                'closed_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TicketMessageInline]
    
    actions = ['close_tickets', 'reopen_tickets', 'mark_as_in_progress']
    
    @admin.display(description='شماره تیکت')
    def ticket_id_display(self, obj):
        return format_html(
            '<strong style="font-family: monospace; color: #007bff;">{}</strong>',
            obj.ticket_id
        )
    
    @admin.display(description='کاربر')
    def user_display(self, obj):
        user_name = obj.user.get_full_name() or obj.user.phone
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:accounts_user_change', args=[obj.user.id]),
            user_name
        )
    
    @admin.display(description='وضعیت')
    def status_display(self, obj):
        status_colors = {
            'pending': '#ffc107',
            'in_progress': '#17a2b8',
            'answered': '#28a745',
            'closed': '#6c757d'
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    @admin.display(description='اولویت')
    def priority_display(self, obj):
        priority_colors = {
            'low': '#6c757d',
            'medium': '#17a2b8',
            'high': '#ffc107',
            'urgent': '#dc3545'
        }
        color = priority_colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    
    @admin.display(description='زمان پاسخ')
    def response_time_display(self, obj):
        response_time = obj.response_time
        if response_time:
            total_seconds = int(response_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if hours > 0:
                return f'{hours} ساعت و {minutes} دقیقه'
            return f'{minutes} دقیقه'
        return 'هنوز پاسخ داده نشده'
    
    @admin.action(description='بستن تیکت‌های انتخاب شده')
    def close_tickets(self, request, queryset):
        count = 0
        for ticket in queryset:
            if not ticket.is_closed:
                ticket.close()
                count += 1
        self.message_user(request, f'{count} تیکت بسته شد.')
    
    @admin.action(description='بازگشایی تیکت‌های انتخاب شده')
    def reopen_tickets(self, request, queryset):
        count = 0
        for ticket in queryset:
            if ticket.is_closed:
                ticket.reopen()
                count += 1
        self.message_user(request, f'{count} تیکت بازگشایی شد.')
    
    @admin.action(description='علامت‌گذاری به عنوان "در حال بررسی"')
    def mark_as_in_progress(self, request, queryset):
        count = queryset.update(status='in_progress')
        self.message_user(request, f'{count} تیکت به وضعیت "در حال بررسی" تغییر کرد.')


# ═══════════════════════════════════════════════════════════════════════════════
# TICKET MESSAGE ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = [
        'ticket_link',
        'sender_display',
        'message_preview',
        'is_staff_reply',
        'is_read',
        'has_attachments',
        'created_at'
    ]
    list_filter = ['is_staff_reply', 'is_read', 'created_at']
    search_fields = ['ticket__ticket_id', 'sender__phone', 'sender__email', 'message']
    readonly_fields = ['ticket', 'sender', 'created_at', 'read_at']
    
    fieldsets = (
        ('اطلاعات پیام', {
            'fields': ('ticket', 'sender', 'message', 'is_staff_reply')
        }),
        ('وضعیت خواندن', {
            'fields': ('is_read', 'read_at', 'created_at')
        }),
    )
    
    inlines = [TicketAttachmentInline]
    
    @admin.display(description='تیکت')
    def ticket_link(self, obj):
        url = reverse('admin:consulting_supportticket_change', args=[obj.ticket.id])
        return format_html(
            '<a href="{}">#{}</a>',
            url,
            obj.ticket.ticket_id
        )
    
    @admin.display(description='فرستنده')
    def sender_display(self, obj):
        if obj.is_staff_reply:
            return format_html('<strong style="color: #007bff;">پشتیبان</strong>')
        return obj.sender.get_full_name() or obj.sender.phone
    
    @admin.display(description='پیش‌نمایش پیام')
    def message_preview(self, obj):
        preview = obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
        return preview
    
    @admin.display(description='فایل ضمیمه', boolean=True)
    def has_attachments(self, obj):
        return obj.attachments.exists()


# ═══════════════════════════════════════════════════════════════════════════════
# TICKET ATTACHMENT ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'ticket_link',
        'file_preview',
        'file_size_display',
        'uploaded_at'
    ]
    list_filter = ['uploaded_at']
    search_fields = ['message__ticket__ticket_id', 'original_filename']
    readonly_fields = ['file_size', 'original_filename', 'uploaded_at', 'file_preview_large']
    
    fieldsets = (
        ('اطلاعات فایل', {
            'fields': ('message', 'file', 'file_preview_large', 'original_filename', 'file_size', 'uploaded_at')
        }),
    )
    
    @admin.display(description='تیکت')
    def ticket_link(self, obj):
        url = reverse('admin:consulting_supportticket_change', args=[obj.message.ticket.id])
        return format_html(
            '<a href="{}">#{}</a>',
            url,
            obj.message.ticket.ticket_id
        )
    
    @admin.display(description='پیش‌نمایش')
    def file_preview(self, obj):
        if obj.file:
            return format_html(
                '<img src="{}" style="max-width: 50px; max-height: 50px; object-fit: cover;" />',
                obj.file.url
            )
        return '-'
    
    @admin.display(description='تصویر')
    def file_preview_large(self, obj):
        if obj.file:
            return format_html(
                '<img src="{}" style="max-width: 400px; border-radius: 5px;" />',
                obj.file.url
            )
        return '-'
    
    @admin.display(description='حجم فایل')
    def file_size_display(self, obj):
        return f'{obj.file_size_mb} MB'
