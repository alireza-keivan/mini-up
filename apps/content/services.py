# apps/content/services.py

from django.db import transaction
from django.db.models import Q, Count, F
from django.utils import timezone
from django.core.cache import cache
from django.core.exceptions import ValidationError

from .models import (
    ArticleCategory, ArticleTag, Article, ArticleComment,
    Page, FAQItem, Testimonial, SystemNotification
)


# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class ArticleService:
    """
    سرویس مدیریت مقالات
    """
    
    # ─────────────────────────────────────────────────────────────────────────
    # READ OPERATIONS
    # ─────────────────────────────────────────────────────────────────────────
    
    @staticmethod
    def get_published_articles(category_slug=None, tag_slug=None, search=None):
        """
        دریافت لیست مقالات منتشر شده با فیلترها
        
        Args:
            category_slug: فیلتر دسته‌بندی
            tag_slug: فیلتر تگ
            search: جستجو در عنوان و محتوا
        
        Returns:
            QuerySet[Article]
        """
        queryset = Article.objects.filter(
            status=Article.Status.PUBLISHED,
            published_at__lte=timezone.now()
        ).select_related(
            'author', 'category'
        ).prefetch_related('tags')
        
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(excerpt__icontains=search) |
                Q(content__icontains=search)
            )
        
        return queryset.distinct()
    
    @staticmethod
    def get_article_by_slug(slug):
        """
        دریافت مقاله با slug
        
        Args:
            slug: نامک مقاله
        
        Returns:
            Article or None
        """
        try:
            return Article.objects.select_related(
                'author', 'category'
            ).prefetch_related('tags').get(
                slug=slug,
                status=Article.Status.PUBLISHED,
                published_at__lte=timezone.now()
            )
        except Article.DoesNotExist:
            return None
    
    @staticmethod
    def get_featured_articles(limit=5):
        """دریافت مقالات ویژه"""
        cache_key = f'featured_articles_{limit}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        articles = Article.objects.filter(
            status=Article.Status.PUBLISHED,
            is_featured=True,
            published_at__lte=timezone.now()
        ).select_related('author', 'category')[:limit]
        
        cache.set(cache_key, list(articles), 60 * 15)  # 15 minutes
        return articles
    
    @staticmethod
    def get_related_articles(article, limit=4):
        """دریافت مقالات مرتبط"""
        return Article.objects.filter(
            status=Article.Status.PUBLISHED,
            published_at__lte=timezone.now()
        ).filter(
            Q(category=article.category) |
            Q(tags__in=article.tags.all())
        ).exclude(
            pk=article.pk
        ).distinct()[:limit]
    
    @staticmethod
    def get_popular_articles(limit=5, days=30):
        """دریافت محبوب‌ترین مقالات بر اساس بازدید"""
        since = timezone.now() - timezone.timedelta(days=days)
        
        return Article.objects.filter(
            status=Article.Status.PUBLISHED,
            published_at__gte=since
        ).order_by('-view_count')[:limit]
    
    # ─────────────────────────────────────────────────────────────────────────
    # WRITE OPERATIONS
    # ─────────────────────────────────────────────────────────────────────────
    
    @staticmethod
    @transaction.atomic
    def increment_view_count(article):
        """افزایش تعداد بازدید (atomic)"""
        Article.objects.filter(pk=article.pk).update(
            view_count=F('view_count') + 1
        )
    
    @staticmethod
    @transaction.atomic
    def like_article(article, user):
        """
        لایک کردن مقاله
        (در صورت نیاز به جدول جداگانه لایک، اینجا اضافه کنید)
        """
        Article.objects.filter(pk=article.pk).update(
            like_count=F('like_count') + 1
        )
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# COMMENT SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class CommentService:
    """
    سرویس مدیریت کامنت‌ها
    """
    
    @staticmethod
    def get_article_comments(article):
        """دریافت کامنت‌های تایید شده به همراه پاسخ‌ها"""
        return (
            ArticleComment.objects
            .filter(article=article, status='approved', parent__isnull=True)
            .select_related('user')
            .prefetch_related('replies')
            .order_by('-created_at')
        )

    @staticmethod
    @transaction.atomic
    def create_comment(user, data):
        """
        ایجاد کامنت جدید (در صف تایید)
        Args:
            user: کاربر
            data: article, parent, content
        """
        article = data.get('article')

        if not article.allow_comments:
            raise ValidationError('کامنت‌گذاری برای این مقاله غیرفعال است.')

        parent = data.get('parent')
        if parent and parent.parent:
            raise ValidationError('پاسخ به پاسخ امکان‌پذیر نیست.')

        return ArticleComment.objects.create(
            article=article,
            parent=parent,
            user=user,
            content=data['content'],
            status='pending'
        )

    @staticmethod
    @transaction.atomic
    def like_comment(comment):
        """افزایش لایک کامنت"""
        ArticleComment.objects.filter(pk=comment.pk).update(
            like_count=F('like_count') + 1
        )
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class PageService:
    """
    سرویس مدیریت صفحات استاتیک
    """

    @staticmethod
    def get_page(slug):
        """دریافت صفحه از روی slug"""
        try:
            return Page.objects.get(slug=slug)
        except Page.DoesNotExist:
            return None

    @staticmethod
    def list_pages():
        """لیست صفحات به ترتیب نمایش"""
        return Page.objects.order_by('order')


# ═══════════════════════════════════════════════════════════════════════════════
# FAQ SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class FAQService:
    """
    سرویس سوالات متداول
    """

    @staticmethod
    def get_grouped_faq():
        """
        خروجی به صورت:
        [
            { "category": "پرداخت", "items": [...] },
            { "category": "سفارشات", "items": [...] },
        ]
        """
        categories = (
            FAQItem.objects.values_list('category', flat=True)
            .distinct().order_by('category')
        )

        result = []
        for category in categories:
            items = FAQItem.objects.filter(category=category).order_by('order')
            result.append({
                'category': category,
                'items': list(items)
            })

        return result


# ═══════════════════════════════════════════════════════════════════════════════
# TESTIMONIAL SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class TestimonialService:
    """
    سرویس نظرات مشتریان
    """

    @staticmethod
    def get_featured():
        """نظرات ویژه"""
        cache_key = 'featured_testimonials'
        cached = cache.get(cache_key)
        if cached:
            return cached

        items = Testimonial.objects.filter(is_featured=True).order_by('-created_at')[:10]
        cache.set(cache_key, list(items), 60 * 60)  # 1 hour
        return items

    @staticmethod
    def list_all():
        """تمام نظرات"""
        return Testimonial.objects.order_by('-created_at')


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATION SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class NotificationService:
    """
    سرویس اعلان‌ها
    """

    @staticmethod
    def list_unread(user):
        return SystemNotification.objects.filter(
            user=user,
            is_read=False
        ).order_by('-created_at')

    @staticmethod
    def list_all(user):
        return SystemNotification.objects.filter(
            user=user
        ).order_by('-created_at')

    @staticmethod
    @transaction.atomic
    def mark_as_read(user, notification_ids=None):
        """
        اگر notification_ids خالی باشد → همه را خوانده شده علامت بزن
        """
        queryset = SystemNotification.objects.filter(user=user, is_read=False)

        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)

        queryset.update(is_read=True, read_at=timezone.now())
        return queryset.count()