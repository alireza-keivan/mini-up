# apps/products/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, Http404
from django.db.models import Q, Prefetch, Avg, Count, Min, Max
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.utils.decorators import method_decorator
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
    Template: products/list.html
    """
    model = Product
    template_name = 'products/list.html'
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
                    Q(price__gte=min_price) | 
                    Q(variants__price__gte=min_price)
                ).distinct()
            except:
                pass
        
        if filters.get('max_price'):
            try:
                max_price = Decimal(filters['max_price'])
                queryset = queryset.filter(
                    Q(price__lte=max_price) | 
                    Q(variants__price__lte=max_price)
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
            'price_low': 'price',
            'price_high': '-price',
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
            min_price=Min('price'),
            max_price=Max('price')
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

@method_decorator(ensure_csrf_cookie, name='dispatch')
class ProductDetailView(WishlistContextMixin, DetailView):
    """
    Product detail page.
    
    URL: /products/product/<slug>/
    Template: products/detail.html
    """
    model = Product
    template_name = 'products/detail.html'
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
            Prefetch(
                'reviews',
                queryset=ProductReview.objects.filter(
                    is_approved=True
                ).select_related('user').order_by('-created_at')
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
        
        return obj
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        # All product images
        context['images'] = product.images.all().order_by('sort_order')
        
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
        
        # All approved reviews for display
        context['reviews'] = ProductReview.objects.filter(
            product=product,
            is_approved=True
        ).select_related('user').order_by('-created_at')
        
        # Recent reviews (already prefetched)
        context['recent_reviews'] = context['reviews'][:5]
        
        # User's review (if exists)
        if self.request.user.is_authenticated:
            context['user_review'] = ProductReview.objects.filter(
                product=product,
                user=self.request.user
            ).first()
            
            # Can user review this product? (has purchased but not reviewed yet)
            context['can_review'] = not context['user_review']
        
        # Related products
        context['related_products'] = ProductService.get_related_products(
            product=product,
            limit=8
        )
        
        # Recently viewed (excluding current)
        session_key = self.request.session.session_key
        recently_viewed = RecentlyViewedService.get_recently_viewed(
            user=self.request.user if self.request.user.is_authenticated else None,
            session_key=session_key,
            limit=7  # Get 7 to exclude current and show 6
        )
        # Exclude current product
        context['recently_viewed'] = [p for p in recently_viewed if p.id != product.id][:6]
        
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
            return {
                'in_stock': product.is_in_stock,
                'quantity': product.stock,
                'low_stock': product.is_low_stock,
                'allow_backorder': False,
                'max_per_order': 10,
            }
        else:  # digital
            return {
                'in_stock': True,  # Digital products always available
                'quantity': None,  # Unlimited for digital
                'low_stock': False,
                'allow_backorder': False,
                'max_per_order': 1,
            }
    
    def _build_breadcrumbs(self, product):
        """Build breadcrumb trail for product."""
        breadcrumbs = [
            {'name': 'خانه', 'url': reverse('core:home')},
            {'name': 'فروشگاه', 'url': reverse('products:list')},
        ]
        
        # Add category (flat structure, no hierarchy)
        if product.category:
            breadcrumbs.append({
                'name': product.category.name,
                'url': reverse('products:category_detail', kwargs={'slug': product.category.slug})
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
    Template: products/category.html
    """
    model = Product
    template_name = 'products/category.html'
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
                queryset = queryset.filter(price__gte=Decimal(filters['min_price']))
            except:
                pass
        
        if filters.get('max_price'):
            try:
                queryset = queryset.filter(price__lte=Decimal(filters['max_price']))
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
            'price_low': 'price',
            'price_high': '-price',
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
            min_price=Min('price'),
            max_price=Max('price')
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
                queryset = queryset.filter(price__gte=Decimal(filters['min_price']))
            except:
                pass
        
        if filters.get('max_price'):
            try:
                queryset = queryset.filter(price__lte=Decimal(filters['max_price']))
            except:
                pass
        
        # Sorting
        sort_option = self.get_sort_option()
        sorting_map = {
            'newest': '-created_at',
            'price_low': 'price',
            'price_high': '-price',
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
            min_price=Min('price'),
            max_price=Max('price')
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
                queryset = queryset.filter(price__gte=Decimal(filters['min_price']))
            except:
                pass

        if filters.get('max_price'):
            try:
                queryset = queryset.filter(price__lte=Decimal(filters['max_price']))
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
            'price_low': 'price',
            'price_high': '-price',
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
                queryset = queryset.filter(price__gte=Decimal(filters['min_price']))
            except:
                pass

        if filters.get('max_price'):
            try:
                queryset = queryset.filter(price__lte=Decimal(filters['max_price']))
            except:
                pass

        sort_option = self.get_sort_option()
        sorting_map = {
            'newest': '-created_at',
            'price_low': 'price',
            'price_high': '-price',
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

class WishlistView(TemplateView):
    """
    User wishlist page.
    
    URL: /products/wishlist/
    Template: products/wishlist.html
    """
    template_name = 'products/wishlist.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            wishlist_data = WishlistService.get_user_wishlist(self.request.user)
            # get_user_wishlist returns a dict with 'items' key
            wishlist_items = wishlist_data.get('items', [])
            
            # Filter out products with empty, invalid, or None slugs
            valid_wishlist = []
            for item in wishlist_items:
                if hasattr(item, 'product') and item.product and hasattr(item.product, 'slug'):
                    if item.product.slug and item.product.slug.strip():
                        valid_wishlist.append(item)
            context['wishlist_products'] = valid_wishlist
        else:
            context['wishlist_products'] = []
        
        context['page_title'] = 'لیست علاقه‌مندی‌ها'

        return context


class WishlistToggleView(View):
    """
    API endpoint to toggle product in wishlist.
    
    URL: /products/api/wishlist/toggle/
    Method: POST
    Body: { "product_id": <int> }
    Response: { "success": true, "added": true/false }
    """
    
    def post(self, request, *args, **kwargs):
        import json
        from django.http import JsonResponse
        from .models import Product, Wishlist
        
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
        
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            
            if not product_id:
                return JsonResponse({'success': False, 'error': 'Product ID required'}, status=400)
            
            product = Product.objects.get(id=product_id, is_active=True)
            
            # Check if item already exists in wishlist
            wishlist_item = Wishlist.objects.filter(
                user=request.user,
                product=product
            ).first()
            
            if wishlist_item:
                # Remove from wishlist
                wishlist_item.delete()
                added = False
            else:
                # Add to wishlist
                Wishlist.objects.create(
                    user=request.user,
                    product=product
                )
                added = True
            
            return JsonResponse({
                'success': True,
                'added': added,
                'message': 'به لیست علاقه‌مندی‌ها اضافه شد' if added else 'از لیست علاقه‌مندی‌ها حذف شد'
            })
            
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


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
# REVIEW SUBMISSION
# ═══════════════════════════════════════════════════════════════════════════════

class AddReviewView(LoginRequiredMixin, View):
    """
    Handle product review submissions
    Simple POST-only view using product ID
    """
    login_url = '/accounts/login/'
    
    def post(self, request, product_id):
        """Handle review submission"""
        try:
            # Get the product
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            messages.error(request, 'محصول مورد نظر یافت نشد.')
            return redirect('products:list')
        
        # Get form data
        rating = request.POST.get('rating', '').strip()
        comment = request.POST.get('comment', '').strip()
        
        # Validate rating
        try:
            rating_value = int(rating)
            if not (1 <= rating_value <= 5):
                raise ValueError()
        except (ValueError, TypeError):
            messages.error(request, 'لطفاً امتیاز معتبر (۱ تا ۵) را انتخاب کنید.')
            return redirect('products:detail', slug=product.slug)
        
        # Validate comment
        if not comment or len(comment) < 10:
            messages.error(request, 'لطفاً نظر خود را با حداقل ۱۰ کاراکتر وارد کنید.')
            return redirect('products:detail', slug=product.slug)
        
        # Check for duplicate review
        existing_review = ProductReview.objects.filter(
            product=product,
            user=request.user
        ).first()
        
        if existing_review:
            messages.warning(request, 'شما قبلاً برای این محصول نظر ثبت کرده‌اید.')
            return redirect('products:detail', slug=product.slug)
        
        # Create new review
        ProductReview.objects.create(
            product=product,
            user=request.user,
            rating=rating_value,
            comment=comment,
            is_approved=False
        )
        
        messages.success(request, 'نظر شما با موفقیت ثبت شد و پس از تایید نمایش داده خواهد شد.')
        return redirect('products:detail', slug=product.slug)


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
                'price': variant.price,
                'stock': variant.stock,
                'sku': variant.sku,
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


# ═══════════════════════════════════════════════════════════════════════════════
# VIRTUAL SERVICES
# ═══════════════════════════════════════════════════════════════════════════════

class VirtualServicesListView(WishlistContextMixin, ListView):
    """
    Display all virtual services with carousel layout.
    """
    model = Product
    template_name = 'products/virtual_services_list.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        return Product.objects.filter(
            product_type='virtual',
            is_active=True
        ).select_related('category').order_by('-is_featured', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_products = self.get_queryset()
        
        context['featured_products'] = all_products.filter(is_featured=True)
        context['all_products'] = all_products
        context['page_title'] = 'خدمات مجازی'
        
        return context


class VirtualServiceDetailView(WishlistContextMixin, DetailView):
    """
    Detail view for a single virtual service.
    Similar to ProductDetailView but without colors and technical specs.
    """
    model = Product
    template_name = 'products/virtual_service_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Product.objects.filter(
            product_type='virtual',
            is_active=True
        ).select_related(
            'category'
        ).prefetch_related(
            'images',
            Prefetch(
                'reviews',
                queryset=ProductReview.objects.filter(is_approved=True).select_related('user').order_by('-created_at')
            )
        )
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Increment view count
        Product.objects.filter(pk=obj.pk).update(view_count=obj.view_count + 1)
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        # Related products (same category)
        context['related_products'] = Product.objects.filter(
            category=product.category,
            product_type='virtual',
            is_active=True
        ).exclude(
            id=product.id
        ).order_by('-is_featured', '-created_at')[:8]
        
        # Reviews
        context['reviews'] = product.reviews.filter(is_approved=True).order_by('-created_at')
        context['reviews_count'] = context['reviews'].count()
        
        # Rating statistics
        if context['reviews_count'] > 0:
            rating_counts = {i: 0 for i in range(1, 6)}
            for review in context['reviews']:
                rating_counts[review.rating] += 1
            
            context['review_stats'] = {
                'total': context['reviews_count'],
                'average': product.average_rating,
                'rating_5': rating_counts[5],
                'rating_4': rating_counts[4],
                'rating_3': rating_counts[3],
                'rating_2': rating_counts[2],
                'rating_1': rating_counts[1],
            }
        
        # Recently viewed
        if self.request.user.is_authenticated:
            RecentlyViewedService.add_viewed_product(
                user=self.request.user,
                product=product
            )
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            RecentlyViewedService.add_viewed_product(
                user=None,
                product=product,
                session_key=session_key
            )
        
        context['page_title'] = product.name
        
        return context


# ═══════════════════════════════════════════════════════════════════════════════
# END OF FILE
# ═══════════════════════════════════════════════════════════════════════════════
