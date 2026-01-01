# apps/products/api_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db.models import Q, Prefetch
from decimal import Decimal

from .models import (
    Category, Brand, Product, #ProductVariant, ProductImage,
    ProductReview, Wishlist, #DigitalInventory
)
from .serializers import (
    CategorySerializer, CategoryTreeSerializer, CategoryDetailSerializer,
    BrandSerializer, BrandDetailSerializer,
    ProductListSerializer, ProductDetailSerializer, ProductCardSerializer,
    ProductVariantSerializer,
    ProductReviewSerializer, ProductReviewCreateSerializer,
    WishlistSerializer, WishlistItemSerializer,
)
from .services import (
    CategoryService, ProductService, InventoryService,
    ReviewService, WishlistService, RecentlyViewedService
)

import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_pagination_params(request, default_limit=20, max_limit=100):
    """Extract pagination parameters from request."""
    try:
        page = max(1, int(request.query_params.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    
    try:
        limit = min(max_limit, max(1, int(request.query_params.get('limit', default_limit))))
    except (ValueError, TypeError):
        limit = default_limit
    
    return page, limit


def build_pagination_response(data, page, limit, total_count):
    """Build standardized pagination response."""
    total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
    
    return {
        'success': True,
        'data': data,
        'pagination': {
            'page': page,
            'limit': limit,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1,
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT APIs
# ═══════════════════════════════════════════════════════════════════════════════

class ProductListAPIView(APIView):
    """
    Get list of products with filters and pagination.
    
    GET /api/v1/products/
    
    Query Parameters:
        - page: Page number (default: 1)
        - limit: Items per page (default: 20, max: 100)
        - category: Category ID or slug
        - brand: Brand ID or slug
        - min_price: Minimum price
        - max_price: Maximum price
        - min_rating: Minimum rating (1-5)
        - in_stock: Filter in-stock only (true/false)
        - sort: Sorting option (newest, price_low, price_high, rating, popular, bestseller)
        - q: Search query
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        page, limit = get_pagination_params(request)
        
        # Build filters from query params
        filters = {}
        
        # Category filter
        category = request.query_params.get('category')
        if category:
            filters['category'] = category
        
        # Brand filter
        brand = request.query_params.get('brand')
        if brand:
            filters['brand'] = brand
        
        # Price range
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if min_price:
            try:
                filters['min_price'] = Decimal(min_price)
            except:
                pass
        if max_price:
            try:
                filters['max_price'] = Decimal(max_price)
            except:
                pass
        
        # Rating filter
        min_rating = request.query_params.get('min_rating')
        if min_rating:
            try:
                filters['min_rating'] = float(min_rating)
            except:
                pass
        
        # Stock filter
        in_stock = request.query_params.get('in_stock')
        if in_stock and in_stock.lower() == 'true':
            filters['in_stock'] = True
        
        # Sorting
        sort = request.query_params.get('sort', 'newest')
        
        # Search query
        search_query = request.query_params.get('q', '').strip()
        
        # Get products using service
        result = ProductService.get_filtered_products(
            filters=filters,
            sort_by=sort,
            search_query=search_query,
            page=page,
            per_page=limit,
            user=request.user if request.user.is_authenticated else None
        )
        
        # Serialize
        serializer = ProductListSerializer(
            result['products'],
            many=True,
            context={'request': request}
        )
        
        return Response(build_pagination_response(
            data=serializer.data,
            page=page,
            limit=limit,
            total_count=result['total_count']
        ))


class ProductDetailAPIView(APIView):
    """
    Get product details by ID.
    
    GET /api/v1/products/<pk>/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        queryset = ProductService.get_detail_queryset()
        product = get_object_or_404(queryset, pk=pk, is_active=True)
        
        # Track view
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        RecentlyViewedService.add_viewed_product(
            user=request.user if request.user.is_authenticated else None,
            product=product,
            session_key=session_key
        )
        
        # Increment view count
        ProductService.increment_view_count(product)
        
        serializer = ProductDetailSerializer(product, context={'request': request})
        
        return Response({
            'success': True,
            'data': serializer.data
        })


class ProductDetailBySlugAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        queryset = ProductService.get_detail_queryset()
        product = get_object_or_404(queryset, slug=slug, is_active=True)

        # Track recently viewed
        session_key = request.session.session_key or request.session.create()
        RecentlyViewedService.add_viewed_product(
            user=request.user if request.user.is_authenticated else None,
            product=product,
            session_key=request.session.session_key
        )

        # Increment view count
        ProductService.increment_view_count(product)

        serializer = ProductDetailSerializer(product, context={'request': request})
        return Response({'success': True, 'data': serializer.data})


# =====================================================================
# PRODUCT VARIANTS
# =====================================================================

class ProductVariantsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk, is_active=True)
        variants = product.variants.filter(is_active=True).order_by('price')

        serializer = ProductVariantSerializer(variants, many=True)
        return Response({'success': True, 'data': serializer.data})


# =====================================================================
# PRODUCT REVIEWS
# =====================================================================

class ProductReviewsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        page, limit = 1, 20
        try:
            page = max(1, int(request.query_params.get('page', 1)))
            limit = min(100, int(request.query_params.get('limit', 20)))
        except:
            pass

        result = ReviewService.get_reviews_for_product(
            product_id=pk,
            page=page,
            per_page=limit
        )

        serializer = ProductReviewSerializer(result['reviews'], many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': result['pagination']
        })


# =====================================================================
# RELATED PRODUCTS
# =====================================================================

class RelatedProductsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        result = ProductService.get_related_products(product_id=pk, limit=12)
        serializer = ProductCardSerializer(result, many=True)
        return Response({'success': True, 'data': serializer.data})


# =====================================================================
# CATEGORY APIS
# =====================================================================

class CategoryListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = CategoryService.get_category_tree()
        serializer = CategoryTreeSerializer(categories, many=True)
        return Response({'success': True, 'data': serializer.data})


class CategoryDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk, is_active=True)
        serializer = CategoryDetailSerializer(category)
        return Response({'success': True, 'data': serializer.data})


class CategoryDetailBySlugAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug, is_active=True)
        serializer = CategoryDetailSerializer(category)
        return Response({'success': True, 'data': serializer.data})


class CategoryProductsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        page, limit = 1, 20
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))

        result = ProductService.get_products_by_category(
            category_id=pk,
            page=page,
            per_page=limit,
            user=request.user if request.user.is_authenticated else None
        )

        serializer = ProductListSerializer(result['products'], many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': result['pagination']
        })


# =====================================================================
# BRAND APIS
# =====================================================================

class BrandListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        brands = Brand.objects.filter(is_active=True).order_by('name')
        serializer = BrandSerializer(brands, many=True)
        return Response({'success': True, 'data': serializer.data})


class BrandDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        brand = get_object_or_404(Brand, pk=pk, is_active=True)
        serializer = BrandDetailSerializer(brand)
        return Response({'success': True, 'data': serializer.data})


class BrandProductsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        page, limit = 1, 20
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))

        result = ProductService.get_products_by_brand(
            brand_id=pk,
            page=page,
            per_page=limit,
            user=request.user if request.user.is_authenticated else None
        )

        serializer = ProductListSerializer(result['products'], many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': result['pagination']
        })


# =====================================================================
# SEARCH APIS
# =====================================================================

class ProductSearchAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        page, limit = 1, 20
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))

        result = ProductService.search_products(
            query=q,
            page=page,
            per_page=limit,
            user=request.user if request.user.is_authenticated else None
        )

        serializer = ProductCardSerializer(result['products'], many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': result['pagination']
        })


class SearchSuggestionsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        suggestions = ProductService.get_search_suggestions(q, limit=10)
        return Response({'success': True, 'data': suggestions})


class AvailableFiltersAPIView(APIView):
    """Return filters available for current products."""
    permission_classes = [AllowAny]

    def get(self, request):
        filters = ProductService.get_available_filters()
        return Response({'success': True, 'data': filters})


# =====================================================================
# REVIEW APIs (CRUD)
# =====================================================================

class ReviewCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProductReviewCreateSerializer(
            data=request.data,
            context={'user': request.user}
        )
        serializer.is_valid(raise_exception=True)

        review = ReviewService.create_review(
            user=request.user,
            **serializer.validated_data
        )

        return Response({
            'success': True,
            'message': 'نظر شما ثبت شد',
            'data': ProductReviewSerializer(review).data
        }, status=201)


class ReviewDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        review = get_object_or_404(ProductReview, pk=pk, user=request.user)

        serializer = ProductReviewCreateSerializer(
            instance=review,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        ReviewService.update_review(review, serializer.validated_data)

        return Response({'success': True, 'data': ProductReviewSerializer(review).data})

    def delete(self, request, pk):
        review = get_object_or_404(ProductReview, pk=pk, user=request.user)
        review.delete()
        return Response({'success': True, 'message': 'نظر حذف شد'})


class ReviewHelpfulAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        review = get_object_or_404(ProductReview, pk=pk)
        ReviewService.toggle_helpful(review, request.user)
        return Response({'success': True})


# =====================================================================
# WISHLIST APIs
# =====================================================================

class WishlistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get wishlist items directly without pagination
        wishlist_items = Wishlist.objects.filter(user=request.user).select_related(
            'product', 'product__category', 'product__brand'
        ).order_by('-created_at')
        
        # Serialize the items - return simple product IDs for the JavaScript
        data = []
        for item in wishlist_items:
            data.append({
                'id': item.id,
                'product_id': item.product.id,
                'product': {
                    'id': item.product.id,
                    'name': item.product.name,
                    'slug': item.product.slug,
                    'price': str(item.product.price),
                }
            })
        
        return Response({'success': True, 'data': data})


class WishlistAddAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        try:
            from .models import Product
            product = Product.objects.get(id=product_id)
            wishlist_item, created = WishlistService.add_to_wishlist(request.user, product)
            return Response({
                'success': True, 
                'message': 'محصول به علاقه‌مندی‌ها اضافه شد',
                'data': {'product_id': product.id, 'created': created}
            })
        except Product.DoesNotExist:
            return Response({'success': False, 'message': 'محصول یافت نشد'}, status=404)


class WishlistRemoveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        try:
            from .models import Product
            product = Product.objects.get(id=product_id)
            removed = WishlistService.remove_from_wishlist(request.user, product)
            return Response({
                'success': True, 
                'message': 'محصول از علاقه‌مندی‌ها حذف شد',
                'data': {'product_id': product.id, 'removed': removed}
            })
        except Product.DoesNotExist:
            return Response({'success': False, 'message': 'محصول یافت نشد'}, status=404)


class WishlistToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        try:
            from .models import Product
            product = Product.objects.get(id=product_id)
            result = WishlistService.toggle_wishlist(request.user, product)
            return Response({'success': True, 'data': result})
        except Product.DoesNotExist:
            return Response({'success': False, 'message': 'محصول یافت نشد'}, status=404)


class WishlistClearAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        WishlistService.clear_wishlist(request.user)
        return Response({'success': True, 'message': 'Wishlist cleared'})


# =====================================================================
# RECENTLY VIEWED
# =====================================================================

class RecentlyViewedAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        session_key = request.session.session_key or request.session.create()
        result = RecentlyViewedService.get_recently_viewed(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key
        )

        serializer = ProductCardSerializer(result, many=True)
        return Response({'success': True, 'data': serializer.data})


# =====================================================================
# COMPARE
# =====================================================================

class CompareProductsAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ids = request.data.get('ids', [])
        products = ProductService.get_products_for_compare(ids)
        serializer = ProductDetailSerializer(products, many=True)
        return Response({'success': True, 'data': serializer.data})


# =====================================================================
# STOCK CHECK
# =====================================================================

class ProductStockAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        stock = InventoryService.get_stock_status(product_id=pk)
        return Response({'success': True, 'data': stock})