# apps/content/serializers.py

from rest_framework import serializers
from .models import (
    ArticleCategory, ArticleTag, Article, ArticleImage, ArticleComment,
    Page, FAQItem, SystemNotification
)


# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE CATEGORY SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class ArticleCategoryListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست دسته‌بندی‌ها"""
    article_count = serializers.ReadOnlyField()
    
    class Meta:
        model = ArticleCategory
        fields = [
            'id', 'name', 'slug', 'icon', 'image',
            'article_count', 'order'
        ]


class ArticleCategoryDetailSerializer(serializers.ModelSerializer):
    """سریالایزر جزئیات دسته‌بندی"""
    article_count = serializers.ReadOnlyField()
    children = ArticleCategoryListSerializer(many=True, read_only=True)
    parent = ArticleCategoryListSerializer(read_only=True)
    
    class Meta:
        model = ArticleCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'image',
            'parent', 'children', 'article_count',
            'meta_title', 'meta_description',
            'order', 'created_at'
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE TAG SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class ArticleTagSerializer(serializers.ModelSerializer):
    """سریالایزر تگ‌ها"""
    class Meta:
        model = ArticleTag
        fields = ['id', 'name', 'slug']


# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class ArticleImageSerializer(serializers.ModelSerializer):
    """سریالایزر تصاویر مقاله"""
    class Meta:
        model = ArticleImage
        fields = ['id', 'image', 'alt_text', 'caption', 'order']


class ArticleAuthorSerializer(serializers.Serializer):
    """سریالایزر نویسنده مقاله"""
    id = serializers.UUIDField()
    full_name = serializers.CharField()
    avatar = serializers.ImageField(source='avatar', allow_null=True)


class ArticleListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست مقالات"""
    author = ArticleAuthorSerializer(read_only=True)
    category = ArticleCategoryListSerializer(read_only=True)
    tags = ArticleTagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'excerpt',
            'featured_image', 'featured_image_alt',
            'author', 'category', 'tags',
            'reading_time', 'view_count',
            'is_featured', 'is_pinned',
            'published_at', 'created_at'
        ]


class ArticleDetailSerializer(serializers.ModelSerializer):
    """سریالایزر جزئیات مقاله"""
    author = ArticleAuthorSerializer(read_only=True)
    category = ArticleCategoryDetailSerializer(read_only=True)
    tags = ArticleTagSerializer(many=True, read_only=True)
    images = ArticleImageSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'excerpt', 'content',
            'featured_image', 'featured_image_alt',
            'images',
            'author', 'category', 'tags',
            'reading_time', 'view_count',
            'allow_comments', 'comment_count',
            'is_featured', 'is_pinned',
            'meta_title', 'meta_description', 'meta_keywords', 'canonical_url',
            'published_at', 'created_at', 'updated_at'
        ]
    
    def get_comment_count(self, obj):
        return obj.comments.filter(status='approved').count()


class ArticleMinimalSerializer(serializers.ModelSerializer):
    """سریالایزر کوتاه برای مقالات مرتبط"""
    class Meta:
        model = Article
        fields = ['id', 'title', 'slug', 'featured_image', 'published_at']


# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE COMMENT SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class CommentUserSerializer(serializers.Serializer):
    """سریالایزر کاربر کامنت"""
    id = serializers.UUIDField()
    full_name = serializers.CharField()
    avatar = serializers.ImageField(allow_null=True)


class ArticleCommentSerializer(serializers.ModelSerializer):
    """سریالایزر کامنت‌ها"""
    user = CommentUserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = ArticleComment
        fields = [
            'id', 'user', 'content', 'like_count',
            'parent', 'replies',
            'created_at'
        ]
    
    def get_replies(self, obj):
        if obj.parent is None:  # فقط برای کامنت‌های اصلی
            replies = obj.replies.filter(status='approved')
            return ArticleCommentSerializer(replies, many=True).data
        return []


class ArticleCommentCreateSerializer(serializers.ModelSerializer):
    """سریالایزر ایجاد کامنت"""
    class Meta:
        model = ArticleComment
        fields = ['article', 'parent', 'content']
    
    def validate_parent(self, value):
        if value and value.parent is not None:
            raise serializers.ValidationError('پاسخ به پاسخ امکان‌پذیر نیست.')
        return value
    
    def validate(self, data):
        # بررسی مجاز بودن کامنت در مقاله
        if not data['article'].allow_comments:
            raise serializers.ValidationError('کامنت‌گذاری در این مقاله غیرفعال است.')
        return data


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class PageListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست صفحات"""
    class Meta:
        model = Page
        fields = ['id', 'title', 'slug', 'order']


class PageDetailSerializer(serializers.ModelSerializer):
    """سریالایزر جزئیات صفحه"""
    class Meta:
        model = Page
        fields = [
            'id', 'title', 'slug', 'content', 'featured_image',
            'meta_title', 'meta_description',
            'created_at', 'updated_at'
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# FAQ SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class FAQItemSerializer(serializers.ModelSerializer):
    """سریالایزر سوالات متداول"""
    class Meta:
        model = FAQItem
        fields = ['id', 'question', 'answer', 'category', 'order']


class FAQGroupedSerializer(serializers.Serializer):
    """سریالایزر FAQ گروه‌بندی شده"""
    category = serializers.CharField()
    items = FAQItemSerializer(many=True)


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATION SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════

class SystemNotificationSerializer(serializers.ModelSerializer):
    """سریالایزر اعلان‌ها"""
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = SystemNotification
        fields = [
            'id', 'title', 'message', 'type',
            'is_read', 'read_at', 'is_expired',
            'created_at'
        ]


class NotificationMarkReadSerializer(serializers.Serializer):
    """سریالایزر برای علامت‌گذاری خوانده شده"""
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text='لیست شناسه اعلان‌ها (خالی = همه)'
    )
