# apps/content/api_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import (
    ArticleCategory, ArticleTag, Article, ArticleComment,
    Page, FAQItem, SystemNotification
)
from .services import (
    ArticleService, CommentService, PageService,
    FAQService, NotificationService
)
from .serializers import (
    ArticleCategoryListSerializer, ArticleCategoryDetailSerializer,
    ArticleTagSerializer,
    ArticleListSerializer, ArticleDetailSerializer, ArticleMinimalSerializer,
    ArticleCommentSerializer, ArticleCommentCreateSerializer,
    PageListSerializer, PageDetailSerializer,
    FAQItemSerializer, FAQGroupedSerializer,
    SystemNotificationSerializer, NotificationMarkReadSerializer
)


# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE CATEGORY APIs
# ═══════════════════════════════════════════════════════════════════════════════

class ArticleCategoryListAPIView(APIView):
    """
    لیست دسته‌بندی‌های مقالات
    GET /content/api/v1/categories/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        categories = ArticleCategory.objects.filter(
            parent__isnull=True
        ).prefetch_related('children').order_by('order')

        serializer = ArticleCategoryListSerializer(categories, many=True)

        return Response({
            'success': True,
            'data': serializer.data
        })


class ArticleCategoryDetailAPIView(APIView):
    """
    جزئیات دسته‌بندی + مقالات آن
    GET /content/api/v1/categories/<slug>/
    """
    permission_classes = [AllowAny]

    def get(self, request, slug):
        category = get_object_or_404(ArticleCategory, slug=slug)
        
        # مقالات این دسته‌بندی
        articles = ArticleService.get_published_articles(category_slug=slug)

        return Response({
            'success': True,
            'data': {
                'category': ArticleCategoryDetailSerializer(category).data,
                'articles': ArticleListSerializer(articles[:20], many=True).data
            }
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE TAG APIs
# ═══════════════════════════════════════════════════════════════════════════════

class ArticleTagListAPIView(APIView):
    """
    لیست تگ‌ها
    GET /content/api/v1/tags/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        tags = ArticleTag.objects.all().order_by('name')
        serializer = ArticleTagSerializer(tags, many=True)

        return Response({
            'success': True,
            'data': serializer.data
        })


class ArticleTagDetailAPIView(APIView):
    """
    مقالات یک تگ خاص
    GET /content/api/v1/tags/<slug>/
    """
    permission_classes = [AllowAny]

    def get(self, request, slug):
        tag = get_object_or_404(ArticleTag, slug=slug)
        articles = ArticleService.get_published_articles(tag_slug=slug)

        return Response({
            'success': True,
            'data': {
                'tag': ArticleTagSerializer(tag).data,
                'articles': ArticleListSerializer(articles[:20], many=True).data
            }
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE APIs
# ═══════════════════════════════════════════════════════════════════════════════

class ArticleListAPIView(APIView):
    """
    لیست مقالات
    GET /content/api/v1/articles/

    Query Params:
        - category: slug دسته‌بندی
        - tag: slug تگ
        - search: جستجو
        - limit: تعداد (پیش‌فرض 20)
        - offset: شروع از
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # فیلترها
        category_slug = request.query_params.get('category')
        tag_slug = request.query_params.get('tag')
        search = request.query_params.get('search')
        limit = min(int(request.query_params.get('limit', 20)), 50)
        offset = int(request.query_params.get('offset', 0))

        # دریافت مقالات
        articles = ArticleService.get_published_articles(
            category_slug=category_slug,
            tag_slug=tag_slug,
            search=search
        ).order_by('-is_pinned', '-published_at')[offset:offset + limit]

        serializer = ArticleListSerializer(articles, many=True)

        return Response({
            'success': True,
            'count': len(serializer.data),
            'data': serializer.data
        })


class ArticleDetailAPIView(APIView):
    """
    جزئیات مقاله
    GET /content/api/v1/articles/<slug>/
    """
    permission_classes = [AllowAny]

    def get(self, request, slug):
        article = ArticleService.get_article_by_slug(slug)

        if not article:
            return Response({
                'success': False,
                'error': 'مقاله یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)

        # افزایش بازدید
        ArticleService.increment_view_count(article)

        # مقالات مرتبط
        related = ArticleService.get_related_articles(article, limit=4)

        return Response({
            'success': True,
            'data': {
                'article': ArticleDetailSerializer(article).data,
                'related_articles': ArticleMinimalSerializer(related, many=True).data
            }
        })


class ArticleFeaturedAPIView(APIView):
    """
    مقالات ویژه
    GET /content/api/v1/articles/featured/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 5))
        articles = ArticleService.get_featured_articles(limit=limit)
        serializer = ArticleListSerializer(articles, many=True)

        return Response({
            'success': True,
            'data': serializer.data
        })


class ArticlePopularAPIView(APIView):
    """
    محبوب‌ترین مقالات
    GET /content/api/v1/articles/popular/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 5))
        days = int(request.query_params.get('days', 30))
        
        articles = ArticleService.get_popular_articles(limit=limit, days=days)
        serializer = ArticleListSerializer(articles, many=True)

        return Response({
            'success': True,
            'data': serializer.data
        })


class ArticleLikeAPIView(APIView):
    """
    لایک مقاله
    POST /content/api/v1/articles/<slug>/like/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        article = ArticleService.get_article_by_slug(slug)

        if not article:
            return Response({
                'success': False,
                'error': 'مقاله یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)

        ArticleService.like_article(article, request.user)

        return Response({
            'success': True,
            'message': 'لایک ثبت شد',
            'data': {
                'like_count': article.like_count + 1
            }
        })


# ═══════════════════════════════════════════════════════════════════════════════
# COMMENT APIs
# ═══════════════════════════════════════════════════════════════════════════════

class ArticleCommentsAPIView(APIView):
    """
    کامنت‌های یک مقاله
    GET /content/api/v1/articles/<slug>/comments/
    """
    permission_classes = [AllowAny]

    def get(self, request, slug):
        article = get_object_or_404(Article, slug=slug)
        comments = CommentService.get_article_comments(article)
        serializer = ArticleCommentSerializer(comments, many=True)

        return Response({
            'success': True,
            'data': serializer.data
        })


class ArticleCommentCreateAPIView(APIView):
    """
    ارسال کامنت جدید
    POST /content/api/v1/articles/<slug>/comments/

    Body:
        - content: متن کامنت
        - parent: شناسه کامنت والد (اختیاری - برای پاسخ)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        article = get_object_or_404(Article, slug=slug)

        data = {
            'article': article,
            'parent': None,
            'content': request.data.get('content', '').strip()
        }

        # بررسی پاسخ
        parent_id = request.data.get('parent')
        if parent_id:
            data['parent'] = get_object_or_404(ArticleComment, pk=parent_id, article=article)

        # اعتبارسنجی
        if not data['content']:
            return Response({
                'success': False,
                'error': 'متن کامنت الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(data['content']) < 10:
            return Response({
                'success': False,
                'error': 'کامنت باید حداقل ۱۰ کاراکتر باشد'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = CommentService.create_comment(request.user, data)

            return Response({
                'success': True,
                'message': 'کامنت شما ثبت شد و پس از تایید نمایش داده می‌شود',
                'data': ArticleCommentSerializer(comment).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CommentLikeAPIView(APIView):
    """
    لایک کامنت
    POST /content/api/v1/comments/<pk>/like/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        comment = get_object_or_404(ArticleComment, pk=pk, status='approved')
        CommentService.like_comment(comment)

        return Response({
            'success': True,
            'message': 'لایک ثبت شد'
        })


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE APIs
# ═══════════════════════════════════════════════════════════════════════════════

class PageListAPIView(APIView):
    """
    لیست صفحات استاتیک
    GET /content/api/v1/pages/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        pages = PageService.list_pages()
        serializer = PageListSerializer(pages, many=True)

        return Response({
            'success': True,
            'data': serializer.data
        })


class PageDetailAPIView(APIView):
    """
    جزئیات صفحه
    GET /content/api/v1/pages/<slug>/
    """
    permission_classes = [AllowAny]

    def get(self, request, slug):
        page = PageService.get_page(slug)

        if not page:
            return Response({
                'success': False,
                'error': 'صفحه یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = PageDetailSerializer(page)

        return Response({
            'success': True,
            'data': serializer.data
        })


# ═══════════════════════════════════════════════════════════════════════════════
# FAQ APIs
# ═══════════════════════════════════════════════════════════════════════════════

class FAQListAPIView(APIView):
    """
    لیست سوالات متداول (گروه‌بندی شده)
    GET /content/api/v1/faq/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        grouped = FAQService.get_grouped_faq()

        # سریالایز
        data = []
        for group in grouped:
            data.append({
                'category': group['category'],
                'items': FAQItemSerializer(group['items'], many=True).data
            })

        return Response({
            'success': True,
            'data': data
        })


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATION APIs
# ═══════════════════════════════════════════════════════════════════════════════

class NotificationListAPIView(APIView):
    """
    لیست اعلان‌های کاربر
    GET /content/api/v1/notifications/

    Query Params:
        - unread_only: فقط خوانده‌نشده‌ها (true/false)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'

        if unread_only:
            notifications = NotificationService.list_unread(request.user)
        else:
            notifications = NotificationService.list_all(request.user)

        serializer = SystemNotificationSerializer(notifications, many=True)

        return Response({
            'success': True,
            'data': serializer.data
        })


class NotificationMarkReadAPIView(APIView):
    """
    علامت‌گذاری اعلان‌ها به‌عنوان خوانده‌شده
    POST /content/api/v1/notifications/mark-read/

    Body:
        - notification_ids: لیست UUID (اختیاری)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = NotificationMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data.get('notification_ids')
        count = NotificationService.mark_as_read(request.user, notification_ids)

        return Response({
            'success': True,
            'message': f'{count} اعلان خوانده شد',
            'count': count
        })