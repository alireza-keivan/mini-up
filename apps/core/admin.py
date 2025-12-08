from django.contrib import admin
from .models import ServiceDescription


@admin.register(ServiceDescription)
class ServiceDescriptionAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'title', 'is_active', 'updated_at')
    list_filter = ('service_type', 'is_active')
    search_fields = ('title', 'description')
    list_editable = ('is_active',)
    
    # برای محدود کردن به فقط ۴ رکورد
    def has_add_permission(self, request):
        # اگر ۴ رکورد وجود دارد، اجازه ضافه کردن نده
        if ServiceDescription.objects.count() >= 4:
            return False
        return super().has_add_permission(request)