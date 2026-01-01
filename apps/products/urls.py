# apps/products/urls.py

from django.urls import path, re_path
from . import views

app_name = 'products'

urlpatterns = [
    # ═══════════════════════════════════════════════════════════════════════════
    # SHOP & CATALOG PAGES
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Main shop page (product listing with filters)
    path('', views.ProductListView.as_view(), name='list'),
    path('shop/', views.ProductListView.as_view(), name='shop'),
    
    # Product detail page - supports Unicode slugs
    re_path(r'^product/(?P<slug>[\w\-]+)/$', views.ProductDetailView.as_view(), name='detail'),
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='detail_by_id'),
    
    # Review submission - simple path with product ID
    path('review/add/<int:product_id>/', views.AddReviewView.as_view(), name='add_review'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CATEGORY PAGES
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Category listing
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    
    # Category detail (products in category) - supports Unicode slugs
    re_path(r'^category/(?P<slug>[\w\-]+)/$', views.CategoryDetailView.as_view(), name='category_detail'),
    # Backwards-compatible alias
    re_path(r'^category/(?P<slug>[\w\-]+)/$', views.CategoryDetailView.as_view(), name='category'),
    path('category/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail_by_id'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # BRAND PAGES
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Brand listing
    path('brands/', views.BrandListView.as_view(), name='brand_list'),
    
    # Brand detail (products by brand)
    path('brand/<slug:slug>/', views.BrandDetailView.as_view(), name='brand_detail'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SEARCH
    # ═══════════════════════════════════════════════════════════════════════════
    
    path('search/', views.ProductSearchView.as_view(), name='search'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # WISHLIST (HTML)
    # ═══════════════════════════════════════════════════════════════════════════
    
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('api/wishlist/toggle/', views.WishlistToggleView.as_view(), name='wishlist_toggle'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # COMPARE
    # ═══════════════════════════════════════════════════════════════════════════
    
    path('compare/', views.CompareView.as_view(), name='compare'),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # VIRTUAL SERVICES
    # ═══════════════════════════════════════════════════════════════════════════
    
    path('virtual-services/', views.VirtualServicesListView.as_view(), name='virtual_services'),
    re_path(r'^virtual-service/(?P<slug>[\w\-]+)/$', views.VirtualServiceDetailView.as_view(), name='virtual_service_detail'),
]