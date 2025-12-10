# apps/core/urls.py

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # صفحات اصلی
    path('', views.home, name='home'),
    path('virtual-services/', views.virtual_services, name='virtual_services'),
    path('gaming-products/', views.gaming_products, name='gaming_products'),
    path('buy-products/', views.buy_products, name='buy_products'),
    path('mini-game/', views.mini_game, name='mini_game'),
    path('consulting/', views.consulting, name='consulting'),
    path('about/', views.about, name='about'),
    path('faq/', views.faq, name='faq'), 
    # REMOVED: path('accounts/', views.accounts, name='accounts'),  # This conflicts with apps/accounts/
    
    # ===== صفحات احراز هویت =====
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    
    # ===== صفحات قانونی =====
    path('terms/', views.terms, name='terms'),
    path('term-conditions/', views.terms, name='term_conditions'),  # alias
    path('privacy/', views.privacy, name='privacy'),
    path('contact/', views.contact, name='contact'),
    path('search/', views.search_view, name='search'),
    path('search/api/', views.search_api_view, name='search_api'),
    path('category/<slug:slug>/', views.category_view, name='category'),

]
