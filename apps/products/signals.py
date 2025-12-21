# apps/products/signals.py

import logging
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.cache import cache
from django.db.models import Avg
from django.utils import timezone
from django.db.models import Avg, F
from .models import (
    Product, ProductVariant, ProductReview, Category,
    DigitalInventory, Wishlist, RecentlyViewed, Brand
)

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════
# CACHE KEY PATTERNS
# ════════════════════════════════════════════════

CACHE_KEYS = {
    'product_detail': 'product:detail:{product_id}',
    'product_list': 'products:list:{category_slug}',
    'category_tree': 'categories:tree',
    'category_detail': 'category:detail:{category_id}',
    'featured_products': 'products:featured',
    'bestseller_products': 'products:bestsellers',
    'new_products': 'products:new',
    'brand_products': 'brand:products:{brand_id}',
    'product_reviews': 'product:reviews:{product_id}',
    'product_stats': 'product:stats:{product_id}',
}

CACHE_TIMEOUT = 60 * 15  # 15 minutes



# ════════════════════════════════════════════════
# CACHE INVALIDATION HELPERS
# ════════════════════════════════════════════════

def _invalidate_product_cache(product):
    keys = [
        CACHE_KEYS['product_detail'].format(product_id=product.id),
        CACHE_KEYS['product_reviews'].format(product_id=product.id),
        CACHE_KEYS['product_stats'].format(product_id=product.id),
        CACHE_KEYS['featured_products'],
        CACHE_KEYS['bestseller_products'],
        CACHE_KEYS['new_products'],
    ]

    # Invalidate product list caches for category
    if product.category:
        cat = product.category
        keys.append(CACHE_KEYS['product_list'].format(category_slug=cat.slug))

    # Brand cache
    if product.brand:
        keys.append(CACHE_KEYS['brand_products'].format(brand_id=product.brand.id))

    cache.delete_many(keys)
    logger.debug(f"[Cache] Invalidated {len(keys)} keys for product {product.id}")


def _invalidate_category_cache(category):
    keys = [
        CACHE_KEYS['category_tree'],
        CACHE_KEYS['category_detail'].format(category_id=category.id),
        CACHE_KEYS['product_list'].format(category_slug=category.slug),
    ]
    cache.delete_many(keys)



# ════════════════════════════════════════════════
# NOTIFICATION HELPERS (PLACEHOLDER)
# ════════════════════════════════════════════════

def _notify_price_drop(product, old_price, new_price):
    """
    Notify users whose wishlists include this product.
    Placeholder - connects to actual notification system.
    """
    users = Wishlist.objects.filter(product=product).values_list('user', flat=True)
    logger.info(
        f"[Notify] Price drop for product {product.id}: {old_price} → {new_price} "
        f"({len(users)} users)"
    )
    # integrate with your notifications service


def _notify_back_in_stock(product):
    users = Wishlist.objects.filter(product=product).values_list('user', flat=True)
    logger.info(
        f"[Notify] Back in stock: product {product.id} ({len(users)} users)"
    )
    # integrate with your notifications service



# ════════════════════════════════════════════════
# PRODUCT SIGNALS
# ════════════════════════════════════════════════

@receiver(pre_save, sender=Product)
def product_pre_save(sender, instance, **kwargs):
    """
    Store old values for comparison (price, stock, status).
    """
    if not instance.pk:
        instance._old_price = None
        instance._old_stock = None
        instance._was_active = None
        return

    try:
        old = Product.objects.get(pk=instance.pk)
        instance._old_price = old.price
        instance._old_stock = old.stock
        instance._was_active = old.is_active
    except Product.DoesNotExist:
        instance._old_price = None
        instance._old_stock = None
        instance._was_active = None


@receiver(post_save, sender=Product)
def product_post_save(sender, instance, created, **kwargs):
    # Invalidate caches
    _invalidate_product_cache(instance)

    if created:
        logger.info(f"[Product] Created: {instance.id}")
        return

    # Price drop
    if instance._old_price and instance.price < instance._old_price:
        _notify_price_drop(instance, instance._old_price, instance.price)

    # Back in stock
    if (instance._old_stock == 0 and instance.stock > 0) or \
       (instance._was_active is False and instance.is_active):
        _notify_back_in_stock(instance)



@receiver(post_delete, sender=Product)
def product_post_delete(sender, instance, **kwargs):
    _invalidate_product_cache(instance)
    logger.info(f"[Product] Deleted: {instance.id}")



# ════════════════════════════════════════════════
# PRODUCT VARIANT SIGNALS
# ════════════════════════════════════════════════

@receiver(post_save, sender=ProductVariant)
@receiver(post_delete, sender=ProductVariant)
def variant_changed(sender, instance, **kwargs):
    _invalidate_product_cache(instance.product)



# ════════════════════════════════════════════════
# CATEGORY SIGNALS
# ════════════════════════════════════════════════

@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def category_changed(sender, instance, **kwargs):
    _invalidate_category_cache(instance)



# ════════════════════════════════════════════════
# BRAND SIGNALS
# ════════════════════════════════════════════════

@receiver(post_delete, sender=Brand)
def brand_post_delete(sender, instance, **kwargs):
    cache.delete(
        CACHE_KEYS['brand_products'].format(brand_id=instance.id)
    )
    logger.info(f"[Brand] Deleted: {instance.id}")



# ════════════════════════════════════════════════
# REVIEW SIGNALS
# ════════════════════════════════════════════════

@receiver(post_save, sender=ProductReview)
def review_post_save(sender, instance, created, **kwargs):
    """
    - Recalculate product average rating
    - Invalidate caches
    """
    _invalidate_product_cache(instance.product)

    avg_rating = instance.product.reviews.filter(
        is_approved=True
    ).aggregate(avg=Avg('rating'))['avg']

    instance.product.average_rating = avg_rating or 0
    instance.product.review_count = instance.product.reviews.filter(
        is_approved=True
    ).count()
    instance.product.save(update_fields=['average_rating', 'review_count'])

    if created:
        logger.info(f"[Review] New review added for product {instance.product.id}")


@receiver(post_delete, sender=ProductReview)
def review_post_delete(sender, instance, **kwargs):
    _invalidate_product_cache(instance.product)



# ════════════════════════════════════════════════
# DIGITAL INVENTORY SIGNALS
# ════════════════════════════════════════════════

@receiver(post_save, sender=DigitalInventory)
@receiver(post_delete, sender=DigitalInventory)
def digital_inventory_changed(sender, instance, **kwargs):
    """
    When digital inventory is updated, invalidate product cache
    so stock indicators refresh.
    """
    _invalidate_product_cache(instance.product)



# ════════════════════════════════════════════════
# RECENTLY VIEWED SIGNALS
# ════════════════════════════════════════════════

@receiver(post_save, sender=RecentlyViewed)
def recently_viewed_post_save(sender, instance, created, **kwargs):
    """
    Increase product view count only on first view creation.
    """
    if created:
        Product.objects.filter(pk=instance.product_id).update(
            view_count=F('view_count') + 1
        )
        _invalidate_product_cache(instance.product)


# ════════════════════════════════════════════════
# WISHLIST SIGNALS
# ════════════════════════════════════════════════

@receiver(post_save, sender=Wishlist)
@receiver(post_delete, sender=Wishlist)
def wishlist_changed(sender, instance, **kwargs):
    """
    Invalidate product cache (wishlist state in serializer).
    """
    _invalidate_product_cache(instance.product)
