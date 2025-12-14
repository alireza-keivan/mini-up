# apps/consulting/urls.py

from django.urls import path
from . import views

app_name = 'consulting'

urlpatterns = [
    # Ticket list
    path('tickets/', views.ticket_list, name='ticket_list'),
    
    # Ticket create
    path('tickets/create/', views.ticket_create, name='ticket_create'),
    
    # Ticket detail
    path('tickets/<str:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    
    # Ticket actions
    path('tickets/<str:ticket_id>/close/', views.ticket_close, name='ticket_close'),
    path('tickets/<str:ticket_id>/reopen/', views.ticket_reopen, name='ticket_reopen'),
    
    # Message
    path('tickets/<str:ticket_id>/message/', views.ticket_message_create, name='ticket_message_create'),
    
    # AJAX endpoints
    path('tickets/<str:ticket_id>/check-messages/', views.ticket_check_new_messages, name='ticket_check_new_messages'),
]
