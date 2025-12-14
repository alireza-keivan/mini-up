from django.urls import path
from . import views
app_name = 'consulting'
urlpatterns = [
    # Consultant listing
    path('', views.consultant_list, name='list'),
    
    # Consultant detail
    path('consultant/<int:consultant_id>/', views.consultant_detail, name='detail'),
    
    # Appointment management
    path('appointment/book/<int:slot_id>/', views.book_appointment, name='book_appointment'),
    path('appointment/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('appointment/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    
    # Review
    path('appointment/review/<int:appointment_id>/', views.submit_review, name='submit_review'),
    
    # AJAX endpoints
    path('ajax/slots/<int:consultant_id>/', views.get_slots_ajax, name='get_slots_ajax'),
]