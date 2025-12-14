# apps/content/signals.py

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache

from .models import (
    Article,
    ArticleCategory,
    ArticleTag,
    ArticleComment,
    ArticleImage,
    Page,
    FAQItem,
    SystemNotification
)


# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE SIGNALS
# ═══════════════════════════════════════════════════════════════════════════════

@receiver(pre_save, sender=Article)
def set_article_published_date(sender, instance, **kwargs):
    """
    Automatically set published_at when article status changes to published.
    Only if published_at is not already set.
    """
    if instance.pk:
        try:
            old_instance = Article.objects.get(pk=instance.pk)
            # Status changed from non-published to published
            if (old_instance.status != Article.Status.PUBLISHED and 
                instance.status == Article.Status.PUBLISHED and 
                not instance.published_at):
                instance.published_at = timezone.now()
        except Article.DoesNotExist:
            pass
    else:
        # New article being published directly
        if instance.status == Article.Status.PUBLISHED and not instance.published_at:
            instance.published_at = timezone.now()


@receiver(post_save, sender=Article)
def clear_article_cache_on_save(sender, instance, created, **kwargs):
    """
    Clear article-related caches when an article is created or updated.
    """
    # Clear specific article cache
    cache.delete(f'article_detail_{instance.slug}')
    cache.delete(f'article_detail_{instance.pk}')
    
    # Clear article list caches
    cache.delete('articles_list')
    cache.delete('articles_featured')
    cache.delete('articles_latest')
    cache.delete('articles_pinned')
    
    # Clear category-specific cache
    if instance.category:
        cache.delete(f'articles_category_{instance.category.slug}')
        cache.delete(f'articles_category_{instance.category.pk}')
    
    # Clear tag caches
    for tag in instance.tags.all():
        cache.delete(f'articles_tag_{tag.slug}')


@receiver(post_delete, sender=Article)
def clear_article_cache_on_delete(sender, instance, **kwargs):
    """
    Clear article caches when an article is deleted.
    """
    cache.delete(f'article_detail_{instance.slug}')
    cache.delete(f'article_detail_{instance.pk}')
    cache.delete('articles_list')
    cache.delete('articles_featured')
    cache.delete('articles_latest')
    cache.delete('articles_pinned')
    
    if instance.category:
        cache.delete(f'articles_category_{instance.category.slug}')


@receiver(post_save, sender=Article)
def notify_admin_new_article(sender, instance, created, **kwargs):
    """
    Create admin notification when a new article is pending review.
    """
    if created and instance.status == Article.Status.PENDING:
        # Find admin users and notify them
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        admins = User.objects.filter(is_staff=True, is_active=True)
        for admin in admins:
            SystemNotification.objects.create(
                user=admin,
                title='مقاله جدید در انتظار تأیید',
                message=f'مقاله "{instance.title}" توسط {instance.author} ارسال شده و در انتظار تأیید است.',
                type=SystemNotification.NotificationType.INFO
            )


# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE CATEGORY SIGNALS
# ═══════════════════════════════════════════════════════════════════════════════

@receiver(post_save, sender=ArticleCategory)
def clear_category_cache(sender, instance, **kwargs):
    """
    Clear category caches when a category is saved.
    """
    cache.delete('article_categories_list')
    cache.delete('article_categories_active')
    cache.delete(f'article_category_{instance.slug}')
    cache.delete(f'article_category_{instance.pk}')
    
    # Clear parent category cache if exists
    if instance.parent:
        cache.delete(f'article_category_{instance.parent.slug}')


@receiver(post_delete, sender=ArticleCategory)
def clear_category_cache_on_delete(sender, instance, **kwargs):
    """
    Clear category caches when a category is deleted.
    """
    cache.delete('article_categories_list')
    cache.delete('article_categories_active')
    cache.delete(f'article_category_{instance.slug}')


# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE TAG SIGNALS
# ═══════════════════════════════════════════════════════════════════════════════

@receiver(post_save, sender=ArticleTag)
def clear_tag_cache(sender, instance, **kwargs):
    """
    Clear tag caches when a tag is saved.
    """
    cache.delete('article_tags_list')
    cache.delete(f'articles_tag_{instance.slug}')


@receiver(post_delete, sender=ArticleTag)
def clear_tag_cache_on_delete(sender, instance, **kwargs):
    """
    Clear tag caches when a tag is deleted.
    """
    cache.delete('article_tags_list')
    cache.delete(f'articles_tag_{instance.slug}')


# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE COMMENT SIGNALS
# ═══════════════════════════════════════════════════════════════════════════════

@receiver(post_save, sender=ArticleComment)
def handle_comment_saved(sender, instance, created, **kwargs):
    """
    Handle comment creation and approval:
    - Notify article author about new comments
    - Notify parent comment author about replies
    - Clear article cache
    """
    # Clear article's comment cache
    cache.delete(f'article_comments_{instance.article.pk}')
    cache.delete(f'article_detail_{instance.article.slug}')
    
    if created:
        # New comment notification to article author
        if instance.status == ArticleComment.Status.APPROVED:
            _notify_article_author(instance)
            
            # Reply notification
            if instance.parent:
                _notify_parent_author(instance)
    
    # If comment was just approved (not created)
    if not created:
        try:
            old_instance = ArticleComment.objects.get(pk=instance.pk)
            if (old_instance.status != ArticleComment.Status.APPROVED and 
                instance.status == ArticleComment.Status.APPROVED):
                _notify_article_author(instance)
                if instance.parent:
                    _notify_parent_author(instance)
        except ArticleComment.DoesNotExist:
            pass


@receiver(post_delete, sender=ArticleComment)
def handle_comment_deleted(sender, instance, **kwargs):
    """
    Clear caches when a comment is deleted.
    """
    cache.delete(f'article_comments_{instance.article.pk}')
    cache.delete(f'article_detail_{instance.article.slug}')


def _notify_article_author(comment):
    """
    Notify article author about a new approved comment.
    """
    try:
        article = comment.article
        
        # Don't notify if the commenter is the author
        if article.author and comment.user != article.author:
            SystemNotification.objects.create(
                user=article.author,
                title='نظر جدید روی مقاله شما',
                message=f'{comment.user.get_full_name() or comment.user.phone} روی مقاله "{article.title}" نظر داد.',
                type=SystemNotification.NotificationType.INFO
            )
    except Exception:
        pass  # Fail silently, log in production


def _notify_parent_author(comment):
    """
    Notify parent comment author about a reply.
    """
    try:
        parent = comment.parent
        
        # Don't notify if replying to own comment
        if parent.user and comment.user != parent.user:
            SystemNotification.objects.create(
                user=parent.user,
                title='پاسخ به نظر شما',
                message=f'{comment.user.get_full_name() or comment.user.phone} به نظر شما پاسخ داد.',
                type=SystemNotification.NotificationType.INFO
            )
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE SIGNALS
# ═══════════════════════════════════════════════════════════════════════════════

@receiver(post_save, sender=Page)
def clear_page_cache(sender, instance, **kwargs):
    """
    Clear page caches when a page is saved.
    """
    cache.delete(f'page_detail_{instance.slug}')
    cache.delete(f'page_detail_{instance.pk}')
    cache.delete('pages_footer')  # Footer pages list
    cache.delete('pages_header')  # Header pages list
    cache.delete('pages_list')


@receiver(post_delete, sender=Page)
def clear_page_cache_on_delete(sender, instance, **kwargs):
    """
    Clear page caches when a page is deleted.
    """
    cache.delete(f'page_detail_{instance.slug}')
    cache.delete('pages_footer')
    cache.delete('pages_header')
    cache.delete('pages_list')


# ═══════════════════════════════════════════════════════════════════════════════
# FAQ SIGNALS
# ═══════════════════════════════════════════════════════════════════════════════

@receiver(post_save, sender=FAQItem)
def clear_faq_cache(sender, instance, **kwargs):
    """
    Clear FAQ caches when an FAQ item is saved.
    """
    cache.delete('faq_list')
    cache.delete('faq_list_active')
    cache.delete('faq_categories')
    
    if instance.category:
        cache.delete(f'faq_category_{instance.category}')


@receiver(post_delete, sender=FAQItem)
def clear_faq_cache_on_delete(sender, instance, **kwargs):
    """
    Clear FAQ caches when an FAQ item is deleted.
    """
    cache.delete('faq_list')
    cache.delete('faq_list_active')
    cache.delete('faq_categories')
    
    if instance.category:
        cache.delete(f'faq_category_{instance.category}')


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM NOTIFICATION SIGNALS
# ═══════════════════════════════════════════════════════════════════════════════

@receiver(post_save, sender=SystemNotification)
def handle_notification_created(sender, instance, created, **kwargs):
    """
    Handle new system notification:
    - Clear user notification cache
    - Could trigger push notification in the future
    """
    if instance.user:
        cache.delete(f'notifications_user_{instance.user.pk}')
        cache.delete(f'notifications_unread_{instance.user.pk}')
    
    if instance.send_to_all:
        cache.delete('notifications_global')
    
    # Future: Send push notification or websocket event
    if created:
        _trigger_realtime_notification(instance)


@receiver(post_delete, sender=SystemNotification)
def handle_notification_deleted(sender, instance, **kwargs):
    """
    Clear notification caches when deleted.
    """
    if instance.user:
        cache.delete(f'notifications_user_{instance.user.pk}')
        cache.delete(f'notifications_unread_{instance.user.pk}')


@receiver(pre_save, sender=SystemNotification)
def set_notification_read_timestamp(sender, instance, **kwargs):
    """
    Automatically set read_at timestamp when is_read becomes True.
    """
    if instance.pk:
        try:
            old_instance = SystemNotification.objects.get(pk=instance.pk)
            # If is_read changed from False to True
            if not old_instance.is_read and instance.is_read and not instance.read_at:
                instance.read_at = timezone.now()
        except SystemNotification.DoesNotExist:
            pass


def _trigger_realtime_notification(notification):
    """
    Placeholder for real-time notification delivery.
    Could use Django Channels, Firebase, or other push services.
    """
    # TODO: Implement WebSocket push
    # TODO: Implement Firebase Cloud Messaging
    # TODO: Implement email for important notifications
    pass
# ═══════════════════════════════════════════════════════════════════════════════