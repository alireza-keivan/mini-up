"""
URL Configuration for Accounts App
OTP-Only Authentication
"""

from django.urls import path
from . import views, api_views

app_name = 'accounts'

urlpatterns = [
    # Base route - redirect to dashboard or profile
    path('', views.AccountsIndexView.as_view(), name='index'),
    
    # Authentication Flow
    path('login/', views.LoginView.as_view(), name='login'),
    path('verify/', views.VerifyView.as_view(), name='verify'),
    path('resend-otp/', views.ResendOTPView.as_view(), name='resend_otp'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Google OAuth
    path('login/google/', views.GoogleLoginView.as_view(), name='google_login'),
    path('login/google/callback/', views.GoogleCallbackView.as_view(), name='google_callback'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'), 
    path('orders/', views.OrdersView.as_view(), name='orders'),  
    path('transactions/', views.transactions_view, name='transactions'),
    path('tickets/', views.tickets_view, name='tickets'),
    path('tickets/create/', views.ticket_create_view, name='ticket_create'),
    path('tickets/<str:ticket_id>/', views.ticket_detail_view, name='ticket_detail'),
    path('tickets/<str:ticket_id>/message/', views.ticket_message_create_view, name='ticket_message_create'),
    path('tickets/<str:ticket_id>/close/', views.ticket_close_view, name='ticket_close'),
    path('tickets/<str:ticket_id>/reopen/', views.ticket_reopen_view, name='ticket_reopen'),
    path('settings/', views.settings_view, name='settings'),
    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('favorites/', views.favorites_view, name='favorites'),
    # API
    path('api/check-auth/', views.check_auth_status, name='check_auth'),
    
    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('api/notifications/', api_views.get_notifications_api, name='api_notifications'),
    path('api/notifications/unread-count/', api_views.get_unread_count_api, name='api_notifications_unread_count'),
    path('api/notifications/mark-read/', api_views.mark_notification_read_api, name='api_notifications_mark_read'),
    path('api/notifications/mark-all-read/', api_views.mark_all_notifications_read_api, name='api_notifications_mark_all_read'),
    path('api/notifications/delete/', api_views.delete_notification_api, name='api_notifications_delete'),
    path('bank-card/add/', views.AddBankCardView.as_view(), name='add_bank_card'),
    path('bank-card/delete/<int:card_id>/', views.DeleteBankCardView.as_view(), name='delete_bank_card'),
    path('bank-card/set-default/<int:card_id>/', views.SetDefaultBankCardView.as_view(), name='set_default_bank_card'),
    path('bank-card/list/', views.GetBankCardsView.as_view(), name='list_bank_cards'),
    path('address/add/', views.AddAddressView.as_view(), name='add_address'),
    path('address/delete/<int:address_id>/', views.DeleteAddressView.as_view(), name='delete_address'),
    path('address/set-default/<int:address_id>/', views.SetDefaultAddressView.as_view(), name='set_default_address'),
    path('address/edit/<int:address_id>/', views.EditAddressView.as_view(), name='edit_address'),
    path('address/list/', views.GetAddressesView.as_view(), name='list_addresses'),
]