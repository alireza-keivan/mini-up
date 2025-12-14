# apps/consulting/views.py

"""
ویوهای Template-based برای مشاوره
(برای صفحات HTML - نه API)
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import ConsultingCategory, Consultant, Appointment, TimeSlot
from .services import ConsultingService


def consultant_list(request):
    """
    صفحه لیست مشاوران
    GET /consulting/
    """
    category_slug = request.GET.get('category')
    
    categories = ConsultingCategory.objects.filter(is_active=True)
    consultants = ConsultingService.get_active_consultants(category_slug=category_slug)
    
    # دسته‌بندی فعلی
    current_category = None
    if category_slug:
        current_category = categories.filter(slug=category_slug).first()
    
    context = {
        'categories': categories,
        'consultants': consultants,
        'current_category': current_category,
    }
    
    return render(request, 'consulting/consultant_list.html', context)


def consultant_detail(request, consultant_id):
    """
    صفحه پروفایل مشاور
    GET /consulting/<uuid:consultant_id>/
    """
    consultant = get_object_or_404(
        Consultant,
        id=consultant_id,
        is_active=True,
        is_verified=True
    )
    
    # اسلات‌های آزاد
    available_slots = ConsultingService.get_available_slots(consultant_id)
    
    # نظرات
    reviews = ConsultingService.get_consultant_reviews(consultant_id, limit=10)
    
    context = {
        'consultant': consultant,
        'slots': available_slots,
        'reviews': reviews,
    }
    
    return render(request, 'consulting/consultant_detail.html', context)


@login_required
def book_appointment(request, slot_id):
    """
    رزرو نوبت
    POST /consulting/book/<uuid:slot_id>/
    """
    if request.method != 'POST':
        return redirect('consulting:list')
    
    description = request.POST.get('description', '')
    
    result = ConsultingService.book_appointment(
        user=request.user,
        slot_id=slot_id,
        description=description
    )
    
    if result['success']:
        appointment = result['appointment']
        messages.success(request, 'نوبت شما با موفقیت رزرو شد.')
        return redirect('consulting:appointment_detail', appointment_id=appointment.id)
    else:
        messages.error(request, result['error'])
        return redirect('consulting:list')


@login_required
def appointment_detail(request, appointment_id):
    """
    جزئیات نوبت
    GET /consulting/appointments/<uuid:appointment_id>/
    """
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        user=request.user
    )
    
    context = {
        'appointment': appointment,
    }
    
    return render(request, 'consulting/appointment_detail.html', context)


@login_required
def my_appointments(request):
    """
    لیست نوبت‌های من
    GET /consulting/my-appointments/
    """
    appointments = Appointment.objects.filter(
        user=request.user
    ).select_related('consultant', 'slot').order_by('-created_at')
    
    context = {
        'appointments': appointments,
    }
    
    return render(request, 'consulting/my_appointments.html', context)


@login_required
@require_POST
def cancel_appointment(request, appointment_id):
    """
    لغو نوبت
    POST /consulting/appointments/<uuid:appointment_id>/cancel/
    """
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        user=request.user
    )
    
    result = ConsultingService.cancel_appointment(appointment, cancelled_by='user')
    
    if result['success']:
        messages.success(request, 'نوبت شما لغو شد.')
    else:
        messages.error(request, result['error'])
    
    return redirect('consulting:my_appointments')


@login_required
@require_POST
def submit_review(request, appointment_id):
    """
    ثبت نظر
    POST /consulting/appointments/<uuid:appointment_id>/review/
    """
    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '')
    
    if not rating:
        messages.error(request, 'لطفاً امتیاز را انتخاب کنید.')
        return redirect('consulting:appointment_detail', appointment_id=appointment_id)
    
    result = ConsultingService.add_review(
        user=request.user,
        appointment_id=appointment_id,
        rating=int(rating),
        comment=comment
    )
    
    if result['success']:
        messages.success(request, 'نظر شما ثبت شد. با تشکر!')
    else:
        messages.error(request, result['error'])
    
    return redirect('consulting:appointment_detail', appointment_id=appointment_id)


# ═══════════════════════════════════════════════════════════════════════════════
# AJAX ENDPOINTS (برای درخواست‌های JavaScript)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def get_slots_ajax(request, consultant_id):
    """
    دریافت اسلات‌ها با AJAX
    GET /consulting/ajax/slots/<uuid:consultant_id>/?date=2024-01-15
    """
    date = request.GET.get('date')
    
    slots = ConsultingService.get_available_slots(consultant_id, date)
    
    data = []
    for slot in slots:
        data.append({
            'id': str(slot.id),
            'date': str(slot.date),
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'duration': slot.duration,
            'price': slot.price,
        })
    
    return JsonResponse({'success': True, 'slots': data})
