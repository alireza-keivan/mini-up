# apps/core/views.py

from django.shortcuts import render
from django.db import models
from .models import ServiceDescription, SocialMediaLinks, YouTubeVideo
from apps.content.models import Article


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PAGES
# ═══════════════════════════════════════════════════════════════════════════════

def home(request):
    """صفحه اصلی"""
    from apps.products.models import Product
    
    # دریافت توضیحات خدمات فعال
    service_descriptions = ServiceDescription.objects.filter(is_active=True).order_by('service_type')
    
    # دریافت لینک‌های شبکه‌های اجتماعی
    social_links = SocialMediaLinks.objects.filter(is_active=True).first()
    
    # دریافت ویدیوی یوتیوب فعال
    youtube_video = YouTubeVideo.objects.filter(is_active=True).first()
    
    # دریافت مقالات سنجاق شده
    # مقالات بر اساس تاریخ انتشار (جدیدترین) مرتب می‌شوند
    latest_articles = Article.objects.filter(
        status='published',
        is_pinned=True
    ).order_by('-published_at')[:4]
    
    # دریافت 10 محصول پرفروش (جدیدترین)
    bestseller_products = Product.objects.filter(
        is_active=True,
        is_bestseller=True,
        stock__gt=0  # فقط محصولات موجود
    ).select_related('category', 'brand').order_by('-created_at')[:10]
    
    return render(request, 'core/home.html', {
        'title': 'صفحه اصلی',
        'service_descriptions': service_descriptions,
        'social_links': social_links,
        'youtube_video': youtube_video,
        'latest_articles': latest_articles,
        'bestseller_products': bestseller_products,
    })


def virtual_services(request):
    """
    صفحه خدمات مجازی - محتوای دینامیک
    Displays virtual service categories with their products
    All content is managed by admin through Category and Product models
    """
    from apps.products.models import Category, Product
    from django.db.models import Prefetch
    from django.core.paginator import Paginator
    
    # Get categories that have virtual service products only
    categories = Category.objects.filter(
        is_active=True,
        products__is_active=True,
        products__sub_type=Product.ProductSubType.VIRTUAL_SERVICE
    ).distinct().prefetch_related(
        Prefetch(
            'products',
            queryset=Product.objects.filter(
                is_active=True,
                sub_type=Product.ProductSubType.VIRTUAL_SERVICE
            ).select_related('category', 'brand').prefetch_related('images').order_by('-is_featured', '-created_at')[:12],
            to_attr='active_products'
        )
    ).order_by('sort_order', 'name')
    
    # Filter out categories with no products
    categories_with_products = []
    for cat in categories:
        if hasattr(cat, 'active_products') and cat.active_products:
            categories_with_products.append(cat)
    
    # Pagination - 6 categories per page
    paginator = Paginator(categories_with_products, 6)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get featured products for carousel (admin-controlled via is_featured flag)
    carousel_products = Product.objects.filter(
        is_active=True,
        sub_type=Product.ProductSubType.VIRTUAL_SERVICE,
        is_featured=True  # Only featured products appear in carousel
    ).select_related('category', 'brand').prefetch_related('images').order_by('-created_at')[:6]
    
    return render(request, 'core/virtual_services.html', {
        'title': 'خدمات مجازی',
        'categories': page_obj.object_list,
        'page_obj': page_obj,
        'carousel_products': carousel_products
    })


def gaming_products(request):
    """
    Gaming products page with filter sidebar
    """
    from apps.products.models import Product, Category, Brand
    from django.db.models import Min, Max, Q
    from django.core.paginator import Paginator
    
    # Base queryset for gaming products
    products = Product.objects.filter(
        is_active=True,
        sub_type=Product.ProductSubType.GAMING
    ).select_related('category', 'brand').prefetch_related('images')
    
    # Apply brand filter (using slug)
    brand_slugs = request.GET.getlist('brand')
    if brand_slugs:
        products = products.filter(brand__slug__in=brand_slugs)
    
    # Apply price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Apply stock filter (template uses 'in_stock')
    if request.GET.get('in_stock') == 'true':
        products = products.filter(stock__gt=0)
    
    # Apply discount filter (check if original_price exists and is greater than price)
    if request.GET.get('has_discount') == 'true':
        products = products.filter(original_price__isnull=False, original_price__gt=models.F('price'))
    
    # Apply sorting
    sort_param = request.GET.get('sort', 'newest')
    sort_mapping = {
        'newest': '-created_at',
        'price_asc': 'price',
        'price_desc': '-price',
        'popular': '-created_at',  # fallback to newest if view_count doesn't exist
        'rating': '-created_at'    # fallback to newest if avg_rating doesn't exist
    }
    products = products.order_by(sort_mapping.get(sort_param, '-created_at'))
    
    # Pagination
    paginator = Paginator(products, 20)  # 20 items per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for filter
    categories = Category.objects.filter(
        is_active=True,
        products__sub_type=Product.ProductSubType.GAMING
    ).distinct()
    
    # Get all brands for filter
    brands = Brand.objects.filter(
        is_active=True,
        products__sub_type=Product.ProductSubType.GAMING
    ).distinct()
    
    # Get price range
    price_data = Product.objects.filter(
        is_active=True,
        sub_type=Product.ProductSubType.GAMING
    ).aggregate(min_price=Min('price'), max_price=Max('price'))
    
    context = {
        'products': page_obj,  # Changed to paginated object
        'page_obj': page_obj,  # Template expects this
        'categories': categories,
        'brands': brands,
        'min_price': price_data['min_price'] or 0,
        'max_price': price_data['max_price'] or 0,
        'current_sort': sort_param,
        'title': 'محصولات گیمینگ',
        'page_title': 'محصولات گیمینگ'
    }
    
    return render(request, 'core/gaming-products.html', context)


def buy_products(request):
    """
    Buy products (peripherals/accessories) page with filters
    """
    from apps.products.models import Product, Category, Brand
    from django.db.models import Min, Max, Q
    from django.core.paginator import Paginator
    
    # Base queryset for peripheral products
    products = Product.objects.filter(
        is_active=True,
        product_type=Product.ProductType.PHYSICAL,
        sub_type=Product.ProductSubType.ACCESSORY
    ).select_related('category', 'brand').prefetch_related('images')
    
    # Apply brand filter (using slug)
    brand_slugs = request.GET.getlist('brand')
    if brand_slugs:
        products = products.filter(brand__slug__in=brand_slugs)
    
    # Apply price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Apply stock filter (template uses 'in_stock')
    if request.GET.get('in_stock') == 'true':
        products = products.filter(stock__gt=0)
    
    # Apply discount filter (check if original_price exists and is greater than price)
    if request.GET.get('has_discount') == 'true':
        products = products.filter(original_price__isnull=False, original_price__gt=models.F('price'))
    
    # Apply sorting
    sort_param = request.GET.get('sort', 'newest')
    sort_mapping = {
        'newest': '-created_at',
        'price_asc': 'price',
        'price_desc': '-price',
        'popular': '-created_at',  # fallback to newest if view_count doesn't exist
        'rating': '-created_at'    # fallback to newest if avg_rating doesn't exist
    }
    products = products.order_by(sort_mapping.get(sort_param, '-created_at'))
    
    # Pagination
    paginator = Paginator(products, 20)  # 20 items per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for filter
    categories = Category.objects.filter(
        is_active=True,
        products__product_type=Product.ProductType.PHYSICAL,
        products__sub_type=Product.ProductSubType.ACCESSORY
    ).distinct()
    
    # Get all brands for filter
    brands = Brand.objects.filter(
        is_active=True,
        products__product_type=Product.ProductType.PHYSICAL,
        products__sub_type=Product.ProductSubType.ACCESSORY
    ).distinct()
    
    # Get price range
    price_data = Product.objects.filter(
        is_active=True,
        product_type=Product.ProductType.PHYSICAL,
        sub_type=Product.ProductSubType.ACCESSORY
    ).aggregate(min_price=Min('price'), max_price=Max('price'))
    
    context = {
        'products': page_obj,  # Changed to paginated object
        'page_obj': page_obj,  # Template expects this
        'categories': categories,
        'brands': brands,
        'min_price': price_data['min_price'] or 0,
        'max_price': price_data['max_price'] or 0,
        'current_sort': sort_param,
        'title': 'خرید محصولات',
        'page_title': 'خرید محصولات'
    }
    
    return render(request, 'products/buy_products.html', context)


def mini_game(request):
    """
    صفحه مینی گیم
    Displays mini app products
    """
    from apps.products.models import Product, Category
    from django.db.models import Prefetch
    
    # Get categories that have mini app products
    categories = Category.objects.filter(
        is_active=True,
        products__is_active=True,
        products__sub_type=Product.ProductSubType.MINI_APP
    ).distinct().prefetch_related(
        Prefetch(
            'products',
            queryset=Product.objects.filter(
                is_active=True,
                sub_type=Product.ProductSubType.MINI_APP
            ).select_related('category', 'brand').prefetch_related('images').order_by('-is_featured', '-created_at'),
            to_attr='active_products'
        )
    ).order_by('sort_order', 'name')
    
    # Filter out categories with no products
    categories_with_products = [cat for cat in categories if cat.active_products]
    
    return render(request, 'core/mini_game.html', {
        'title': 'مینی گیم',
        'categories': categories_with_products
    })


def contact(request):
    """تماس با ما"""
    return render(request, 'core/contact.html', {'title': 'تماس با ما'})

def accounts(request):
    """تماس با ما"""
    return render(request, 'core/accounts.html', {'title': 'حساب کاربری'})


def about(request):
    """صفحه درباره ما"""
    return render(request, 'core/about.html', {'title': 'درباره ما'})


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION PAGES
# ═══════════════════════════════════════════════════════════════════════════════

def login_view(request):
    """صفحه ورود"""
    return render(request, 'core/login.html', {
        'title': 'ورود',
        'active_tab': 'login'
    })
    
def faq(request):
    """صفحه سوالات متداول"""
    return render(request, 'core/faq.html', {'title': 'سوالات متداول'})

def register_view(request):
    """صفحه ثبت نام - به همان صفحه login می‌رود با تب register فعال"""
    return render(request, 'core/login.html', {
        'title': 'ثبت نام',
        'active_tab': 'register'
    })


# ═══════════════════════════════════════════════════════════════════════════════
# LEGAL PAGES
# ═══════════════════════════════════════════════════════════════════════════════

def terms(request):
    """صفحه قوانین و مقررات"""
    return render(request, 'core/terms.html', {'title': 'قوانین و مقررات'})


def privacy(request):
    """صفحه حریم خصوصی"""
    return render(request, 'core/privacy.html', {'title': 'حریم خصوصی'})


# ═══════════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

def custom_404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    """Custom 500 error handler"""
    return render(request, 'errors/500.html', status=500)

def search_view(request):
    """
    صفحه جستجو - جستجو در محصولات با فیلترهای پیشرفته
    """
    from apps.products.models import Product, Category, Brand
    from django.db.models import Q
    from django.core.paginator import Paginator
    
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '')
    brand_slug = request.GET.get('brand', '')
    product_type = request.GET.get('type', '')  # virtual, physical, game_currency
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort', 'newest')  # newest, price_low, price_high, popular, bestseller
    page_number = request.GET.get('page', 1)
    
    # Start with active products
    products = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images')
    
    # Search query - search in name, description, short_description
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(name_en__icontains=query) |
            Q(short_description__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__name__icontains=query)
        )
    
    # Filter by category
    selected_category = None
    if category_slug:
        try:
            selected_category = Category.objects.get(slug=category_slug, is_active=True)
            products = products.filter(category=selected_category)
        except Category.DoesNotExist:
            pass
    
    # Filter by brand
    selected_brand = None
    if brand_slug:
        try:
            selected_brand = Brand.objects.get(slug=brand_slug, is_active=True)
            products = products.filter(brand=selected_brand)
        except Brand.DoesNotExist:
            pass
    
    # Filter by product type
    if product_type and product_type in ['virtual', 'physical', 'game_currency']:
        products = products.filter(product_type=product_type)
    
    # Filter by price range
    if min_price and min_price.isdigit():
        products = products.filter(price__gte=int(min_price))
    if max_price and max_price.isdigit():
        products = products.filter(price__lte=int(max_price))
    
    # Sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'popular':
        products = products.order_by('-view_count')
    elif sort_by == 'bestseller':
        products = products.order_by('-sales_count')
    elif sort_by == 'name_asc':
        products = products.order_by('name')
    elif sort_by == 'name_desc':
        products = products.order_by('-name')
    else:  # newest (default)
        products = products.order_by('-created_at')
    
    # Get total count before pagination
    total_count = products.count()
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_obj = paginator.get_page(page_number)
    
    # Get filter options for sidebar
    all_categories = Category.objects.filter(is_active=True).order_by('sort_order', 'name')
    all_brands = Brand.objects.filter(is_active=True, products__is_active=True).distinct().order_by('name')
    
    # Price range suggestions (based on all active products)
    price_ranges = [
        {'label': 'زیر ۱۰۰,۰۰۰ تومان', 'min': 0, 'max': 100000},
        {'label': '۱۰۰,۰۰۰ - ۵۰۰,۰۰۰ تومان', 'min': 100000, 'max': 500000},
        {'label': '۵۰۰,۰۰۰ - ۱,۰۰۰,۰۰۰ تومان', 'min': 500000, 'max': 1000000},
        {'label': '۱,۰۰۰,۰۰۰ - ۵,۰۰۰,۰۰۰ تومان', 'min': 1000000, 'max': 5000000},
        {'label': 'بالای ۵,۰۰۰,۰۰۰ تومان', 'min': 5000000, 'max': 999999999},
    ]
    
    context = {
        'page_title': f'جستجو: {query}' if query else 'جستجو در محصولات',
        'query': query,
        'products': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'all_categories': all_categories,
        'all_brands': all_brands,
        'selected_category': selected_category,
        'selected_brand': selected_brand,
        'product_type': product_type,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'price_ranges': price_ranges,
    }
    return render(request, 'core/search.html', context)


from django.http import JsonResponse

def search_api_view(request):
    """
    API جستجو برای autocomplete و AJAX
    GET /search/api/?q=...
    Returns JSON with product suggestions for autocomplete
    """
    from apps.products.models import Product, Category
    from django.db.models import Q
    
    query = request.GET.get('q', '').strip()
    limit = int(request.GET.get('limit', 10))
    
    if len(query) < 2:
        return JsonResponse({'success': True, 'query': query, 'results': [], 'count': 0})
    
    results = []
    
    # Search in products - name, short description, category
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(name_en__icontains=query) |
        Q(short_description__icontains=query) |
        Q(category__name__icontains=query) |
        Q(brand__name__icontains=query),
        is_active=True
    ).select_related('category', 'brand').prefetch_related('images')[:limit]
    
    for product in products:
        # Get first additional image if available
        first_image = product.images.filter(is_active=True).first()
        
        # Build result object
        result = {
            'type': 'product',
            'id': product.id,
            'title': product.name,
            'slug': product.slug,
            'url': f'/products/{product.slug}/',  # Adjust based on your URL pattern
            'price': product.price,
            'original_price': product.original_price,
            'discount_percentage': product.discount_percentage,
            'category': product.category.name if product.category else None,
            'brand': product.brand.name if product.brand else None,
            'product_type': product.get_product_type_display(),
            'is_in_stock': product.is_in_stock,
            'image': None,
        }
        
        # Add image URL if available
        if product.main_image:
            result['image'] = product.main_image.url
        elif first_image:
            result['image'] = first_image.image.url
        
        results.append(result)
    
    # Also search in categories (optional - can help with navigation)
    if len(results) < limit:
        remaining = limit - len(results)
        categories = Category.objects.filter(
            Q(name__icontains=query) |
            Q(name_en__icontains=query),
            is_active=True
        )[:remaining]
        
        for category in categories:
            result = {
                'type': 'category',
                'id': category.id,
                'title': category.name,
                'slug': category.slug,
                'url': f'/category/{category.slug}/',
                'product_count': category.get_active_products_count(),
                'image': category.image.url if category.image else None,
            }
            results.append(result)
    
    return JsonResponse({
        'success': True,
        'query': query,
        'results': results,
        'count': len(results),
    })

def category_view(request, slug):
    """
    صفحه دسته‌بندی محصولات - نمایش محصولات یک دسته‌بندی خاص
    """
    from apps.products.models import Product, Category, Brand
    from django.shortcuts import get_object_or_404
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    # Get category or 404
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    # Get filter parameters
    brand_slug = request.GET.get('brand', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort', 'newest')
    page_number = request.GET.get('page', 1)
    search_query = request.GET.get('q', '').strip()
    
    # Get products from this category and all subcategories
    category_ids = [category.id]
    category_ids.extend([child.id for child in category.get_all_children()])
    
    products = Product.objects.filter(
        category_id__in=category_ids,
        is_active=True
    ).select_related('category', 'brand').prefetch_related('images')
    
    # Search within category
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(name_en__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by brand
    selected_brand = None
    if brand_slug:
        try:
            selected_brand = Brand.objects.get(slug=brand_slug, is_active=True)
            products = products.filter(brand=selected_brand)
        except Brand.DoesNotExist:
            pass
    
    # Filter by price range
    if min_price and min_price.isdigit():
        products = products.filter(price__gte=int(min_price))
    if max_price and max_price.isdigit():
        products = products.filter(price__lte=int(max_price))
    
    # Sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'popular':
        products = products.order_by('-view_count')
    elif sort_by == 'bestseller':
        products = products.order_by('-sales_count')
    elif sort_by == 'name_asc':
        products = products.order_by('name')
    elif sort_by == 'name_desc':
        products = products.order_by('-name')
    elif sort_by == 'featured':
        products = products.order_by('-is_featured', '-created_at')
    else:  # newest (default)
        products = products.order_by('-created_at')
    
    # Get total count
    total_count = products.count()
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_obj = paginator.get_page(page_number)
    
    # Get subcategories for navigation
    subcategories = category.children.filter(is_active=True).order_by('sort_order', 'name')
    
    # Get brands available in this category
    available_brands = Brand.objects.filter(
        is_active=True,
        products__category_id__in=category_ids,
        products__is_active=True
    ).distinct().order_by('name')
    
    # Price range calculations
    from django.db.models import Min, Max
    price_stats = Product.objects.filter(
        category_id__in=category_ids,
        is_active=True
    ).aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    # Featured products in this category
    featured_products = Product.objects.filter(
        category_id__in=category_ids,
        is_active=True,
        is_featured=True
    ).select_related('category', 'brand')[:4]
    
    context = {
        'page_title': f'{category.name}',
        'category': category,
        'products': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'subcategories': subcategories,
        'available_brands': available_brands,
        'selected_brand': selected_brand,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'search_query': search_query,
        'price_stats': price_stats,
        'featured_products': featured_products,
    }
    return render(request, 'core/category.html', context)


def neon_products_demo(request):
    """
    Demo page for neon-themed product cards
    Showcases the new card design with proper 2:1 proportions
    """
    from apps.products.models import Product
    
    # Get sample products (first 8 active products)
    products = Product.objects.filter(
        is_active=True
    ).select_related('category', 'brand')[:8]
    
    return render(request, 'core/neon_products_demo.html', {
        'title': 'نمایش کارت‌های نئون',
        'products': products,
    })