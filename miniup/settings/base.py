"""
Base settings for miniup project.
Common settings shared between development and production.
"""

import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY', default='django-insecure-change-me-in-production')

# ═══════════════════════════════════════════════════════════════════════════════
# APPLICATION DEFINITION
# ═══════════════════════════════════════════════════════════════════════════════

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',  # ✅ Required for allauth
]

THIRD_PARTY_APPS = [
    'compressor',
    'rest_framework',
    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.products',
    'apps.orders',
    'apps.payments',
    'apps.wallet',
    'apps.coupons',
    'apps.consulting',  # Re-enabled for support ticket system
    'apps.content',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
INSTALLED_APPS += ['channels']
ASGI_APPLICATION = 'miniup.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {"hosts": [('127.0.0.1', 6379)]},
    },
}
# ═══════════════════════════════════════════════════════════════════════════════
# MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════════

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # ✅ Required for allauth
]

# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════════════════

AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Site ID for django.contrib.sites
SITE_ID = 2

# ═══════════════════════════════════════════════════════════════════════════════
# ALLAUTH SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

# Login methods - فقط با ایمیل
ACCOUNT_LOGIN_METHODS = {'email'}

# Email settings
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'none'  # 'mandatory', 'optional', 'none'

# Signup fields (replaces ACCOUNT_EMAIL_REQUIRED and ACCOUNT_USERNAME_REQUIRED)
ACCOUNT_SIGNUP_FIELDS = [
    'email*',
    'password1*',
    'password2*',
]

# ═══════════════════════════════════════════════════════════════════════════════
# SOCIAL ACCOUNT SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

# ⭐ مهم: برای Social Login نیازی به username نیست
SOCIALACCOUNT_QUERY_EMAIL = True

# Google Provider settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
            'openid',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
        'FETCH_USERINFO': True,
    }
}
# Custom adapters (create these files later)
ACCOUNT_ADAPTER = 'apps.accounts.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'apps.accounts.adapters.CustomSocialAccountAdapter'

# ═══════════════════════════════════════════════════════════════════════════════
# URL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

ROOT_URLCONF = 'miniup.urls'
WSGI_APPLICATION = 'miniup.wsgi.application'

# Login/Logout redirects
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # Required by allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.site_settings',
                'apps.core.context_processors.site_context',
                'apps.wallet.context_processors.wallet_context',
            ],
        },
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# PASSWORD VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# INTERNATIONALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('fa', 'Persian'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# ═══════════════════════════════════════════════════════════════════════════════
# STATIC & MEDIA FILES
# ═══════════════════════════════════════════════════════════════════════════════

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

# Django Compressor
COMPRESS_ENABLED = True
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.rCSSMinFilter',
]

# ═══════════════════════════════════════════════════════════════════════════════
# DEFAULT SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ═══════════════════════════════════════════════════════════════════════════════
# SITE SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

SITE_NAME = 'مینی‌آپ'
SITE_DESCRIPTION = 'فروشگاه آنلاین بازی و خدمات مجازی'

# ═══════════════════════════════════════════════════════════════════════════════
# OTP SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

OTP_EXPIRE_SECONDS = 120  # 2 minutes
OTP_LENGTH = 5

# ═══════════════════════════════════════════════════════════════════════════════
# WALLET SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

MIN_WALLET_TOPUP = 10000  # Minimum 10,000 Toman
MAX_WALLET_TOPUP = 10000000  # Maximum 10,000,000 Toman

# ═══════════════════════════════════════════════════════════════════════════════
# SHIPPING
# ═══════════════════════════════════════════════════════════════════════════════

FLAT_SHIPPING_RATE = 50000  # 50,000 Toman
FREE_SHIPPING_THRESHOLD = 500000  # Free above 500,000 Toman

# ═══════════════════════════════════════════════════════════════════════════════
# REST FRAMEWORK
# ═══════════════════════════════════════════════════════════════════════════════

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@mini-up.ir'
SERVER_EMAIL = 'server@mini-up.ir'


# ═══════════════════════════════════════════════════════════════════════════════
# CSRF SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

CSRF_COOKIE_HTTPONLY = False  # مهم! باید False باشد تا JavaScript بتواند token را بخواند
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# برای development - در production این را حذف یا True کنید
CSRF_COOKIE_SECURE = False

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # در production: True
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ═══════════════════════════════════════════════════════════════════════════════
# GOOGLE OAUTH SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

# Get from environment or .env file
GOOGLE_OAUTH_CLIENT_ID = env('GOOGLE_OAUTH_CLIENT_ID', default=None)
GOOGLE_OAUTH_CLIENT_SECRET = env('GOOGLE_OAUTH_CLIENT_SECRET', default=None)