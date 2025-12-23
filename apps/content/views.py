# apps/content/views.py

from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from .models import Article, ArticleCategory, Page, FAQItem


class ArticleListPageView(TemplateView):
    """
    صفحه لیست مقالات
    """
    template_name = "content/article_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get published articles ordered by publish date
        articles = Article.objects.filter(
            status='published'
        ).select_related('category', 'author').order_by('-published_at')
        
        context["articles"] = articles
        context["categories"] = ArticleCategory.objects.filter(parent__isnull=True)
        return context


class ArticleDetailPageView(TemplateView):
    """
    صفحه جزئیات مقاله
    """
    template_name = "content/article_detail.html"

    def get_context_data(self, slug=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["article"] = get_object_or_404(Article, slug=slug)
        return context


class PageDetailView(TemplateView):
    """
    صفحه استاتیک
    """
    template_name = "content/page.html"

    def get_context_data(self, slug=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = get_object_or_404(Page, slug=slug)
        return context


class FAQPageView(TemplateView):
    """
    صفحه سوالات متداول
    """
    template_name = "content/faq.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items"] = FAQItem.objects.all().order_by("order")
        return context
