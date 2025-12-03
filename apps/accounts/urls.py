"""
URL Configuration for Accounts App
OTP-Only Authentication
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication Flow
    path('login/', views.LoginView.as_view(), name='login'),
    path('verify/', views.VerifyView.as_view(), name='verify'),
    path('resend-otp/', views.ResendOTPView.as_view(), name='resend_otp'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'), 
    path('orders/', views.orders, name='orders'),  
    
    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # API
    path('api/check-auth/', views.check_auth_status, name='check_auth'),
]