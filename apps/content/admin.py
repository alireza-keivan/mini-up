# apps/content/admin.py

from django.contrib import admin
from .models import (
    ArticleCategory, ArticleTag, Article, ArticleImage, ArticleComment,
    Page, FAQItem, SystemNotification
)

@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "order")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ArticleTag)
class ArticleTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "article_count")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    
    @admin.display(description='تعداد مقالات')
    def article_count(self, obj):
        return obj.article_count


# Inline for article images
class ArticleImageInline(admin.TabularInline):
    model = ArticleImage
    extra = 1
    fields = ('image', 'alt_text', 'caption', 'order', 'is_active')
    verbose_name = 'تصویر'
    verbose_name_plural = 'تصاویر مقاله'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "status", "published_at", "is_featured")
    list_filter = ("status", "category", "is_featured")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    inlines = [ArticleImageInline]


@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    list_display = ("article", "user", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("content",)


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "order")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ("category", "question", "order")
    search_fields = ("question", "answer")
    list_filter = ("category",)


@admin.register(SystemNotification)
class SystemNotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("title", "message")
