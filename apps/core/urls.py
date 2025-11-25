from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('virtual-services/', views.virtual_services, name='virtual_services'),
    path('gaming-products/', views.gaming_products, name='gaming_products'),
    path('buy-products/', views.buy_products, name='buy_products'),
    path('mini-game/', views.mini_game, name='mini_game'),
    path('consulting/', views.consulting, name='consulting'),
    path('about/', views.about, name='about'),
]
