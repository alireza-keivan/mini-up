"""
URL Configuration for Accounts App
OTP-Only Authentication
"""

from django.urls import path
from . import views, api_views

app_name = 'accounts'

urlpatterns = [
    # Authentication Flow
    path('login/', views.LoginView.as_view(), name='login'),
    path('verify/', views.VerifyView.as_view(), name='verify'),
    path('resend-otp/', views.ResendOTPView.as_view(), name='resend_otp'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'), 
    path('orders/', views.OrdersView.as_view(), name='orders'),  
    path('transactions/', views.transactions_view, name='transactions'),
    path('tickets/', views.tickets_view, name='tickets'),
    path('settings/', views.settings_view, name='settings'),
    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('favorites/', views.favorites_view, name='favorites'),
    # API
    path('api/check-auth/', views.check_auth_status, name='check_auth'),
    path('notifications/', views.notifications_view, name='notifications'),
]