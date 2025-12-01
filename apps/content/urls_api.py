# apps/content/urls_api.py

from django.urls import path
from . import api_views

app_name = "content_api"

urlpatterns = [
    # Categories
    path("categories/", api_views.ArticleCategoryListAPIView.as_view(), name="category_list"),
    path("categories/<slug:slug>/", api_views.ArticleCategoryDetailAPIView.as_view(), name="category_detail"),

    # Tags
    path("tags/", api_views.ArticleTagListAPIView.as_view(), name="tag_list"),
    path("tags/<slug:slug>/", api_views.ArticleTagDetailAPIView.as_view(), name="tag_detail"),

    # Articles
    path("articles/", api_views.ArticleListAPIView.as_view(), name="article_list"),
    path("articles/featured/", api_views.ArticleFeaturedAPIView.as_view(), name="article_featured"),
    path("articles/popular/", api_views.ArticlePopularAPIView.as_view(), name="article_popular"),
    path("articles/<slug:slug>/", api_views.ArticleDetailAPIView.as_view(), name="article_detail"),
    path("articles/<slug:slug>/like/", api_views.ArticleLikeAPIView.as_view(), name="article_like"),

    # Comments
    path("articles/<slug:slug>/comments/", api_views.ArticleCommentsAPIView.as_view(), name="article_comments"),
    path("articles/<slug:slug>/comments/create/", api_views.ArticleCommentCreateAPIView.as_view(), name="comment_create"),
    path("comments/<uuid:pk>/like/", api_views.CommentLikeAPIView.as_view(), name="comment_like"),

    # Pages
    path("pages/", api_views.PageListAPIView.as_view(), name="page_list"),
    path("pages/<slug:slug>/", api_views.PageDetailAPIView.as_view(), name="page_detail"),

    # FAQ
    path("faq/", api_views.FAQListAPIView.as_view(), name="faq_list"),

    # Testimonials
    path("testimonials/", api_views.TestimonialListAPIView.as_view(), name="testimonials"),

    # Notifications
    path("notifications/", api_views.NotificationListAPIView.as_view(), name="notifications"),
    path("notifications/mark-read/", api_views.NotificationMarkReadAPIView.as_view(), name="notifications_mark_read"),
]
