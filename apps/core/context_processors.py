"""
Custom context processors for the core app.
These variables will be available in all templates.
"""
from .models import SocialMediaLinks


def site_context(request):
    """
    Adds site-wide context variables to all templates.
    """
    # Fetch social media links from database
    try:
        social_media = SocialMediaLinks.objects.filter(is_active=True).first()
        social_links = {
            'telegram': social_media.telegram if social_media and social_media.telegram else '',
            'instagram': social_media.instagram if social_media and social_media.instagram else '',
            'twitter': social_media.twitter if social_media and social_media.twitter else '',
            'youtube': social_media.youtube if social_media and social_media.youtube else '',
            'whatsapp': social_media.whatsapp if social_media and social_media.whatsapp else '',
        }
    except Exception:
        # Fallback in case of database errors
        social_links = {
            'telegram': '',
            'instagram': '',
            'twitter': '',
            'youtube': '',
            'whatsapp': '',
        }
    
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
            {'name': 'درباره ما', 'url': 'core:about', 'icon': 'fa-info-circle'},
        ],
        'social_links': social_links,
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
