from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django import forms
from .models import (
    Category, Brand, Product, ProductImage, 
    GameCurrencyRate, ProductReview, RecentlyViewed
)


# ============================================
# Custom Forms for Product Type Filtering
# ============================================
class VirtualProductForm(forms.ModelForm):
    """Form for virtual products with limited sub_type choices"""
    class Meta:
        model = Product
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit sub_type choices to virtual product options only
        if 'sub_type' in self.fields:
            self.fields['sub_type'].choices = [
                ('', '---------'),
                (Product.ProductSubType.VIRTUAL_SERVICE, 'خدمات مجازی'),
                (Product.ProductSubType.MINI_APP, 'مینی گیم'),
            ]
        # Add SKU validation help text
        if 'sku' in self.fields:
            self.fields['sku'].help_text = '⚠️ کد محصول باید دقیقاً 5 رقم باشد (مثال: 12345). اگر خالی بگذارید، به صورت خودکار تولید می‌شود.'


class PhysicalProductForm(forms.ModelForm):
    """Form for physical products with limited sub_type choices"""
    class Meta:
        model = Product
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit sub_type choices to physical product options only
        if 'sub_type' in self.fields:
            self.fields['sub_type'].choices = [
                ('', '---------'),
                (Product.ProductSubType.GAMING, 'خدمات گیمینگ'),
                (Product.ProductSubType.ACCESSORY, 'محصولات جانبی'),
            ]
        # Add SKU validation help text
        if 'sku' in self.fields:
            self.fields['sku'].help_text = '⚠️ کد محصول باید دقیقاً 5 رقم باشد (مثال: 12345). اگر خالی بگذارید، به صورت خودکار تولید می‌شود.'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'sort_order')
    list_filter = ('is_active', 'is_featured')
    search_fields = ('name', 'name_en', 'slug')
    prepopulated_fields = {'slug': ('name_en',)}
    list_editable = ('sort_order',)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


# ============================================
# Product Image Inline
# ============================================
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'sort_order', 'is_active')
    verbose_name = _('تصویر محصول')
    verbose_name_plural = _('تصاویر محصول')


# Inline for game currency rates (moved into Virtual products admin)
class GameCurrencyRateInline(admin.TabularInline):
    from .models import GameCurrencyRate
    model = GameCurrencyRate
    extra = 1
    fields = ('min_amount', 'max_amount', 'price_per_unit', 'unit_name', 'is_active')
    verbose_name = _('نرخ ارز بازی')
    verbose_name_plural = _('نرخ‌های ارز بازی')


# ============================================
# Base Product Admin (Not Registered - used as parent)
# ============================================
class BaseProductAdmin(admin.ModelAdmin):
    """Base admin class with common fields for all products"""
    
    list_filter = ('is_active', 'is_featured', 'is_new', 'is_bestseller', 'category')
    search_fields = ('name', 'name_en', 'slug', 'sku')
    prepopulated_fields = {'slug': ('name_en',)}
    inlines = [ProductImageInline]
    
    # Common fields for all products
    common_fields = (
        'sku',
        'name',
        'name_en',
        'slug',
        'short_description',
        'specifications',
        'price',
        'original_price',
        'main_image',
        'meta_title',
        'meta_description',
        'is_active',
        'is_featured',
        'is_new',
        'is_bestseller',
    )
    
    readonly_fields = ('view_count', 'sales_count', 'created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        """Override to validate and generate SKU"""
        from django.core.exceptions import ValidationError
        import random
        
        # If SKU is provided, validate it
        if obj.sku:
            # Remove any whitespace
            obj.sku = obj.sku.strip()
            
            # Check if it's exactly 5 digits
            if not obj.sku.isdigit() or len(obj.sku) != 5:
                from django.contrib import messages
                messages.error(request, 'کد محصول باید دقیقاً 5 رقم باشد')
                raise ValidationError('کد محصول باید دقیقاً 5 رقم باشد')
        else:
            # Generate a unique 5-digit SKU
            while True:
                sku = str(random.randint(10000, 99999))
                if not Product.objects.filter(sku=sku).exists():
                    obj.sku = sku
                    break
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Override in child classes to filter by product_type"""
        return super().get_queryset(request)


# ============================================
# Virtual Product Admin (خدمات مجازی)
# ============================================
class VirtualProductProxy(Product):
    """Proxy model for virtual products"""
    class Meta:
        proxy = True
        verbose_name = 'محصول مجازی'
        verbose_name_plural = 'محصولات مجازی'


@admin.register(VirtualProductProxy)
class VirtualProductAdmin(BaseProductAdmin):
    """Admin for virtual products (mini-games and virtual services)"""
    
    form = VirtualProductForm
    list_display = ('name', 'category', 'price', 'is_active', 'is_featured', 'sales_count')
    list_filter = ('is_active', 'is_featured', 'is_new', 'category')
    inlines = [ProductImageInline, GameCurrencyRateInline]
    
    fieldsets = (
        (_('اطلاعات پایه'), {
            'fields': ('sku', 'name', 'name_en', 'slug', 'category', 'sub_type')
        }),
        (_('توضیحات'), {
            'fields': ('short_description', 'description', 'specifications')
        }),
        (_('قیمت‌گذاری'), {
            'fields': ('price', 'original_price')
        }),
        (_('تصاویر'), {
            'fields': ('main_image',)
        }),
        (_('سئو'), {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        (_('وضعیت'), {
            'fields': ('is_active', 'is_featured', 'is_new', 'is_bestseller')
        }),
        (_('آمار'), {
            'fields': ('view_count', 'sales_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Only show virtual products"""
        return super().get_queryset(request).filter(product_type=Product.ProductType.VIRTUAL)
    
    def save_model(self, request, obj, form, change):
        """Ensure product_type is set to virtual"""
        obj.product_type = Product.ProductType.VIRTUAL
        # Virtual products don't track stock
        obj.track_stock = False
        obj.stock = 999999  # Unlimited
        # Ensure sub_type is valid for virtual products
        if obj.sub_type not in (Product.ProductSubType.VIRTUAL_SERVICE, Product.ProductSubType.MINI_APP):
            obj.sub_type = None
        super().save_model(request, obj, form, change)


# ============================================
# Physical Product Admin (محصولات فیزیکی)
# ============================================
class PhysicalProductProxy(Product):
    """Proxy model for physical products"""
    class Meta:
        proxy = True
        verbose_name = 'محصول فیزیکی'
        verbose_name_plural = 'محصولات فیزیکی'


@admin.register(PhysicalProductProxy)
class PhysicalProductAdmin(BaseProductAdmin):
    """Admin for physical products (gaming products and accessories)"""
    
    form = PhysicalProductForm
    list_display = ('name', 'category', 'brand', 'price', 'stock', 'stock_status', 'is_active', 'sales_count')
    list_filter = ('brand', 'is_active', 'is_featured', 'is_new', 'category', 'track_stock', 'sub_type')
    
    fieldsets = (
        (_('اطلاعات پایه'), {
            'fields': ('sku', 'name', 'name_en', 'slug', 'category', 'brand', 'sub_type')
        }),
        (_('توضیحات'), {
            'fields': ('short_description', 'description', 'specifications')
        }),
        (_('قیمت‌گذاری'), {
            'fields': ('price', 'original_price')
        }),
        (_('موجودی و انبار'), {
            'fields': ('stock', 'low_stock_threshold', 'track_stock'),
            'description': 'مدیریت موجودی محصولات فیزیکی'
        }),
        (_('مشخصات فیزیکی'), {
            'fields': ('weight', 'dimensions'),
            'description': 'برند، وزن و ابعاد محصول'
        }),
        (_('تصاویر'), {
            'fields': ('main_image',)
        }),
        (_('سئو'), {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        (_('وضعیت'), {
            'fields': ('is_active', 'is_featured', 'is_new', 'is_bestseller')
        }),
        (_('آمار'), {
            'fields': ('view_count', 'sales_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Only show physical products"""
        return super().get_queryset(request).filter(product_type=Product.ProductType.PHYSICAL)
    
    def save_model(self, request, obj, form, change):
        """Ensure product_type is set to physical"""
        obj.product_type = Product.ProductType.PHYSICAL
        obj.delivery_type = Product.DeliveryType.SHIPPING
        # Ensure sub_type is valid for physical products
        if obj.sub_type not in (Product.ProductSubType.ACCESSORY, Product.ProductSubType.GAMING):
            obj.sub_type = None
        super().save_model(request, obj, form, change)
    
    @admin.display(description=_('وضعیت موجودی'))
    def stock_status(self, obj):
        """Display stock status with color coding"""
        if not obj.track_stock:
            return format_html(
                '<span style="color: #999;">بدون پیگیری</span>'
            )
        if obj.stock == 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">ناموجود</span>'
            )
        elif obj.stock <= obj.low_stock_threshold:
            return format_html(
                '<span style="color: #ffc107; font-weight: bold;">کم موجود ({})</span>',
                obj.stock
            )
        else:
            return format_html(
                '<span style="color: #28a745;">موجود ({})</span>',
                obj.stock
            )

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_approved', 'submitted_at')
    list_filter = ('is_approved', 'rating')
    search_fields = ('product__name', 'user__phone', 'comment')

    @admin.display(description=_('زمان ارسال نظر'))
    def submitted_at(self, obj):
        return obj.created_at


@admin.register(RecentlyViewed)
class RecentlyViewedAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'viewed_at')
    list_filter = ('viewed_at',)
    readonly_fields = ('user', 'product', 'viewed_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
