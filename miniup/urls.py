"""
URL configuration for miniup project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Accounts - باید قبل از core باشد
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('accounts/api/v1/', include('apps.accounts.urls_api', namespace='accounts_api')),
    path('accounts/', include('allauth.urls')),
    
    # Products
    path('products/', include('apps.products.urls', namespace='products')),
    path('products/api/v1/', include('apps.products.urls_api', namespace='products_api')),
    
    # Orders
    path('orders/', include('apps.orders.urls', namespace='orders')),
    path('orders/api/v1/', include('apps.orders.urls_api', namespace='orders_api')),
    
    # Wallet
    path('wallet/', include('apps.wallet.urls', namespace='wallet')),
    path('wallet/api/v1/', include('apps.wallet.urls_api', namespace='wallet_api')),
    
    # Payments
    path('payments/', include('apps.payments.urls', namespace='payments')),
    path('payments/api/v1/', include('apps.payments.urls_api', namespace='payments_api')),
    
    # Coupons
    path('coupons/api/v1/', include('apps.coupons.urls_api', namespace='coupons_api')),
    
    # Consulting
    path('consulting/', include('apps.consulting.urls', namespace='consulting')),
    path('consulting/api/v1/', include('apps.consulting.urls_api', namespace='consulting_api')),
    
    # Content
    path('blog/', include('apps.content.urls', namespace='content')),
    path('content/api/v1/', include('apps.content.urls_api', namespace='content_api')),
    
    # Core - باید آخر باشد چون '' همه چیز را catch می‌کند
    path('', include('apps.core.urls', namespace='core')),
]

# Serve static and media files in development
if settings.DEBUG:
    # In development, Django serves static files automatically from STATICFILES_DIRS
    # No need to add static() here for STATIC_URL, it's handled by staticfiles app
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'apps.core.views.custom_404'
handler500 = 'apps.core.views.custom_500'
