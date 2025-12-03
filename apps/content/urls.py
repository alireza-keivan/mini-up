# apps/content/urls.py
"""
URL Configuration for Content App

شامل:
- مسیرهای HTML برای صفحات وب
- مسیرهای API برای دسترسی به داده‌ها
"""

from django.urls import path
from . import views, api_views

app_name = 'content'


# ═══════════════════════════════════════════════════════════════════════════════
# HTML VIEWS (Template-based pages)
# ═══════════════════════════════════════════════════════════════════════════════

urlpatterns = [
    # ----- Articles (Blog) -----
    path('articles/', views.ArticleListPageView.as_view(), name='article_list'),
    path('articles/<slug:slug>/', views.ArticleDetailPageView.as_view(), name='article_detail'),
    
    # ----- FAQ -----
    path('faq/', views.FAQPageView.as_view(), name='faq'),
    
    # ----- Static Pages -----
    path('page/<slug:slug>/', views.PageDetailView.as_view(), name='page_detail'),
]


# ═══════════════════════════════════════════════════════════════════════════════
# API VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

api_urlpatterns = [
    # ----- Article Categories -----
    path('api/v1/categories/', api_views.ArticleCategoryListAPIView.as_view(), name='api_category_list'),
    path('api/v1/categories/<slug:slug>/', api_views.ArticleCategoryDetailAPIView.as_view(), name='api_category_detail'),
    
    # ----- Article Tags -----
    path('api/v1/tags/', api_views.ArticleTagListAPIView.as_view(), name='api_tag_list'),
    path('api/v1/tags/<slug:slug>/', api_views.ArticleTagDetailAPIView.as_view(), name='api_tag_detail'),
    
    # ----- Articles -----
    path('api/v1/articles/', api_views.ArticleListAPIView.as_view(), name='api_article_list'),
    path('api/v1/articles/featured/', api_views.ArticleFeaturedAPIView.as_view(), name='api_article_featured'),
    path('api/v1/articles/popular/', api_views.ArticlePopularAPIView.as_view(), name='api_article_popular'),
    path('api/v1/articles/<slug:slug>/', api_views.ArticleDetailAPIView.as_view(), name='api_article_detail'),
    path('api/v1/articles/<slug:slug>/like/', api_views.ArticleLikeAPIView.as_view(), name='api_article_like'),
    
    # ----- Article Comments -----
    path('api/v1/articles/<slug:slug>/comments/', api_views.ArticleCommentsAPIView.as_view(), name='api_article_comments'),
    path('api/v1/articles/<slug:slug>/comments/create/', api_views.ArticleCommentCreateAPIView.as_view(), name='api_article_comment_create'),
    path('api/v1/comments/<uuid:pk>/like/', api_views.CommentLikeAPIView.as_view(), name='api_comment_like'),
    
    # ----- Static Pages -----
    path('api/v1/pages/', api_views.PageListAPIView.as_view(), name='api_page_list'),
    path('api/v1/pages/<slug:slug>/', api_views.PageDetailAPIView.as_view(), name='api_page_detail'),
    
    # ----- FAQ -----
    path('api/v1/faq/', api_views.FAQListAPIView.as_view(), name='api_faq_list'),
    
    # ----- Testimonials -----
    path('api/v1/testimonials/', api_views.TestimonialListAPIView.as_view(), name='api_testimonial_list'),
    
    # ----- Notifications -----
    path('api/v1/notifications/', api_views.NotificationListAPIView.as_view(), name='api_notification_list'),
    path('api/v1/notifications/mark-read/', api_views.NotificationMarkReadAPIView.as_view(), name='api_notification_mark_read'),
]

# Combine all URL patterns
urlpatterns += api_urlpatterns
