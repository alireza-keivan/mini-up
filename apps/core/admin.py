from django.contrib import admin
from .models import ServiceDescription, SocialMediaLinks, YouTubeVideo


@admin.register(SocialMediaLinks)
class SocialMediaLinksAdmin(admin.ModelAdmin):
    list_display = ('instagram', 'telegram', 'youtube', 'is_active', 'updated_at')
    fieldsets = (
        ('شبکه‌های اصلی', {
            'fields': ('instagram', 'telegram', 'youtube')
        }),
        ('شبکه‌های اضافی', {
            'fields': ('whatsapp', 'twitter'),
            'classes': ('collapse',)
        }),
        ('تنظیمات', {
            'fields': ('is_active',)
        }),
    )
    
    def has_add_permission(self, request):
        # فقط اجازه یک رکورد
        if SocialMediaLinks.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # اجازه حذف ندارد - فقط ویرایش
        return False


@admin.register(YouTubeVideo)
class YouTubeVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'video_preview', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    fieldsets = (
        ('اطلاعات ویدیو', {
            'fields': ('video_url', 'title', 'description')
        }),
        ('تنظیمات نمایش', {
            'fields': ('is_active',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def video_preview(self, obj):
        if obj.video_id:
            return f'Video ID: {obj.video_id}'
        return 'نامعتبر'
    video_preview.short_description = 'پیش‌نمایش'

    def has_add_permission(self, request):
        # فقط اجازه یک رکورد فعال
        if YouTubeVideo.objects.filter(is_active=True).exists():
            return True  # می‌تواند رکوردهای غیرفعال اضافه کند
        return super().has_add_permission(request)


@admin.register(ServiceDescription)
class ServiceDescriptionAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'title', 'is_active', 'updated_at')
    list_filter = ('service_type', 'is_active')
    search_fields = ('title', 'description')
    list_editable = ('is_active',)
    
    # برای محدود کردن به فقط ۴ رکورد
    def has_add_permission(self, request):
        # اگر ۴ رکورد وجود دارد، اجازه اضافه کردن نده
        if ServiceDescription.objects.count() >= 4:
            return False
        return super().has_add_permission(request)