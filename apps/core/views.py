# apps/core/views.py

from django.shortcuts import render
from .models import ServiceDescription


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PAGES
# ═══════════════════════════════════════════════════════════════════════════════

def home(request):
    """صفحه اصلی"""
    # دریافت توضیحات خدمات فعال
    service_descriptions = ServiceDescription.objects.filter(is_active=True).order_by('service_type')
    
    return render(request, 'core/home.html', {
        'title': 'صفحه اصلی',
        'service_descriptions': service_descriptions
    })


def virtual_services(request):
    """صفحه خدمات مجازی"""
    return render(request, 'core/virtual_services.html', {'title': 'خدمات مجازی'})


def gaming_products(request):
    """
    صفحه محصولات گیمینگ
    Displays gaming product categories with their products in horizontal scrollable carousels.
    """
    from apps.products.models import Category, Brand
    
    # Get active gaming categories with their active products
    # Filter by category_type = 'gaming'
    categories = Category.objects.filter(
        is_active=True,
        category_type='gaming',
        products__is_active=True
    ).prefetch_related(
        'products__brand',
        'products__images',
        'products__variants'
    ).select_related(
        'parent'
    ).distinct().order_by('sort_order', 'name')
    
    # Get total counts for stats
    total_products = sum(cat.get_active_products_count() for cat in categories)
    total_brands = Brand.objects.filter(
        products__category__category_type='gaming',
        products__is_active=True
    ).distinct().count()
    
    context = {
        'title': 'محصولات گیمینگ',
        'categories': categories,
        'total_products': total_products,
        'total_categories': categories.count(),
        'total_brands': total_brands,
    }
    
    return render(request, 'core/gaming_products.html', context)


def buy_products(request):
    """
    صفحه خرید محصولات
    Displays product categories with their products in horizontal scrollable carousels.
    """
    from apps.products.models import Category
    
    # Get active categories with their active products
    # Using select_related and prefetch_related for optimal performance
    categories = Category.objects.filter(
        is_active=True,
        products__is_active=True  # Only categories that have active products
    ).prefetch_related(
        'products__brand',  # Prefetch brand for each product
        'products__images',  # Prefetch product images
    ).select_related(
        'parent'  # If you want to show parent category info
    ).distinct().order_by('sort_order', 'name')
    
    # Filter products per category to only show active ones
    # This is already handled by the template with category.products.all
    # but we're ensuring the queryset is optimized
    
    context = {
        'title': 'خرید محصولات',
        'categories': categories,
    }
    
    return render(request, 'core/buy_products.html', context)


def mini_game(request):
    """صفحه مینی گیم"""
    return render(request, 'core/mini_game.html', {'title': 'مینی گیم'})


def contact(request):
    """تماس با ما"""
    return render(request, 'core/contact.html', {'title': 'تماس با ما'})

def accounts(request):
    """تماس با ما"""
    return render(request, 'core/accounts.html', {'title': 'حساب کاربری'})

def consulting(request):
    """صفحه مشاوره"""
    return render(request, 'core/consulting.html', {'title': 'مشاوره'})


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
    صفحه جستجو
    """
    query = request.GET.get('q', '')
    results = []
    
    # TODO: پیاده‌سازی جستجو در محصولات و خدمات
    
    context = {
        'page_title': f'جستجو: {query}' if query else 'جستجو',
        'query': query,
        'results': results,
    }
    return render(request, 'core/search.html', context)


from django.http import JsonResponse

def search_api_view(request):
    """
    API جستجو برای autocomplete و AJAX
    GET /search/api/?q=...
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'success': True, 'results': []})
    
    results = []
    
    # TODO: جستجو در محصولات
    # از apps.products.models import Product
    # products = Product.objects.filter(name__icontains=query)[:5]
    # for p in products:
    #     results.append({
    #         'type': 'product',
    #         'title': p.name,
    #         'url': p.get_absolute_url(),
    #         'image': p.image.url if p.image else None,
    #     })
    
    return JsonResponse({
        'success': True,
        'query': query,
        'results': results,
    })

def category_view(request, slug):
    """
    صفحه دسته‌بندی محصولات
    """
    # TODO: پیاده‌سازی کامل با مدل Category
    context = {
        'page_title': f'دسته‌بندی: {slug}',
        'category_slug': slug,
        'products': [],
    }
    return render(request, 'core/category.html', context)