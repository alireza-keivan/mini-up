from django.contrib import admin
from .models import (
    Category, Brand, Product, ProductImage, 
    ProductVariant, DigitalInventory, GameCurrencyRate,
    ProductReview, RecentlyViewed
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'slug', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class DigitalInventoryInline(admin.TabularInline):
    model = DigitalInventory
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'product_type', 'price', 'stock', 'is_active', 'is_featured')
    list_filter = ('product_type', 'delivery_type', 'is_active', 'is_featured', 'category')
    search_fields = ('name', 'slug', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline, DigitalInventoryInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'price', 'stock', 'is_active')
    list_filter = ('is_active', 'product')
    search_fields = ('name', 'product__name')


@admin.register(DigitalInventory)
class DigitalInventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'created_at')
    list_filter = ('product',)
    search_fields = ('product__name',)


@admin.register(GameCurrencyRate)
class GameCurrencyRateAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_active')
    list_filter = ('is_active', 'product')


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating')
    search_fields = ('product__name', 'user__phone', 'comment')


@admin.register(RecentlyViewed)
class RecentlyViewedAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'viewed_at')
    list_filter = ('viewed_at',)
