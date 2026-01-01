# apps/products/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, Http404
from django.db.models import Q, Prefetch, Avg, Count, Min, Max
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.urls import reverse
from decimal import Decimal

from .models import (
    Category, Brand, Product, ProductVariant, ProductImage,
    ProductReview, Wishlist, ProductTag
)
from .services import (
    ProductService, CategoryService, ReviewService,
    WishlistService, RecentlyViewedService
)

import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# MIXINS
# ═══════════════════════════════════════════════════════════════════════════════

class WishlistContextMixin:
    """Add wishlist product IDs to context for authenticated users."""
    
    def get_wishlist_ids(self):
        if self.request.user.is_authenticated:
            return set(
                Wishlist.objects.filter(user=self.request.user)
                .values_list('product_id', flat=True)
            )
        return set()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['wishlist_ids'] = self.get_wishlist_ids()
        return context


class FilterMixin:
    """Extract filter parameters from request."""
    
    def get_filter_params(self):
        params = self.request.GET
        
        filters = {
            'category': params.get('category'),
            'brand': params.get('brand'),
            'min_price': params.get('min_price'),
            'max_price': params.get('max_price'),
            'min_rating': params.get('min_rating'),
            'in_stock': params.get('in_stock') == 'true',
            'has_discount': params.get('has_discount') == 'true',
            'product_type': params.get('type'),  # physical, digital
            'tags': params.getlist('tag'),
        }
        
        # Clean empty values
        return {k: v for k, v in filters.items() if v}
    
    def get_sort_option(self):
        return self.request.GET.get('sort', 'newest')
    
    def get_search_query(self):
        return self.request.GET.get('q', '').strip()


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT LIST VIEW (Shop Page)
# ═══════════════════════════════════════════════════════════════════════════════

class ProductListView(WishlistContextMixin, FilterMixin, ListView):
    """
    Main shop/catalog page with filtering, sorting, and pagination.
    
    URL: /products/ or /products/shop/
    Template: products/product_list.html
    """
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        # Start with active products, EXCLUDE virtual products (they appear on /virtual-services/)
        queryset = Product.objects.filter(
            is_active=True
        ).exclude(
            product_type=Product.ProductType.VIRTUAL
        ).select_related(
            'category', 'brand'
        ).prefetch_related(
            'images',
            'variants'
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        )
        
        # Apply filters
        filters = self.get_filter_params()
        
        # Category filter
        if filters.get('category'):
            category_param = filters['category']
            try:
                if category_param.isdigit():
                    category = Category.objects.get(pk=category_param)
                else:
                    category = Category.objects.get(slug=category_param)
                
                # Include subcategories
                category_ids = CategoryService.get_category_with_descendants(category.id)
                queryset = queryset.filter(category_id__in=category_ids)
            except Category.DoesNotExist:
                pass
        
        # Brand filter
        if filters.get('brand'):
            brand_param = filters['brand']
            if brand_param.isdigit():
                queryset = queryset.filter(brand_id=brand_param)
            else:
                queryset = queryset.filter(brand__slug=brand_param)
        
        # Price range
        if filters.get('min_price'):
            try:
                min_price = Decimal(filters['min_price'])
                queryset = queryset.filter(
                    Q(final_price__gte=min_price) | 
                    Q(variants__final_price__gte=min_price)
                ).distinct()
            except:
                pass
        
        if filters.get('max_price'):
            try:
                max_price = Decimal(filters['max_price'])
                queryset = queryset.filter(
                    Q(final_price__lte=max_price) | 
                    Q(variants__final_price__lte=max_price)
                ).distinct()
            except:
                pass
        
        # Rating filter
        if filters.get('min_rating'):
            try:
                min_rating = float(filters['min_rating'])
                queryset = queryset.filter(avg_rating__gte=min_rating)
            except:
                pass
        
        # Stock filter
        if filters.get('in_stock'):
            queryset = queryset.filter(
                Q(physical_inventory__quantity__gt=0) |
                Q(digital_inventory__is_available=True)
            ).distinct()
        
        # Discount filter
        if filters.get('has_discount'):
            queryset = queryset.filter(
                Q(discount_percent__gt=0) |
                Q(discount_amount__gt=0)
            )
        
        # Product type filter
        if filters.get('product_type'):
            queryset = queryset.filter(product_type=filters['product_type'])
        
        # Tags filter
        if filters.get('tags'):
            queryset = queryset.filter(tags__slug__in=filters['tags']).distinct()
        
        # Search query
        search_query = self.get_search_query()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(name_fa__icontains=search_query) |
                Q(short_description__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(brand__name__icontains=search_query) |
                Q(category__name__icontains=search_query)
            ).distinct()
        
        # Apply sorting
        sort_option = self.get_sort_option()
        queryset = self._apply_sorting(queryset, sort_option)
        
        return queryset
    
    def _apply_sorting(self, queryset, sort_option):
        """Apply sorting based on user selection."""
        sorting_map = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'price_low': 'final_price',
            'price_high': '-final_price',
            'rating': '-avg_rating',
            'popular': '-view_count',
            'bestseller': '-sold_count',
            'name_asc': 'name',
            'name_desc': '-name',
        }
        
        order_by = sorting_map.get(sort_option, '-created_at')
        return queryset.order_by(order_by)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Categories for sidebar filter
        context['categories'] = CategoryService.get_category_tree()
        
        # Brands for sidebar filter
        context['brands'] = Brand.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        ).filter(
            product_count__gt=0
        ).order_by('name')
        
        # Price range for slider
        price_stats = Product.objects.filter(is_active=True).aggregate(
            min_price=Min('final_price'),
            max_price=Max('final_price')
        )
        context['price_range'] = {
            'min': int(price_stats['min_price'] or 0),
            'max': int(price_stats['max_price'] or 10000000),
        }
        
        # Current filters (to maintain state)
        context['current_filters'] = self.get_filter_params()
        context['current_sort'] = self.get_sort_option()
        context['search_query'] = self.get_search_query()
        
        # Sorting options
        context['sort_options'] = [
            ('newest', 'جدیدترین'),
            ('price_low', 'ارزان‌ترین'),
            ('price_high', 'گران‌ترین'),
            ('rating', 'بیشترین امتیاز'),
            ('popular', 'پربازدیدترین'),
            ('bestseller', 'پرفروش‌ترین'),
        ]
        
        # Page title
        if context.get('search_query'):
            context['page_title'] = f'جستجو: {context["search_query"]}'
        elif context['current_filters'].get('category'):
            try:
                cat = Category.objects.get(
                    Q(pk=context['current_filters']['category']) |
                    Q(slug=context['current_filters']['category'])
                )
                context['page_title'] = cat.name
                context['current_category'] = cat
            except:
                context['page_title'] = 'فروشگاه'
        else:
            context['page_title'] = 'فروشگاه'
        
        return context


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT DETAIL VIEW
# ═══════════════════════════════════════════════════════════════════════════════

class ProductDetailView(WishlistContextMixin, DetailView):
    """
    Product detail page.
    
    URL: /products/product/<slug>/
    Template: products/product_detail.html
    """
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Product.objects.filter(
            is_active=True
        ).select_related(
            'category', 'brand'
        ).prefetch_related(
            'images',
            'variants__attribute_values__attribute',
            'tags',
            Prefetch(
                'reviews',
                queryset=ProductReview.objects.filter(
                    is_approved=True
                ).select_related('user').order_by('-created_at')[:5]
            )
        )
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        # Track view
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        # Add to recently viewed
        RecentlyViewedService.add_viewed_product(
            user=self.request.user if self.request.user.is_authenticated else None,
            product=obj,
            session_key=session_key
        )
        
        # Increment view count (async would be better)
        ProductService.increment_view_count(obj)
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        # All product images
        context['images'] = product.images.all().order_by('order', '-is_primary')
        
        # Product variants with their attributes
        context['variants'] = product.variants.filter(
            is_active=True
        ).select_related().prefetch_related(
            'attribute_values__attribute'
        ).order_by('price')
        
        # Check if product has variants
        context['has_variants'] = context['variants'].exists()
        
        # Stock status
        context['stock_status'] = self._get_stock_status(product)
        
        # Reviews statistics
        review_stats = ProductReview.objects.filter(
            product=product,
            is_approved=True
        ).aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id'),
            rating_5=Count('id', filter=Q(rating=5)),
            rating_4=Count('id', filter=Q(rating=4)),
            rating_3=Count('id', filter=Q(rating=3)),
            rating_2=Count('id', filter=Q(rating=2)),
            rating_1=Count('id', filter=Q(rating=1)),
        )
        context['review_stats'] = review_stats
        
        # Recent reviews (already prefetched)
        context['recent_reviews'] = product.reviews.all()[:5]
        
        # User's review (if exists)
        if self.request.user.is_authenticated:
            context['user_review'] = ProductReview.objects.filter(
                product=product,
                user=self.request.user
            ).first()
            
            # Can user review this product?
            context['can_review'] = ReviewService.can_user_review(
                self.request.user, product
            )
        
        # Related products
        context['related_products'] = ProductService.get_related_products(
            product_id=product.id,
            limit=8
        )
        
        # Recently viewed (excluding current)
        session_key = self.request.session.session_key
        context['recently_viewed'] = RecentlyViewedService.get_recently_viewed(
            user=self.request.user if self.request.user.is_authenticated else None,
            session_key=session_key,
            exclude_product_id=product.id,
            limit=6
        )
        
        # Breadcrumbs
        context['breadcrumbs'] = self._build_breadcrumbs(product)
        
        # Is in wishlist
        if self.request.user.is_authenticated:
            context['is_wishlisted'] = Wishlist.objects.filter(
                user=self.request.user,
                product=product
            ).exists()
        else:
            context['is_wishlisted'] = False
        
        # SEO meta
        context['meta_title'] = product.meta_title or product.name
        context['meta_description'] = product.meta_description or product.short_description
        
        return context
    
    def _get_stock_status(self, product):
        """Get stock status for product."""
        if product.product_type == 'physical':
            try:
                inventory = product.physical_inventory
                return {
                    'in_stock': inventory.quantity > 0,
                    'quantity': inventory.quantity,
                    'low_stock': 0 < inventory.quantity <= inventory.low_stock_threshold,
                    'allow_backorder': inventory.allow_backorder,
                    'max_per_order': inventory.max_per_order,
                }
            except:
                return {
                    'in_stock': False,
                    'quantity': 0,
                    'low_stock': False,
                    'allow_backorder': False,
                    'max_per_order': 1,
                }
        else:  # digital
            try:
                inventory = product.digital_inventory
                return {
                    'in_stock': inventory.is_available,
                    'quantity': None,  # Unlimited for digital
                    'low_stock': False,
                    'allow_backorder': False,
                    'max_per_order': inventory.max_per_order,
                }
            except:
                return {
                    'in_stock': True,
                    'quantity': None,
                    'low_stock': False,
                    'allow_backorder': False,
                    'max_per_order': 1,
                }
    
    def _build_breadcrumbs(self, product):
        """Build breadcrumb trail for product."""
        breadcrumbs = [
            {'name': 'خانه', 'url': reverse('core:home')},
            {'name': 'فروشگاه', 'url': reverse('products:product_list')},
        ]
        
        # Add category hierarchy
        if product.category:
            ancestors = []
            category = product.category
            while category:
                ancestors.insert(0, category)
                category = category.parent
            
            for cat in ancestors:
                breadcrumbs.append({
                    'name': cat.name,
                    'url': reverse('products:category_detail', kwargs={'slug': cat.slug})
                })
        
        # Add current product (no URL - current page)
        breadcrumbs.append({
            'name': product.name,
            'url': None
        })
        
        return breadcrumbs


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class CategoryListView(ListView):
    """
    List all categories.
    
    URL: /products/categories/
    Template: products/category_list.html
    """
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(
            is_active=True,
            parent__isnull=True  # Only root categories
        ).prefetch_related(
            'children__children'  # 2 levels deep
        ).annotate(
            product_count=Count(
                'products',
                filter=Q(products__is_active=True)
            )
        ).order_by('order', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'دسته‌بندی‌ها'
        return context


class CategoryDetailView(WishlistContextMixin, FilterMixin, ListView):
    """
    Products in a specific category.
    
    URL: /products/category/<slug>/
    Template: products/category_detail.html
    """
    model = Product
    template_name = 'products/category_detail.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        self.category = get_object_or_404(
            Category.objects.filter(is_active=True),
            slug=self.kwargs['slug']
        )
        
        # Get all descendant categories
        category_ids = CategoryService.get_category_with_descendants(self.category.id)
        
        queryset = Product.objects.filter(
            is_active=True,
            category_id__in=category_ids
        ).select_related(
            'category', 'brand'
        ).prefetch_related(
            'images',
            'variants'
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        )
        
        # Apply additional filters from FilterMixin
        filters = self.get_filter_params()
        
        if filters.get('brand'):
            queryset = queryset.filter(brand__slug=filters['brand'])
        
        if filters.get('min_price'):
            try:
                queryset = queryset.filter(final_price__gte=Decimal(filters['min_price']))
            except:
                pass
        
        if filters.get('max_price'):
            try:
                queryset = queryset.filter(final_price__lte=Decimal(filters['max_price']))
            except:
                pass
        
        if filters.get('in_stock'):
            queryset = queryset.filter(
                Q(physical_inventory__quantity__gt=0) |
                Q(digital_inventory__is_available=True)
            ).distinct()
        
        if filters.get('has_discount'):
            queryset = queryset.filter(
                Q(discount_percent__gt=0) | Q(discount_amount__gt=0)
            )
        
        # Sorting
        sort_option = self.get_sort_option()
        sorting_map = {
            'newest': '-created_at',
            'price_low': 'final_price',
            'price_high': '-final_price',
            'rating': '-avg_rating',
            'popular': '-view_count',
            'bestseller': '-sold_count',
        }
        queryset = queryset.order_by(sorting_map.get(sort_option, '-created_at'))
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['category'] = self.category
        context['page_title'] = self.category.name
        
        # Subcategories
        context['subcategories'] = self.category.children.filter(
            is_active=True
        ).annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        ).order_by('order', 'name')
        
        # Parent categories (breadcrumbs)
        context['breadcrumbs'] = self._build_category_breadcrumbs()
        
        # Brands in this category
        category_ids = CategoryService.get_category_with_descendants(self.category.id)
        context['brands'] = Brand.objects.filter(
            is_active=True,
            products__category_id__in=category_ids,
            products__is_active=True
        ).distinct().annotate(
            product_count=Count('products', filter=Q(
                products__is_active=True,
                products__category_id__in=category_ids
            ))
        ).order_by('name')
        
        # Price range in category
        price_stats = Product.objects.filter(
            is_active=True,
            category_id__in=category_ids
        ).aggregate(
            min_price=Min('final_price'),
            max_price=Max('final_price')
        )
        context['price_range'] = {
            'min': int(price_stats['min_price'] or 0),
            'max': int(price_stats['max_price'] or 10000000),
        }
        
        # Current filters & sort
        context['current_filters'] = self.get_filter_params()
        context['current_sort'] = self.get_sort_option()
        
        # Sort options
        context['sort_options'] = [
            ('newest', 'جدیدترین'),
            ('price_low', 'ارزان‌ترین'),
            ('price_high', 'گران‌ترین'),
            ('rating', 'بیشترین امتیاز'),
            ('popular', 'پربازدیدترین'),
            ('bestseller', 'پرفروش‌ترین'),
        ]
        
        # SEO
        context['meta_title'] = self.category.meta_title or self.category.name
        context['meta_description'] = self.category.meta_description or self.category.description
        
        return context
    
    def _build_category_breadcrumbs(self):
        """Build breadcrumb trail for category."""
        breadcrumbs = [
            {'name': 'خانه', 'url': reverse('core:home')},
            {'name': 'فروشگاه', 'url': reverse('products:product_list')},
        ]
        
        # Add ancestor categories
        ancestors = []
        category = self.category
        while category:
            ancestors.insert(0, category)
            category = category.parent
        
        for i, cat in enumerate(ancestors):
            if i == len(ancestors) - 1:
                # Current category - no URL
                breadcrumbs.append({'name': cat.name, 'url': None})
            else:
                breadcrumbs.append({
                    'name': cat.name,
                    'url': reverse('products:category_detail', kwargs={'slug': cat.slug})
                })
        
        return breadcrumbs


# ═══════════════════════════════════════════════════════════════════════════════
# BRAND VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class BrandListView(ListView):
    """
    List all brands.
    
    URL: /products/brands/
    Template: products/brand_list.html
    """
    model = Brand
    template_name = 'products/brand_list.html'
    context_object_name = 'brands'
    
    def get_queryset(self):
        return Brand.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        ).filter(
            product_count__gt=0
        ).order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'برندها'
        
        # Group by first letter
        brands_by_letter = {}
        for brand in context['brands']:
            first_letter = brand.name[0].upper()
            if first_letter not in brands_by_letter:
                brands_by_letter[first_letter] = []
            brands_by_letter[first_letter].append(brand)
        
        context['brands_by_letter'] = dict(sorted(brands_by_letter.items()))
        
        return context


class BrandDetailView(WishlistContextMixin, FilterMixin, ListView):
    """
    Products of a specific brand.
    
    URL: /products/brand/<slug>/
    Template: products/brand_detail.html
    """
    model = Product
    template_name = 'products/brand_detail.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        self.brand = get_object_or_404(
            Brand.objects.filter(is_active=True),
            slug=self.kwargs['slug']
        )
        
        queryset = Product.objects.filter(
            is_active=True,
            brand=self.brand
        ).select_related(
            'category', 'brand'
        ).prefetch_related(
            'images', 'variants'
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        )
        
        # Apply filters
        filters = self.get_filter_params()
        
        if filters.get('category'):
            try:
                if filters['category'].isdigit():
                    category = Category.objects.get(pk=filters['category'])
                else:
                    category = Category.objects.get(slug=filters['category'])
                category_ids = CategoryService.get_category_with_descendants(category.id)
                queryset = queryset.filter(category_id__in=category_ids)
            except Category.DoesNotExist:
                pass
        
        if filters.get('min_price'):
            try:
                queryset = queryset.filter(final_price__gte=Decimal(filters['min_price']))
            except:
                pass
        
        if filters.get('max_price'):
            try:
                queryset = queryset.filter(final_price__lte=Decimal(filters['max_price']))
            except:
                pass
        
        # Sorting
        sort_option = self.get_sort_option()
        sorting_map = {
            'newest': '-created_at',
            'price_low': 'final_price',
            'price_high': '-final_price',
            'rating': '-avg_rating',
            'popular': '-view_count',
        }
        queryset = queryset.order_by(sorting_map.get(sort_option, '-created_at'))
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['brand'] = self.brand
        context['page_title'] = self.brand.name
        
        # Categories that have products from this brand
        context['categories'] = Category.objects.filter(
            is_active=True,
            products__brand=self.brand,
            products__is_active=True
        ).distinct().annotate(
            product_count=Count('products', filter=Q(
                products__is_active=True,
                products__brand=self.brand
            ))
        ).order_by('name')
        
        # Price range
        price_stats = Product.objects.filter(
            is_active=True,
            brand=self.brand
        ).aggregate(
            min_price=Min('final_price'),
            max_price=Max('final_price')
        )
        context['price_range'] = {
            'min': int(price_stats['min_price'] or 0),
            'max': int(price_stats['max_price'] or 10000000),
        }
        
        # Breadcrumbs
        context['breadcrumbs'] = [
            {'name': 'خانه', 'url': reverse('core:home')},
            {'name': 'فروشگاه', 'url': reverse('products:product_list')},
            {'name': 'برندها', 'url': reverse('products:brand_list')},
            {'name': self.brand.name, 'url': None},
        ]
        
        context['current_filters'] = self.get_filter_params()
        context['current_sort'] = self.get_sort_option()
        context['sort_options'] = [
            ('newest', 'جدیدترین'),
            ('price_low', 'ارزان‌ترین'),
            ('price_high', 'گران‌ترین'),
            ('rating', 'بیشترین امتیاز'),
            ('popular', 'پربازدیدترین'),
        ]
        
        return context


# ═══════════════════════════════════════════════════════════════════════════════
# TAG VIEW
# ═══════════════════════════════════════════════════════════════════════════════

# TAG VIEW
class TagDetailView(WishlistContextMixin, FilterMixin, ListView):
    """
    Products with a specific tag.
    
    URL: /products/tag/<slug>/
    Template: products/tag_detail.html
    """
    model = Product
    template_name = 'products/tag_detail.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        self.tag = get_object_or_404(
            ProductTag.objects.filter(is_active=True),
            slug=self.kwargs['slug']
        )

        queryset = Product.objects.filter(
            is_active=True,
            tags=self.tag
        ).select_related(
            'category', 'brand'
        ).prefetch_related(
            'images', 'variants'
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        ).distinct()

        filters = self.get_filter_params()

        if filters.get('min_price'):
            try:
                queryset = queryset.filter(final_price__gte=Decimal(filters['min_price']))
            except:
                pass

        if filters.get('max_price'):
            try:
                queryset = queryset.filter(final_price__lte=Decimal(filters['max_price']))
            except:
                pass

        if filters.get('in_stock'):
            queryset = queryset.filter(
                Q(physical_inventory__quantity__gt=0) |
                Q(digital_inventory__is_available=True)
            ).distinct()

        sort_option = self.get_sort_option()
        sorting_map = {
            'newest': '-created_at',
            'price_low': 'final_price',
            'price_high': '-final_price',
            'rating': '-avg_rating',
            'popular': '-view_count',
        }

        return queryset.order_by(sorting_map.get(sort_option, '-created_at'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['tag'] = self.tag
        context['page_title'] = f'برچسب: {self.tag.name}'
        context['current_filters'] = self.get_filter_params()
        context['current_sort'] = self.get_sort_option()
        context['sort_options'] = [
            ('newest', 'جدیدترین'),
            ('price_low', 'ارزان‌ترین'),
            ('price_high', 'گران‌ترین'),
            ('rating', 'بیشترین امتیاز'),
            ('popular', 'پربازدیدترین'),
        ]

        # Breadcrumbs
        context['breadcrumbs'] = [
            {'name': 'خانه', 'url': reverse('core:home')},
            {'name': 'فروشگاه', 'url': reverse('products:product_list')},
            {'name': f'برچسب: {self.tag.name}', 'url': None},
        ]

        return context


# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH VIEW
# ═══════════════════════════════════════════════════════════════════════════════

class ProductSearchView(WishlistContextMixin, FilterMixin, ListView):
    """
    Product search page.
    
    URL: /products/search/?q=...
    Template: products/search_results.html
    """
    model = Product
    template_name = 'products/search_results.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        query = self.get_search_query()
        if not query:
            return Product.objects.none()

        queryset = Product.objects.filter(
            is_active=True
        ).filter(
            Q(name__icontains=query) |
            Q(name_fa__icontains=query) |
            Q(short_description__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__name__icontains=query)
        ).select_related(
            'category', 'brand'
        ).prefetch_related(
            'images', 'variants'
        ).annotate(
            avg_rating=Avg('reviews__rating')
        ).distinct()

        filters = self.get_filter_params()

        if filters.get('min_price'):
            try:
                queryset = queryset.filter(final_price__gte=Decimal(filters['min_price']))
            except:
                pass

        if filters.get('max_price'):
            try:
                queryset = queryset.filter(final_price__lte=Decimal(filters['max_price']))
            except:
                pass

        sort_option = self.get_sort_option()
        sorting_map = {
            'newest': '-created_at',
            'price_low': 'final_price',
            'price_high': '-final_price',
            'rating': '-avg_rating',
        }

        return queryset.order_by(sorting_map.get(sort_option, '-created_at'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        query = self.get_search_query()

        context['search_query'] = query
        context['page_title'] = f'نتایج جستجو: {query}'
        context['current_filters'] = self.get_filter_params()
        context['current_sort'] = self.get_sort_option()

        # Breadcrumbs
        context['breadcrumbs'] = [
            {'name': 'خانه', 'url': reverse('core:home')},
            {'name': 'فروشگاه', 'url': reverse('products:product_list')},
            {'name': f'جستجو: {query}', 'url': None},
        ]

        return context


# ═══════════════════════════════════════════════════════════════════════════════
# WISHLIST VIEW (HTML PAGE)
# ═══════════════════════════════════════════════════════════════════════════════

class WishlistView(LoginRequiredMixin, TemplateView):
    """
    User wishlist page.
    
    URL: /products/wishlist/
    Template: products/wishlist.html
    """
    template_name = 'products/wishlist.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        wishlist_products = WishlistService.get_user_wishlist(self.request.user)

        context['wishlist_products'] = wishlist_products
        context['page_title'] = 'لیست علاقه‌مندی‌ها'

        return context


# ═══════════════════════════════════════════════════════════════════════════════
# COMPARE VIEW (HTML PAGE)
# ═══════════════════════════════════════════════════════════════════════════════

class CompareView(TemplateView):
    """
    Compare products.
    
    URL: /products/compare/
    Template: products/compare.html
    """
    template_name = 'products/compare.html'

    def get(self, request, *args, **kwargs):
        product_ids = request.GET.getlist('id')

        # Limit to 4 products for better UI
        product_ids = product_ids[:4]

        products = Product.objects.filter(
            id__in=product_ids,
            is_active=True
        ).prefetch_related(
            'images',
            'variants',
            'attributes',
        ).select_related(
            'brand', 'category'
        )

        context = self.get_context_data(products=products)
        context['page_title'] = 'مقایسه محصولات'

        return render(request, self.template_name, context)


# ═══════════════════════════════════════════════════════════════════════════════
# AJAX ENDPOINTS (NON-API, for frontend usage)
# ═══════════════════════════════════════════════════════════════════════════════

class ToggleWishlistAjaxView(LoginRequiredMixin, View):
    """
    Toggle wishlist for current user (AJAX).
    
    URL: /products/ajax/wishlist/toggle/
    """
    def post(self, request):
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id, is_active=True)

        result = WishlistService.toggle_wishlist(request.user, product)

        return JsonResponse({
            'success': True,
            'in_wishlist': result['in_wishlist']
        })


class VariantPriceAjaxView(View):
    """
    Return price of a specific variant based on selected attributes.
    
    URL: /products/ajax/variant-price/
    """
    def post(self, request):
        try:
            product_id = request.POST.get('product_id')
            selected_attrs = request.POST.getlist('attributes[]')

            variant = ProductService.get_variant_by_attributes(
                product_id=product_id,
                attribute_value_ids=selected_attrs
            )

            if not variant:
                return JsonResponse({'success': False, 'error': 'variant_not_found'})

            return JsonResponse({
                'success': True,
                'price': variant.final_price,
                'stock': variant.stock,
                'sku': variant.sku,
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


# ═══════════════════════════════════════════════════════════════════════════════
# PHYSICAL PRODUCT PAGES (Gaming & Peripherals)
# ═══════════════════════════════════════════════════════════════════════════════

class GamingProductsView(WishlistContextMixin, FilterMixin, ListView):
    """
    Gaming products listing page with comprehensive filtering.
    Similar to Digikala product listing.
    
    URL: /gaming-products/
    Template: core/gaming_products.html
    """
    model = Product
    template_name = 'core/gaming_products.html'
    context_object_name = 'products'
    paginate_by = 50
    
    def get_queryset(self):
        # Get gaming products only
        queryset = Product.objects.filter(
            is_active=True,
            product_type=Product.ProductType.PHYSICAL,
            sub_type=Product.ProductSubType.GAMING
        ).select_related(
            'category', 'brand'
        ).prefetch_related(
            'images'
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        )
        
        # Apply filters
        filters = self.get_filter_params()
        
        # Brand filter
        if filters.get('brand'):
            brand_slugs = self.request.GET.getlist('brand')
            if brand_slugs:
                queryset = queryset.filter(brand__slug__in=brand_slugs)
        
        # Price range
        if filters.get('min_price'):
            try:
                min_price = int(filters['min_price'])
                queryset = queryset.filter(price__gte=min_price)
            except:
                pass
        
        if filters.get('max_price'):
            try:
                max_price = int(filters['max_price'])
                queryset = queryset.filter(price__lte=max_price)
            except:
                pass
        
        # In stock filter
        if filters.get('in_stock'):
            queryset = queryset.filter(stock__gt=0)
        
        # Has discount filter
        if filters.get('has_discount'):
            queryset = queryset.filter(original_price__isnull=False, original_price__gt=0)
        
        # Search in specifications
        spec_filters = {}
        for key in self.request.GET.keys():
            if key.startswith('spec_'):
                spec_key = key.replace('spec_', '')
                spec_values = self.request.GET.getlist(key)
                if spec_values:
                    # Filter by specifications JSON field
                    for value in spec_values:
                        queryset = queryset.filter(
                            specifications__has_key=spec_key
                        )
        
        # Search query
        search_query = self.get_search_query()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(name_en__icontains=search_query) |
                Q(short_description__icontains=search_query) |
                Q(brand__name__icontains=search_query)
            ).distinct()
        
        # Apply sorting
        sort_option = self.get_sort_option()
        if sort_option == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_option == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort_option == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort_option == 'popular':
            queryset = queryset.order_by('-sales_count', '-view_count')
        elif sort_option == 'rating':
            queryset = queryset.order_by('-avg_rating')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all gaming brands for filter
        context['brands'] = Brand.objects.filter(
            products__sub_type=Product.ProductSubType.GAMING,
            is_active=True
        ).distinct().order_by('name')
        
        # Get price range
        price_range = Product.objects.filter(
            is_active=True,
            product_type=Product.ProductType.PHYSICAL,
            sub_type=Product.ProductSubType.GAMING
        ).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        context['min_price'] = price_range['min_price'] or 0
        context['max_price'] = price_range['max_price'] or 100000000
        
        # Get all unique specification keys for filtering
        all_products = Product.objects.filter(
            is_active=True,
            product_type=Product.ProductType.PHYSICAL,
            sub_type=Product.ProductSubType.GAMING
        )
        
        # Collect all specification keys and their values
        spec_filters = {}
        for product in all_products:
            if product.specifications:
                for key, value in product.specifications.items():
                    if key not in spec_filters:
                        spec_filters[key] = set()
                    spec_filters[key].add(str(value))
        
        # Convert sets to sorted lists
        context['spec_filters'] = {k: sorted(list(v)) for k, v in spec_filters.items()}
        
        # Current filters
        context['current_filters'] = self.get_filter_params()
        context['current_sort'] = self.get_sort_option()
        context['search_query'] = self.get_search_query()
        
        # Page title
        context['page_title'] = 'محصولات گیمینگ'
        context['page_description'] = 'تجهیزات و لوازم گیمینگ حرفه‌ای'
        
        return context


class BuyProductsView(WishlistContextMixin, FilterMixin, ListView):
    """
    Peripheral/accessory products listing page with comprehensive filtering.
    Similar to Digikala product listing.
    
    URL: /buy-products/
    Template: products/buy_products.html
    """
    model = Product
    template_name = 'products/buy_products.html'
    context_object_name = 'products'
    paginate_by = 50
    
    def get_queryset(self):
        # Get peripheral products only
        queryset = Product.objects.filter(
            is_active=True,
            product_type=Product.ProductType.PHYSICAL,
            sub_type=Product.ProductSubType.ACCESSORY
        ).select_related(
            'category', 'brand'
        ).prefetch_related(
            'images'
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        )
        
        # Apply filters
        filters = self.get_filter_params()
        
        # Brand filter
        if filters.get('brand'):
            brand_slugs = self.request.GET.getlist('brand')
            if brand_slugs:
                queryset = queryset.filter(brand__slug__in=brand_slugs)
        
        # Price range
        if filters.get('min_price'):
            try:
                min_price = int(filters['min_price'])
                queryset = queryset.filter(price__gte=min_price)
            except:
                pass
        
        if filters.get('max_price'):
            try:
                max_price = int(filters['max_price'])
                queryset = queryset.filter(price__lte=max_price)
            except:
                pass
        
        # In stock filter
        if filters.get('in_stock'):
            queryset = queryset.filter(stock__gt=0)
        
        # Has discount filter
        if filters.get('has_discount'):
            queryset = queryset.filter(original_price__isnull=False, original_price__gt=0)
        
        # Search in specifications
        spec_filters = {}
        for key in self.request.GET.keys():
            if key.startswith('spec_'):
                spec_key = key.replace('spec_', '')
                spec_values = self.request.GET.getlist(key)
                if spec_values:
                    # Filter by specifications JSON field
                    for value in spec_values:
                        queryset = queryset.filter(
                            specifications__has_key=spec_key
                        )
        
        # Search query
        search_query = self.get_search_query()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(name_en__icontains=search_query) |
                Q(short_description__icontains=search_query) |
                Q(brand__name__icontains=search_query)
            ).distinct()
        
        # Apply sorting
        sort_option = self.get_sort_option()
        if sort_option == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_option == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort_option == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort_option == 'popular':
            queryset = queryset.order_by('-sales_count', '-view_count')
        elif sort_option == 'rating':
            queryset = queryset.order_by('-avg_rating')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all peripheral brands for filter
        context['brands'] = Brand.objects.filter(
            products__sub_type=Product.ProductSubType.ACCESSORY,
            is_active=True
        ).distinct().order_by('name')
        
        # Get price range
        price_range = Product.objects.filter(
            is_active=True,
            product_type=Product.ProductType.PHYSICAL,
            sub_type=Product.ProductSubType.ACCESSORY
        ).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        context['min_price'] = price_range['min_price'] or 0
        context['max_price'] = price_range['max_price'] or 100000000
        
        # Get all unique specification keys for filtering
        all_products = Product.objects.filter(
            is_active=True,
            product_type=Product.ProductType.PHYSICAL,
            sub_type=Product.ProductSubType.ACCESSORY
        )
        
        # Collect all specification keys and their values
        spec_filters = {}
        for product in all_products:
            if product.specifications:
                for key, value in product.specifications.items():
                    if key not in spec_filters:
                        spec_filters[key] = set()
                    spec_filters[key].add(str(value))
        
        # Convert sets to sorted lists
        context['spec_filters'] = {k: sorted(list(v)) for k, v in spec_filters.items()}
        
        # Current filters
        context['current_filters'] = self.get_filter_params()
        context['current_sort'] = self.get_sort_option()
        context['search_query'] = self.get_search_query()
        
        # Page title
        context['page_title'] = 'محصولات جانبی'
        context['page_description'] = 'لوازم جانبی کامپیوتر و موبایل'
        
        return context


# ═══════════════════════════════════════════════════════════════════════════════
# END OF FILE
# ═══════════════════════════════════════════════════════════════════════════════
