# apps/core/views.py

from django.shortcuts import render


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PAGES
# ═══════════════════════════════════════════════════════════════════════════════

def home(request):
    """صفحه اصلی"""
    return render(request, 'core/home.html', {'title': 'صفحه اصلی'})


def virtual_services(request):
    """صفحه خدمات مجازی"""
    return render(request, 'core/virtual_services.html', {'title': 'خدمات مجازی'})


def gaming_products(request):
    """صفحه محصولات گیمینگ"""
    return render(request, 'core/gaming_products.html', {'title': 'محصولات گیمینگ'})


def buy_products(request):
    """صفحه خرید محصولات"""
    return render(request, 'core/buy_products.html', {'title': 'خرید محصولات'})


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
