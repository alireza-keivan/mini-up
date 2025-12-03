# apps/consulting/services.py

"""
سرویس مشاوره - ساده و کاربردی
"""

import logging
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Consultant, TimeSlot, Appointment, ConsultantReview

logger = logging.getLogger(__name__)


class ConsultingService:
    """سرویس اصلی مشاوره"""
    
    # ─────────────────────────────────────────────────────────────
    # GET CONSULTANTS
    # ─────────────────────────────────────────────────────────────
    
    @staticmethod
    def get_active_consultants(category_slug=None):
        """
        لیست مشاوران فعال
        """
        qs = Consultant.objects.filter(
            is_active=True,
            is_verified=True
        ).select_related('user').prefetch_related('categories')
        
        if category_slug:
            qs = qs.filter(categories__slug=category_slug)
        
        return qs.order_by('-is_online', '-rating')
    
    @staticmethod
    def get_consultant(consultant_id):
        """
        دریافت یک مشاور
        """
        try:
            return Consultant.objects.select_related('user').get(
                id=consultant_id,
                is_active=True,
                is_verified=True
            )
        except Consultant.DoesNotExist:
            return None
    
    # ─────────────────────────────────────────────────────────────
    # TIME SLOTS
    # ─────────────────────────────────────────────────────────────
    
    @staticmethod
    def get_available_slots(consultant_id, date=None):
        """
        بازه‌های زمانی آزاد یک مشاور
        """
        qs = TimeSlot.objects.filter(
            consultant_id=consultant_id,
            status=TimeSlot.SlotStatus.AVAILABLE,
            date__gte=timezone.now().date()
        )
        
        if date:
            qs = qs.filter(date=date)
        
        return qs.order_by('date', 'start_time')
    
    @staticmethod
    def create_time_slots(consultant, date, slots_data):
        """
        ایجاد بازه‌های زمانی توسط مشاور
        
        slots_data = [
            {'start_time': '09:00', 'end_time': '09:30', 'duration': 30},
            {'start_time': '10:00', 'end_time': '10:30', 'duration': 30},
        ]
        """
        created = []
        
        for slot in slots_data:
            ts, is_new = TimeSlot.objects.get_or_create(
                consultant=consultant,
                date=date,
                start_time=slot['start_time'],
                defaults={
                    'end_time': slot['end_time'],
                    'duration': slot.get('duration', 30)
                }
            )
            if is_new:
                created.append(ts)
        
        return created
    
    # ─────────────────────────────────────────────────────────────
    # BOOKING
    # ─────────────────────────────────────────────────────────────
    
    @classmethod
    @transaction.atomic
    def book_appointment(cls, user, slot_id, description=''):
        """
        رزرو نوبت مشاوره
        
        Returns:
            dict: {'success': bool, 'appointment': Appointment, 'error': str}
        """
        try:
            # قفل کردن اسلات برای جلوگیری از رزرو همزمان
            slot = TimeSlot.objects.select_for_update().get(id=slot_id)
        except TimeSlot.DoesNotExist:
            return {'success': False, 'error': 'بازه زمانی یافت نشد'}
        
        # بررسی در دسترس بودن
        if not slot.is_available:
            return {'success': False, 'error': 'این بازه زمانی دیگر در دسترس نیست'}
        
        # بررسی اینکه مشاور فعال باشد
        if not slot.consultant.is_active or not slot.consultant.is_verified:
            return {'success': False, 'error': 'مشاور در دسترس نیست'}
        
        # ایجاد نوبت
        appointment = Appointment.objects.create(
            user=user,
            consultant=slot.consultant,
            slot=slot,
            price=slot.price,
            description=description,
            status=Appointment.Status.PENDING
        )
        
        # رزرو اسلات
        slot.status = TimeSlot.SlotStatus.BOOKED
        slot.save(update_fields=['status', 'updated_at'])
        
        logger.info(f"Appointment booked: {appointment.id} by user {user.phone}")
        
        return {'success': True, 'appointment': appointment}
    
    @classmethod
    @transaction.atomic
    def cancel_appointment(cls, appointment, cancelled_by='user'):
        """
        لغو نوبت
        """
        if appointment.status not in [Appointment.Status.PENDING, Appointment.Status.WAITING]:
            return {'success': False, 'error': 'امکان لغو این نوبت وجود ندارد'}
        
        # آزاد کردن اسلات
        appointment.slot.status = TimeSlot.SlotStatus.AVAILABLE
        appointment.slot.save(update_fields=['status', 'updated_at'])
        
        # لغو نوبت
        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=['status', 'updated_at'])
        
        # TODO: اگر پرداخت شده، استرداد به کیف پول
        
        logger.info(f"Appointment cancelled: {appointment.id} by {cancelled_by}")
        
        return {'success': True}
    
    # ─────────────────────────────────────────────────────────────
    # PAYMENT
    # ─────────────────────────────────────────────────────────────
    
    @classmethod
    @transaction.atomic
    def confirm_payment(cls, appointment, payment_transaction):
        """
        تایید پرداخت نوبت
        """
        appointment.payment_transaction = payment_transaction
        appointment.status = Appointment.Status.WAITING
        appointment.save(update_fields=['payment_transaction', 'status', 'updated_at'])
        
        logger.info(f"Appointment paid: {appointment.id}")
        
        return appointment
    
    # ─────────────────────────────────────────────────────────────
    # SESSION
    # ─────────────────────────────────────────────────────────────
    
    @classmethod
    def start_session(cls, appointment):
        """
        شروع جلسه
        """
        if appointment.status != Appointment.Status.WAITING:
            return {'success': False, 'error': 'جلسه قابل شروع نیست'}
        
        appointment.status = Appointment.Status.IN_PROGRESS
        appointment.started_at = timezone.now()
        # TODO: ساخت لینک جلسه ویدیویی
        appointment.session_link = f"https://meet.example.com/{appointment.id}"
        appointment.save()
        
        return {'success': True, 'session_link': appointment.session_link}
    
    @classmethod
    def complete_session(cls, appointment):
        """
        پایان جلسه
        """
        appointment.status = Appointment.Status.COMPLETED
        appointment.finished_at = timezone.now()
        appointment.save()
        
        # بروزرسانی آمار مشاور
        consultant = appointment.consultant
        consultant.total_sessions += 1
        consultant.total_hours += appointment.duration / 60
        consultant.save(update_fields=['total_sessions', 'total_hours'])
        
        return {'success': True}
    
    # ─────────────────────────────────────────────────────────────
    # REVIEWS
    # ─────────────────────────────────────────────────────────────
    
    @classmethod
    def add_review(cls, user, appointment_id, rating, comment=''):
        """
        ثبت نظر برای مشاور
        """
        try:
            appointment = Appointment.objects.get(
                id=appointment_id,
                user=user,
                status=Appointment.Status.COMPLETED
            )
        except Appointment.DoesNotExist:
            return {'success': False, 'error': 'نوبت یافت نشد یا هنوز تکمیل نشده'}
        
        if appointment.has_review:
            return {'success': False, 'error': 'قبلاً نظر ثبت کرده‌اید'}
        
        review = ConsultantReview.objects.create(
            appointment=appointment,
            consultant=appointment.consultant,
            user=user,
            rating=rating,
            comment=comment
        )
        
        appointment.has_review = True
        appointment.save(update_fields=['has_review'])
        
        return {'success': True, 'review': review}
    
    @staticmethod
    def get_consultant_reviews(consultant_id, limit=10):
        """
        نظرات یک مشاور
        """
        return ConsultantReview.objects.filter(
            consultant_id=consultant_id,
            is_approved=True
        ).select_related('user').order_by('-created_at')[:limit]
        