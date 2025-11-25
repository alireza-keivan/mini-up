"""
Custom context processors for the core app.
These variables will be available in all templates.
"""

def site_context(request):
    """
    Adds site-wide context variables to all templates.
    """
    return {
        'site_name': 'Mini-up',
        'site_name_fa': 'مینی‌آپ',
        'site_description': 'خدمات مجازی، محصولات گیمینگ و مشاوره',
        'current_year': 2025,
        'navigation_items': [
            {'name': 'خانه', 'url': 'core:home', 'icon': 'fa-home'},
            {'name': 'خدمات مجازی', 'url': 'core:virtual_services', 'icon': 'fa-cloud'},
            {'name': 'محصولات گیمینگ', 'url': 'core:gaming_products', 'icon': 'fa-gamepad'},
            {'name': 'خرید محصولات', 'url': 'core:buy_products', 'icon': 'fa-shopping-cart'},
            {'name': 'مینی گیم', 'url': 'core:mini_game', 'icon': 'fa-puzzle-piece'},
            {'name': 'مشاوره', 'url': 'core:consulting', 'icon': 'fa-comments'},
            {'name': 'درباره ما', 'url': 'core:about', 'icon': 'fa-info-circle'},
        ],
        'social_links': {
            'telegram': '#',
            'instagram': '#',
            'whatsapp': '#',
        },
        'contact_info': {
            'email': 'info@mini-up.ir',
            'phone': '+98 21 1234 5678',
        },
    }


def site_settings(request):
    """
    Global settings/context available to all templates.
    """
    return {
        'SITE_NAME': 'Mini-up.ir',
        'SITE_DESCRIPTION': 'پلتفرم خدمات و محصولات گیمینگ با استایل تاریک نئونی',
        'LANG_DIRECTION': 'rtl',
        'LANGUAGE_CODE': 'fa',
        'THEME_ACCENT': '#ff0055',
        'THEME_BG': '#0a0a0f',
    }
