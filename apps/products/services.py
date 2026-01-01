# apps/products/services.py

"""
Product Services
================
Business logic layer for Products app.

Handles:
- Product retrieval with optimizations
- Inventory management
- Price calculations (game currency)
- Stock operations
- Search and filtering
- Analytics and statistics
- Wishlist operations
- Recently viewed tracking
- Digital inventory management
"""

import logging
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from datetime import timedelta

from django.db import transaction
from django.db.models import (
    Q, F, Avg, Count, Sum, Prefetch,
    Case, When, Value, IntegerField
)
from django.db.models.functions import Coalesce
from django.core.cache import cache
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings

from .models import (
    Category, Brand, Product, ProductImage, ProductVariant,
    DigitalInventory, GameCurrencyRate, ProductReview,
    ProductFAQ, Wishlist, RecentlyViewed
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CACHE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

CACHE_TIMEOUT = getattr(settings, 'PRODUCT_CACHE_TIMEOUT', 60 * 15)  # 15 minutes
CACHE_KEYS = {
    'product_detail': 'product:detail:{}',
    'product_list': 'products:list:{}',
    'category_tree': 'categories:tree',
    'featured_products': 'products:featured',
    'bestsellers': 'products:bestsellers',
    'new_arrivals': 'products:new',
    'product_stats': 'product:stats:{}',
    'recently_viewed_user': 'recently_viewed:user:{}',
    'recently_viewed_session': 'recently_viewed:session:{}',
}


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class CategoryService:
    """Service for category-related operations."""
    
    @staticmethod
    def get_category_tree(include_inactive: bool = False) -> List[Category]:
        """
        Get hierarchical category tree.
        
        Returns:
            List of root categories with children prefetched.
        """
        cache_key = CACHE_KEYS['category_tree']
        
        if not include_inactive:
            cached = cache.get(cache_key)
            if cached:
                return cached
        
        queryset = Category.objects.filter(parent__isnull=True)
        
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        
        queryset = queryset.prefetch_related(
            Prefetch(
                'children',
                queryset=Category.objects.filter(is_active=True).prefetch_related(
                    Prefetch(
                        'children',
                        queryset=Category.objects.filter(is_active=True)
                    )
                )
            )
        ).order_by('sort_order', 'name')
        
        categories = list(queryset)
        
        if not include_inactive:
            cache.set(cache_key, categories, CACHE_TIMEOUT)
        
        return categories
    
    @staticmethod
    def get_category_by_slug(slug: str) -> Optional[Category]:
        """Get category by slug with caching."""
        try:
            return Category.objects.get(
                slug=slug,
                is_active=True
            )
        except Category.DoesNotExist:
            return None
    
    @staticmethod
    def get_category_ancestors(category: Category) -> List[Category]:
        """Get all ancestor categories (for breadcrumbs). Returns empty list as categories are now flat."""
        return []
    
    @staticmethod
    def get_category_descendants(category: Category) -> List[int]:
        """Get category ID (categories are now flat, no descendants)."""
        return [category.id]
    
    @staticmethod
    def get_featured_categories(limit: int = 8) -> List[Category]:
        """Get featured categories for homepage."""
        return Category.objects.filter(
            is_active=True,
            is_featured=True
        ).order_by('sort_order')[:limit]


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class ProductService:
    """Service for product-related operations."""
    
    # ─────────────────────────────────────────────────────────────────────────
    # QUERYSET OPTIMIZATION
    # ─────────────────────────────────────────────────────────────────────────
    
    @staticmethod
    def get_base_queryset(include_inactive: bool = False):
        """
        Get optimized base queryset for products.
        
        Includes:
        - Related category and brand
        - Annotated average rating
        - Annotated review count
        """
        queryset = Product.objects.select_related(
            'category', 'brand'
        ).prefetch_related(
            'images'
        ).annotate(
            avg_rating=Coalesce(
                Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
                Value(0.0)
            ),
            reviews_count=Count(
                'reviews',
                filter=Q(reviews__is_approved=True)
            )
        )
        
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    @staticmethod
    def get_detail_queryset():
        """Get queryset optimized for detail view."""
        return Product.objects.select_related(
            'category', 'category__parent', 'brand'
        ).prefetch_related(
            'images',
            Prefetch(
                'variants',
                queryset=ProductVariant.objects.filter(is_active=True).order_by('sort_order')
            ),
            Prefetch(
                'faqs',
                queryset=ProductFAQ.objects.filter(is_active=True).order_by('sort_order')
            ),
            Prefetch(
                'reviews',
                queryset=ProductReview.objects.filter(is_approved=True).select_related('user').order_by('-created_at')[:10]
            ),
            Prefetch(
                'currency_rates',
                queryset=GameCurrencyRate.objects.filter(is_active=True).order_by('min_amount')
            )
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # SINGLE PRODUCT RETRIEVAL
    # ─────────────────────────────────────────────────────────────────────────
    
    @classmethod
    def get_product_by_slug(cls, slug: str) -> Optional[Product]:
        """Get product by slug with full details."""
        cache_key = CACHE_KEYS['product_detail'].format(slug)
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        try:
            product = cls.get_detail_queryset().get(slug=slug, is_active=True)
            cache.set(cache_key, product, CACHE_TIMEOUT)
            return product
        except Product.DoesNotExist:
            return None
    
    @classmethod
    def get_product_by_id(cls, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        try:
            return cls.get_detail_queryset().get(pk=product_id, is_active=True)
        except Product.DoesNotExist:
            return None
    
    # ─────────────────────────────────────────────────────────────────────────
    # PRODUCT LISTINGS
    # ─────────────────────────────────────────────────────────────────────────
    
    @classmethod
    def get_products_by_category(
        cls,
        category: Category,
        include_subcategories: bool = True,
        **filters
    ):
        """
        Get products for a category.
        
        Args:
            category: Category instance
            include_subcategories: Include products from child categories
            **filters: Additional filters (brand, price range, etc.)
        """
        queryset = cls.get_base_queryset()
        
        if include_subcategories:
            category_ids = CategoryService.get_category_descendants(category)
            queryset = queryset.filter(category_id__in=category_ids)
        else:
            queryset = queryset.filter(category=category)
        
        return cls._apply_filters(queryset, **filters)
    
    @classmethod
    def get_products_by_brand(cls, brand: Brand, **filters):
        """Get products for a specific brand."""
        queryset = cls.get_base_queryset().filter(brand=brand)
        return cls._apply_filters(queryset, **filters)
    
    @classmethod
    def get_featured_products(cls, limit: int = 12):
        """Get featured products for homepage."""
        cache_key = CACHE_KEYS['featured_products']
        cached = cache.get(cache_key)
        
        if cached:
            return cached[:limit]
        
        products = list(
            cls.get_base_queryset()
            .filter(is_featured=True)
            .order_by('-updated_at')[:20]
        )
        
        cache.set(cache_key, products, CACHE_TIMEOUT)
        return products[:limit]
    
    @classmethod
    def get_bestsellers(cls, limit: int = 12):
        """Get bestseller products."""
        cache_key = CACHE_KEYS['bestsellers']
        cached = cache.get(cache_key)
        
        if cached:
            return cached[:limit]
        
        products = list(
            cls.get_base_queryset()
            .filter(is_bestseller=True)
            .order_by('-sales_count')[:20]
        )
        
        cache.set(cache_key, products, CACHE_TIMEOUT)
        return products[:limit]
    
    @classmethod
    def get_new_arrivals(cls, limit: int = 12, days: int = 30):
        """Get new products."""
        cache_key = CACHE_KEYS['new_arrivals']
        cached = cache.get(cache_key)
        
        if cached:
            return cached[:limit]
        
        cutoff_date = timezone.now() - timedelta(days=days)
        products = list(
            cls.get_base_queryset()
            .filter(
                Q(is_new=True) | Q(created_at__gte=cutoff_date)
            )
            .order_by('-created_at')[:20]
        )
        
        cache.set(cache_key, products, CACHE_TIMEOUT)
        return products[:limit]
    
    @classmethod
    def get_discounted_products(cls, limit: int = 12):
        """Get products with discounts."""
        return cls.get_base_queryset().filter(
            original_price__gt=F('price')
        ).order_by('-original_price')[:limit]
    
    @classmethod
    def get_related_products(cls, product: Product, limit: int = 6):
        """Get related products based on category and brand."""
        queryset = cls.get_base_queryset().exclude(pk=product.pk)
        
        # Same category or brand, prioritize same category
        queryset = queryset.filter(
            Q(category=product.category) | Q(brand=product.brand)
        ).annotate(
            relevance=Case(
                When(category=product.category, brand=product.brand, then=Value(3)),
                When(category=product.category, then=Value(2)),
                When(brand=product.brand, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('-relevance', '-sales_count')
        
        return queryset[:limit]
    
    # ─────────────────────────────────────────────────────────────────────────
    # SEARCH
    # ─────────────────────────────────────────────────────────────────────────
    
    @classmethod
    def search_products(cls, query: str, **filters):
        """
        Search products by name, description, SKU.
        
        Args:
            query: Search query string
            **filters: Additional filters
        """
        if not query or len(query) < 2:
            return Product.objects.none()
        
        queryset = cls.get_base_queryset()
        
        # Basic search (for production, use Elasticsearch or PostgreSQL full-text)
        queryset = queryset.filter(
            Q(name__icontains=query) |
            Q(name_en__icontains=query) |
            Q(sku__icontains=query) |
            Q(short_description__icontains=query) |
            Q(description__icontains=query)
        )
        
        return cls._apply_filters(queryset, **filters)
    
    # ─────────────────────────────────────────────────────────────────────────
    # FILTERING & SORTING
    # ─────────────────────────────────────────────────────────────────────────
    
    @staticmethod
    def _apply_filters(queryset, **filters):
        """
        Apply common filters to queryset.
        
        Supported filters:
            - brand_ids: List[int]
            - min_price: Decimal
            - max_price: Decimal
            - product_type: str (physical, virtual, service)
            - in_stock: bool
            - has_discount: bool
            - rating_min: float
            - sort_by: str (newest, price_asc, price_desc, popular, rating)
        """
        
        # Brand filter
        brand_ids = filters.get('brand_ids')
        if brand_ids:
            queryset = queryset.filter(brand_id__in=brand_ids)
        
        # Price range
        min_price = filters.get('min_price')
        if min_price is not None:
            queryset = queryset.filter(price__gte=Decimal(str(min_price)))
        
        max_price = filters.get('max_price')
        if max_price is not None:
            queryset = queryset.filter(price__lte=Decimal(str(max_price)))
        
        # Product type filter
        product_type = filters.get('product_type')
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        # Stock filter
        in_stock = filters.get('in_stock')
        if in_stock is True:
            queryset = queryset.filter(
                Q(product_type='virtual') |  # Virtual always available
                Q(stock_quantity__gt=0, track_inventory=True) |
                Q(track_inventory=False)  # Not tracking = always available
            )
        
        # Discount filter
        has_discount = filters.get('has_discount')
        if has_discount is True:
            queryset = queryset.filter(original_price__gt=F('price'))
        
        # Rating filter
        rating_min = filters.get('rating_min')
        if rating_min is not None:
            queryset = queryset.filter(avg_rating__gte=float(rating_min))
        
        # Featured filter
        is_featured = filters.get('is_featured')
        if is_featured is True:
            queryset = queryset.filter(is_featured=True)
        
        # Apply sorting
        sort_by = filters.get('sort_by', 'newest')
        queryset = ProductService._apply_sorting(queryset, sort_by)
        
        return queryset
    
    @staticmethod
    def _apply_sorting(queryset, sort_by: str):
        """
        Apply sorting to queryset.
        
        Options:
            - newest: Most recent first
            - oldest: Oldest first
            - price_asc: Price low to high
            - price_desc: Price high to low
            - popular: By sales count
            - rating: By average rating
            - name_asc: Alphabetical A-Z
            - name_desc: Alphabetical Z-A
        """
        sorting_map = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'price_asc': 'price',
            'price_desc': '-price',
            'popular': '-sales_count',
            'rating': '-avg_rating',
            'name_asc': 'name',
            'name_desc': '-name',
            'views': '-view_count',
        }
        
        order_field = sorting_map.get(sort_by, '-created_at')
        return queryset.order_by(order_field)
    
    # ─────────────────────────────────────────────────────────────────────────
    # PRICE CALCULATIONS
    # ─────────────────────────────────────────────────────────────────────────
    
    @staticmethod
    def calculate_discount_percentage(product: Product) -> int:
        """Calculate discount percentage for a product."""
        if not product.original_price or product.original_price <= product.price:
            return 0
        
        discount = product.original_price - product.price
        percentage = (discount / product.original_price) * 100
        return int(percentage)
    
    @staticmethod
    def get_game_currency_price(product: Product, amount: int) -> Optional[Dict[str, Any]]:
        """
        Calculate price for game currency based on amount.
        
        Args:
            product: Product instance (must be virtual type)
            amount: Amount of game currency
            
        Returns:
            dict with price_per_unit, total_price, tier_name
        """
        if product.product_type != Product.ProductType.VIRTUAL:
            return None
        
        # Get applicable rate tier
        rate = GameCurrencyRate.objects.filter(
            product=product,
            is_active=True,
            min_amount__lte=amount
        ).filter(
            Q(max_amount__gte=amount) | Q(max_amount__isnull=True)
        ).order_by('-min_amount').first()
        
        if not rate:
            # Fallback to base price
            return {
                'price_per_unit': product.price,
                'total_price': product.price * amount,
                'tier_name': 'پایه',
                'tier_id': None
            }
        
        total_price = rate.price_per_unit * Decimal(str(amount))
        
        return {
            'price_per_unit': rate.price_per_unit,
            'total_price': total_price,
            'tier_name': rate.tier_name,
            'tier_id': rate.id,
            'min_amount': rate.min_amount,
            'max_amount': rate.max_amount
        }
    
    @staticmethod
    def get_all_currency_tiers(product: Product) -> List[Dict[str, Any]]:
        """Get all currency rate tiers for a product."""
        rates = GameCurrencyRate.objects.filter(
            product=product,
            is_active=True
        ).order_by('min_amount')
        
        return [
            {
                'id': rate.id,
                'tier_name': rate.tier_name,
                'min_amount': rate.min_amount,
                'max_amount': rate.max_amount,
                'price_per_unit': rate.price_per_unit,
                'description': rate.description
            }
            for rate in rates
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# INVENTORY SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class InventoryService:
    """Service for inventory management."""
    
    @staticmethod
    def check_stock(product: Product, quantity: int = 1, variant: ProductVariant = None) -> Dict[str, Any]:
        """
        Check if product is in stock.
        
        Returns:
            dict with is_available, available_quantity, message
        """
        # Virtual products - check digital inventory
        if product.product_type == Product.ProductType.VIRTUAL:
            available = DigitalInventory.objects.filter(
                product=product,
                variant=variant,
                is_sold=False,
                is_reserved=False
            ).count()
            
            return {
                'is_available': available >= quantity,
                'available_quantity': available,
                'message': 'موجود' if available >= quantity else 'ناموجود'
            }
        
        # Physical products
        if not product.track_inventory:
            return {
                'is_available': True,
                'available_quantity': 999,  # Unlimited
                'message': 'موجود'
            }
        
        available = product.stock_quantity
        
        return {
            'is_available': available >= quantity,
            'available_quantity': available,
            'message': 'موجود' if available >= quantity else f'فقط {available} عدد موجود است'
        }
    
    @classmethod
    @transaction.atomic
    def reserve_stock(
        cls,
        product: Product,
        quantity: int,
        order_id: int,
        variant: ProductVariant = None
    ) -> Dict[str, Any]:
        """
        Reserve stock for an order.
        
        For physical products: Decrements stock_quantity
        For virtual products: Marks digital inventory as reserved
        
        Returns:
            dict with success, reserved_items, message
        """
        # Check availability first
        stock_check = cls.check_stock(product, quantity, variant)
        if not stock_check['is_available']:
            return {
                'success': False,
                'reserved_items': [],
                'message': stock_check['message']
            }
        
        if product.product_type == Product.ProductType.VIRTUAL:
            return cls._reserve_digital_stock(product, quantity, order_id, variant)
        else:
            return cls._reserve_physical_stock(product, quantity, order_id, variant)
    
    @staticmethod
    @transaction.atomic
    def _reserve_physical_stock(
        product: Product,
        quantity: int,
        order_id: int,
        variant: ProductVariant = None
    ) -> Dict[str, Any]:
        """Reserve physical product stock."""
        # Lock the product row
        product = Product.objects.select_for_update().get(pk=product.pk)
        
        if product.track_inventory:
            if product.stock_quantity < quantity:
                return {
                    'success': False,
                    'reserved_items': [],
                    'message': 'موجودی کافی نیست'
                }
            
            # Decrement stock
            product.stock_quantity = F('stock_quantity') - quantity
            product.save(update_fields=['stock_quantity'])
        
        logger.info(
            f"Reserved {quantity}x physical stock for Product #{product.id}, "
            f"Order #{order_id}"
        )
        
        return {
            'success': True,
            'reserved_items': [],
            'message': f'{quantity} عدد رزرو شد'
        }
    
    @staticmethod
    @transaction.atomic
    def _reserve_digital_stock(
        product: Product,
        quantity: int,
        order_id: int,
        variant: ProductVariant = None
    ) -> Dict[str, Any]:
        """Reserve digital inventory items."""
        # Get available items
        items = DigitalInventory.objects.select_for_update().filter(
            product=product,
            variant=variant,
            is_sold=False,
            is_reserved=False
        )[:quantity]
        
        if len(items) < quantity:
            return {
                'success': False,
                'reserved_items': [],
                'message': f'فقط {len(items)} کد موجود است'
            }
        
        # Reserve items
        item_ids = [item.id for item in items]
        now = timezone.now()
        expires_at = now + timedelta(minutes=30)  # 30-minute reservation
        
        DigitalInventory.objects.filter(id__in=item_ids).update(
            is_reserved=True,
            reserved_for_order_id=order_id,
            reserved_at=now,
            reservation_expires_at=expires_at
        )
        
        logger.info(
            f"Reserved {quantity}x digital items for Product #{product.id}, "
            f"Order #{order_id}: {item_ids}"
        )
        
        return {
            'success': True,
            'reserved_items': item_ids,
            'message': f'{quantity} کد رزرو شد'
        }
    
    @classmethod
    @transaction.atomic
    def release_reservation(
        cls,
        product: Product,
        quantity: int,
        order_id: int,
        variant: ProductVariant = None
    ) -> bool:
        """
        Release reserved stock (e.g., order cancelled).
        
        Returns:
            bool: Success status
        """
        if product.product_type == Product.ProductType.VIRTUAL:
            # Release digital reservations
            DigitalInventory.objects.filter(
                product=product,
                variant=variant,
                reserved_for_order_id=order_id,
                is_reserved=True,
                is_sold=False
            ).update(
                is_reserved=False,
                reserved_for_order_id=None,
                reserved_at=None,
                reservation_expires_at=None
            )
        else:
            # Return physical stock
            if product.track_inventory:
                Product.objects.filter(pk=product.pk).update(
                    stock_quantity=F('stock_quantity') + quantity
                )
        
        logger.info(
            f"Released reservation: {quantity}x Product #{product.id}, "
            f"Order #{order_id}"
        )
        
        return True
    
    @classmethod
    @transaction.atomic
    def confirm_sale(
        cls,
        product: Product,
        quantity: int,
        order_id: int,
        variant: ProductVariant = None
    ) -> Dict[str, Any]:
        """
        Confirm sale and mark digital items as sold.
        
        Returns:
            dict with success, sold_items (for digital), message
        """
        if product.product_type == Product.ProductType.VIRTUAL:
            # Mark reserved items as sold
            items = DigitalInventory.objects.filter(
                product=product,
                variant=variant,
                reserved_for_order_id=order_id,
                is_reserved=True,
                is_sold=False
            )
            
            sold_items = []
            for item in items:
                item.is_sold = True
                item.sold_at = timezone.now()
                item.sold_to_order_id = order_id
                item.save()
                sold_items.append({
                    'id': item.id,
                    'code': item.code,
                    'serial_number': item.serial_number
                })
            
            return {
                'success': True,
                'sold_items': sold_items,
                'message': f'{len(sold_items)} کد تحویل داده شد'
            }
        
        # Physical products - update sales count
        Product.objects.filter(pk=product.pk).update(
            sales_count=F('sales_count') + quantity
        )
        
        return {
            'success': True,
            'sold_items': [],
            'message': 'فروش ثبت شد'
        }
    
    @staticmethod
    def cleanup_expired_reservations():
        """
        Release expired digital inventory reservations.
        Should be run periodically via Celery.
        """
        now = timezone.now()
        
        expired = DigitalInventory.objects.filter(
            is_reserved=True,
            is_sold=False,
            reservation_expires_at__lt=now
        )
        
        count = expired.count()
        
        if count > 0:
            expired.update(
                is_reserved=False,
                reserved_for_order_id=None,
                reserved_at=None,
                reservation_expires_at=None
            )
            
            logger.info(f"Released {count} expired digital inventory reservations")
        
        return count


# ═══════════════════════════════════════════════════════════════════════════════
# REVIEW SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class ReviewService:
    """Service for product reviews."""
    
    @staticmethod
    def get_product_reviews(
        product: Product,
        page: int = 1,
        per_page: int = 10,
        sort_by: str = 'newest'
    ):
        """
        Get paginated reviews for a product.
        
        Args:
            product: Product instance
            page: Page number (1-indexed)
            per_page: Items per page
            sort_by: Sorting option (newest, oldest, rating_high, rating_low, helpful)
            
        Returns:
            dict with reviews, total_count, page_info
        """
        queryset = ProductReview.objects.filter(
            product=product,
            is_approved=True
        ).select_related('user')
        
        # Apply sorting
        sort_map = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'rating_high': '-rating',
            'rating_low': 'rating',
            'helpful': '-helpful_count',
        }
        order_field = sort_map.get(sort_by, '-created_at')
        queryset = queryset.order_by(order_field)
        
        # Get total count
        total_count = queryset.count()
        
        # Paginate
        offset = (page - 1) * per_page
        reviews = list(queryset[offset:offset + per_page])
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        
        return {
            'reviews': reviews,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1
        }
    
    @staticmethod
    def get_product_rating_stats(product: Product) -> Dict[str, Any]:
        """
        Get rating statistics for a product.
        
        Returns:
            dict with average_rating, total_reviews, rating_distribution
        """
        cache_key = CACHE_KEYS['product_stats'].format(product.id)
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        reviews = ProductReview.objects.filter(
            product=product,
            is_approved=True
        )
        
        # Aggregate stats
        stats = reviews.aggregate(
            average_rating=Coalesce(Avg('rating'), Value(0.0)),
            total_reviews=Count('id')
        )
        
        # Rating distribution (count per star)
        distribution = {}
        for i in range(1, 6):
            distribution[i] = reviews.filter(rating=i).count()
        
        result = {
            'average_rating': round(float(stats['average_rating']), 1),
            'total_reviews': stats['total_reviews'],
            'rating_distribution': distribution
        }
        
        cache.set(cache_key, result, CACHE_TIMEOUT)
        return result
    
    @classmethod
    @transaction.atomic
    def create_review(
        cls,
        product: Product,
        user,
        rating: int,
        title: str = '',
        comment: str = '',
        pros: List[str] = None,
        cons: List[str] = None
    ) -> ProductReview:
        """
        Create a new product review.
        
        Args:
            product: Product to review
            user: User submitting review
            rating: Rating (1-5)
            title: Review title
            comment: Review text
            pros: List of pros
            cons: List of cons
            
        Returns:
            ProductReview instance
            
        Raises:
            ValidationError: If user already reviewed or rating invalid
        """
        # Validate rating
        if not 1 <= rating <= 5:
            raise ValidationError("امتیاز باید بین ۱ تا ۵ باشد")
        
        # Check for existing review
        existing = ProductReview.objects.filter(
            product=product,
            user=user
        ).exists()
        
        if existing:
            raise ValidationError("شما قبلاً برای این محصول نظر ثبت کرده‌اید")
        
        # Check if user has purchased this product (optional)
        has_purchased = cls._check_user_purchased(user, product)
        
        review = ProductReview.objects.create(
            product=product,
            user=user,
            rating=rating,
            title=title,
            comment=comment,
            pros=pros or [],
            cons=cons or [],
            is_verified_purchase=has_purchased,
            is_approved=False  # Requires moderation
        )
        
        # Invalidate cache
        cache_key = CACHE_KEYS['product_stats'].format(product.id)
        cache.delete(cache_key)
        
        logger.info(
            f"New review created: User #{user.id} reviewed Product #{product.id} "
            f"with rating {rating}"
        )
        
        return review
    
    @staticmethod
    def _check_user_purchased(user, product: Product) -> bool:
        """Check if user has purchased the product."""
        from apps.orders.models import Order, OrderItem
        
        return OrderItem.objects.filter(
            order__user=user,
            order__status__in=[Order.Status.COMPLETED, Order.Status.DELIVERED],
            product=product
        ).exists()
    
    @classmethod
    @transaction.atomic
    def update_review(
        cls,
        review: ProductReview,
        user,
        **update_data
    ) -> ProductReview:
        """
        Update an existing review.
        
        Args:
            review: ProductReview instance
            user: User attempting update
            **update_data: Fields to update (rating, title, comment, pros, cons)
            
        Returns:
            Updated ProductReview
            
        Raises:
            ValidationError: If unauthorized or invalid data
        """
        if review.user_id != user.id:
            raise ValidationError("شما اجازه ویرایش این نظر را ندارید")
        
        allowed_fields = {'rating', 'title', 'comment', 'pros', 'cons'}
        
        for field, value in update_data.items():
            if field in allowed_fields:
                if field == 'rating' and not 1 <= value <= 5:
                    raise ValidationError("امتیاز باید بین ۱ تا ۵ باشد")
                setattr(review, field, value)
        
        # Reset approval after edit
        review.is_approved = False
        review.save()
        
        # Invalidate cache
        cache_key = CACHE_KEYS['product_stats'].format(review.product_id)
        cache.delete(cache_key)
        
        return review
    
    @classmethod
    @transaction.atomic
    def delete_review(cls, review: ProductReview, user) -> bool:
        """
        Delete a review.
        
        Args:
            review: ProductReview instance
            user: User attempting deletion
            
        Returns:
            bool: Success status
            
        Raises:
            ValidationError: If unauthorized
        """
        if review.user_id != user.id:
            raise ValidationError("شما اجازه حذف این نظر را ندارید")
        
        product_id = review.product_id
        review.delete()
        
        # Invalidate cache
        cache_key = CACHE_KEYS['product_stats'].format(product_id)
        cache.delete(cache_key)
        
        return True
    
    @staticmethod
    @transaction.atomic
    def mark_helpful(review: ProductReview, user) -> Dict[str, Any]:
        """
        Mark a review as helpful.
        
        Returns:
            dict with success, helpful_count
        """
        # Prevent self-voting
        if review.user_id == user.id:
            raise ValidationError("نمی‌توانید به نظر خودتان رأی دهید")
        
        # Simple increment (for more complex voting, use a separate model)
        ProductReview.objects.filter(pk=review.pk).update(
            helpful_count=F('helpful_count') + 1
        )
        
        review.refresh_from_db()
        
        return {
            'success': True,
            'helpful_count': review.helpful_count
        }
    
    @staticmethod
    def approve_review(review: ProductReview, approved_by=None) -> ProductReview:
        """Approve a review (admin action)."""
        review.is_approved = True
        review.save(update_fields=['is_approved', 'updated_at'])
        
        # Invalidate cache to reflect new review
        cache_key = CACHE_KEYS['product_stats'].format(review.product_id)
        cache.delete(cache_key)
        
        logger.info(
            f"Review #{review.id} approved by admin "
            f"{approved_by.id if approved_by else 'system'}"
        )
        
        return review
    
    @staticmethod
    def reject_review(review: ProductReview, reason: str = '', rejected_by=None) -> ProductReview:
        """Reject a review (admin action)."""
        review.is_approved = False
        review.admin_note = reason
        review.save(update_fields=['is_approved', 'admin_note', 'updated_at'])
        
        logger.info(
            f"Review #{review.id} rejected by admin "
            f"{rejected_by.id if rejected_by else 'system'}: {reason}"
        )
        
        return review


# ═══════════════════════════════════════════════════════════════════════════════
# WISHLIST SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class WishlistService:
    """Service for wishlist operations."""
    
    @staticmethod
    def get_user_wishlist(user, page: int = 1, per_page: int = 20):
        """
        Get paginated wishlist for a user.
        
        Returns:
            dict with items, total_count, pagination info
        """
        queryset = Wishlist.objects.filter(user=user).select_related(
            'product', 'product__category', 'product__brand'
        ).prefetch_related(
            'product__images'
        ).order_by('-created_at')
        
        total_count = queryset.count()
        offset = (page - 1) * per_page
        items = list(queryset[offset:offset + per_page])
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return {
            'items': items,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1
        }
    
    @staticmethod
    def add_to_wishlist(user, product: Product) -> Tuple[Wishlist, bool]:
        """
        Add product to user's wishlist.
        
        Returns:
            Tuple of (Wishlist instance, created: bool)
        """
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=user,
            product=product
        )
        
        if created:
            logger.info(f"User #{user.id} added Product #{product.id} to wishlist")
        
        return wishlist_item, created
    
    @staticmethod
    def remove_from_wishlist(user, product: Product) -> bool:
        """
        Remove product from user's wishlist.
        
        Returns:
            bool: True if removed, False if not found
        """
        deleted, _ = Wishlist.objects.filter(
            user=user,
            product=product
        ).delete()
        
        if deleted:
            logger.info(f"User #{user.id} removed Product #{product.id} from wishlist")
        
        return deleted > 0
    
    @staticmethod
    def toggle_wishlist(user, product: Product) -> Dict[str, Any]:
        """
        Toggle product in wishlist.
        
        Returns:
            dict with is_wishlisted, action ('added' or 'removed')
        """
        existing = Wishlist.objects.filter(user=user, product=product).first()
        
        if existing:
            existing.delete()
            return {
                'is_wishlisted': False,
                'action': 'removed'
            }
        else:
            Wishlist.objects.create(user=user, product=product)
            return {
                'is_wishlisted': True,
                'action': 'added'
            }
    
    @staticmethod
    def is_wishlisted(user, product: Product) -> bool:
        """Check if product is in user's wishlist."""
        if not user or not user.is_authenticated:
            return False
        
        return Wishlist.objects.filter(user=user, product=product).exists()
    
    @staticmethod
    def get_wishlist_product_ids(user) -> List[int]:
        """Get list of product IDs in user's wishlist."""
        if not user or not user.is_authenticated:
            return []
        
        return list(
            Wishlist.objects.filter(user=user).values_list('product_id', flat=True)
        )
    
    @staticmethod
    def update_price_notification(user, product: Product, notify: bool) -> bool:
        """
        Update price drop notification preference.
        
        Returns:
            bool: Success status
        """
        updated = Wishlist.objects.filter(
            user=user,
            product=product
        ).update(notify_price_drop=notify)
        
        return updated > 0
    
    @staticmethod
    def get_users_to_notify_price_drop(product: Product) -> List:
        """
        Get users who want price drop notifications for a product.
        
        Returns:
            List of user objects
        """
        return list(
            Wishlist.objects.filter(
                product=product,
                notify_price_drop=True
            ).select_related('user').values_list('user', flat=True)
        )
    
    @staticmethod
    def clear_wishlist(user) -> int:
        """
        Clear all items from user's wishlist.
        
        Returns:
            int: Number of items removed
        """
        deleted, _ = Wishlist.objects.filter(user=user).delete()
        
        logger.info(f"User #{user.id} cleared wishlist ({deleted} items)")
        
        return deleted

# ═══════════════════════════════════════════════════════════════════════════════
# RECENTLY VIEWED SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class RecentlyViewedService:
    """Service for tracking recently viewed products."""

    MAX_ITEMS = 20  # Maximum items per user/session

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------

    @classmethod
    def add_viewed_product(cls, user, product: Product, session_key: str = None):
        """
        Add a product to recently viewed list.
        """
        if user and user.is_authenticated:
            return cls._add_for_user(user, product)
        elif session_key:
            return cls._add_for_session(session_key, product)
        return None

    @classmethod
    def get_recently_viewed(cls, user=None, session_key=None, limit: int = 10):
        """
        Fetch recently viewed products for user/session.
        """
        if user and user.is_authenticated:
            return cls._get_for_user(user, limit)
        elif session_key:
            return cls._get_for_session(session_key, limit)
        return []

    @classmethod
    def clear_recently_viewed(cls, user=None, session_key=None):
        """
        Clear recently viewed list for user/session.
        """
        if user and user.is_authenticated:
            return cls._clear_for_user(user)
        elif session_key:
            return cls._clear_for_session(session_key)
        return 0

    # ----------------------------------------------------------------------
    # User-based tracking
    # ----------------------------------------------------------------------

    @classmethod
    def _add_for_user(cls, user, product: Product):
        cache_key = CACHE_KEYS['recently_viewed_user'].format(user.id)
        viewed = cache.get(cache_key, [])

        product_id = product.id

        # Remove if exists already (to re-add at top)
        viewed = [pid for pid in viewed if pid != product_id]

        # Insert at beginning
        viewed.insert(0, product_id)

        # Limit items
        viewed = viewed[:cls.MAX_ITEMS]

        cache.set(cache_key, viewed, CACHE_TIMEOUT)

        return viewed

    @classmethod
    def _get_for_user(cls, user, limit: int = 10):
        cache_key = CACHE_KEYS['recently_viewed_user'].format(user.id)
        viewed_ids = cache.get(cache_key, [])[:limit]

        # Fetch products preserving order
        products_map = {
            p.id: p for p in Product.objects.filter(id__in=viewed_ids).select_related(
                'category', 'brand'
            ).prefetch_related('images')
        }

        return [products_map[pid] for pid in viewed_ids if pid in products_map]

    @classmethod
    def _clear_for_user(cls, user):
        cache_key = CACHE_KEYS['recently_viewed_user'].format(user.id)
        cache.delete(cache_key)
        return True

    # ----------------------------------------------------------------------
    # Session-based tracking (Anonymous Users)
    # ----------------------------------------------------------------------

    @classmethod
    def _add_for_session(cls, session_key: str, product: Product):
        cache_key = CACHE_KEYS['recently_viewed_session'].format(session_key)
        viewed = cache.get(cache_key, [])

        pid = product.id
        viewed = [x for x in viewed if x != pid]
        viewed.insert(0, pid)
        viewed = viewed[:cls.MAX_ITEMS]

        cache.set(cache_key, viewed, CACHE_TIMEOUT)
        return viewed

    @classmethod
    def _get_for_session(cls, session_key: str, limit: int = 10):
        cache_key = CACHE_KEYS['recently_viewed_session'].format(session_key)
        viewed_ids = cache.get(cache_key, [])[:limit]

        products_map = {
            p.id: p for p in Product.objects.filter(id__in=viewed_ids)
            .select_related('category', 'brand')
            .prefetch_related('images')
        }

        return [products_map[pid] for pid in viewed_ids if pid in products_map]

    @classmethod
    def _clear_for_session(cls, session_key: str):
        cache_key = CACHE_KEYS['recently_viewed_session'].format(session_key)
        cache.delete(cache_key)
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# END OF FILE — COMPLETE PRODUCTS APP SERVICES LAYER
# ═══════════════════════════════════════════════════════════════════════════════