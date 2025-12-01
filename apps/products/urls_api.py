# apps/products/urls_api.py

from django.urls import path
from . import api_views

app_name = 'products_api'

urlpatterns = [
    # ═══════════════════════════════════════════════════════════════════════════
    # PRODUCTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    # List products (with filters, search, pagination)
    path('products/', api_views.ProductListAPIView.as_view(), name='product_list'),
    
    # Product detail
    path('products/<int:pk>/', api_views.ProductDetailAPIView.as_view(), name='product_detail'),
    path('products/slug/<slug:slug>/', api_views.ProductDetailBySlugAPIView.as_view(), name='product_detail_slug'),
    
    # Product variants
    path('products/<int:pk>/variants/', api_views.ProductVariantsAPIView.as_view(), name='product_variants'),
    
    # Product reviews
    path('products/<int:pk>/reviews/', api_views.ProductReviewsAPIView.as_view(), name='product_reviews'),
    
    # Related products
    path('products/<int:pk>/related/', api_views.RelatedProductsAPIView.as_view(), name='product_related'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CATEGORIES
    # ═══════════════════════════════════════════════════════════════════════════
    
    # List all categories (tree structure)
    path('categories/', api_views.CategoryListAPIView.as_view(), name='category_list'),
    
    # Category detail
    path('categories/<int:pk>/', api_views.CategoryDetailAPIView.as_view(), name='category_detail'),
    path('categories/slug/<slug:slug>/', api_views.CategoryDetailBySlugAPIView.as_view(), name='category_detail_slug'),
    
    # Products in category
    path('categories/<int:pk>/products/', api_views.CategoryProductsAPIView.as_view(), name='category_products'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # BRANDS
    # ═══════════════════════════════════════════════════════════════════════════
    
    path('brands/', api_views.BrandListAPIView.as_view(), name='brand_list'),
    path('brands/<int:pk>/', api_views.BrandDetailAPIView.as_view(), name='brand_detail'),
    path('brands/<int:pk>/products/', api_views.BrandProductsAPIView.as_view(), name='brand_products'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SEARCH & FILTERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    path('search/', api_views.ProductSearchAPIView.as_view(), name='search'),
    path('search/suggestions/', api_views.SearchSuggestionsAPIView.as_view(), name='search_suggestions'),
    path('filters/', api_views.AvailableFiltersAPIView.as_view(), name='available_filters'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # REVIEWS
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Create review
    path('reviews/create/', api_views.ReviewCreateAPIView.as_view(), name='review_create'),
    
    # Update/Delete own review
    path('reviews/<int:pk>/', api_views.ReviewDetailAPIView.as_view(), name='review_detail'),
    
    # Mark review helpful
    path('reviews/<int:pk>/helpful/', api_views.ReviewHelpfulAPIView.as_view(), name='review_helpful'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # WISHLIST
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Get user's wishlist
    path('wishlist/', api_views.WishlistAPIView.as_view(), name='wishlist'),
    
    # Add to wishlist
    path('wishlist/add/', api_views.WishlistAddAPIView.as_view(), name='wishlist_add'),
    
    # Remove from wishlist
    path('wishlist/remove/', api_views.WishlistRemoveAPIView.as_view(), name='wishlist_remove'),
    
    # Toggle wishlist (add if not exists, remove if exists)
    path('wishlist/toggle/', api_views.WishlistToggleAPIView.as_view(), name='wishlist_toggle'),
    
    # Clear wishlist
    path('wishlist/clear/', api_views.WishlistClearAPIView.as_view(), name='wishlist_clear'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RECENTLY VIEWED
    # ═══════════════════════════════════════════════════════════════════════════
    
    path('recently-viewed/', api_views.RecentlyViewedAPIView.as_view(), name='recently_viewed'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # COMPARE
    # ═══════════════════════════════════════════════════════════════════════════
    
    path('compare/', api_views.CompareProductsAPIView.as_view(), name='compare'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # INVENTORY CHECK (Public)
    # ═══════════════════════════════════════════════════════════════════════════
    
    path('products/<int:pk>/stock/', api_views.ProductStockAPIView.as_view(), name='product_stock'),
]
