# apps/consulting/signals.py

"""
سیگنال‌های اپ مشاوره
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg

from .models import ConsultantReview, Consultant, Appointment


@receiver(post_save, sender=ConsultantReview)
def update_consultant_rating_on_review(sender, instance, created, **kwargs):
    """
    بروزرسانی امتیاز مشاور پس از ثبت نظر جدید
    """
    if created:
        consultant = instance.consultant
        
        # محاسبه میانگین جدید
        stats = ConsultantReview.objects.filter(
            consultant=consultant,
            is_approved=True
        ).aggregate(
            avg_rating=Avg('rating')
        )
        
        consultant.rating = stats['avg_rating'] or 0
        consultant.review_count = ConsultantReview.objects.filter(
            consultant=consultant,
            is_approved=True
        ).count()
        consultant.save(update_fields=['rating', 'review_count', 'updated_at'])


@receiver(post_delete, sender=ConsultantReview)
def update_consultant_rating_on_review_delete(sender, instance, **kwargs):
    """
    بروزرسانی امتیاز مشاور پس از حذف نظر
    """
    consultant = instance.consultant
    
    stats = ConsultantReview.objects.filter(
        consultant=consultant,
        is_approved=True
    ).aggregate(
        avg_rating=Avg('rating')
    )
    
    consultant.rating = stats['avg_rating'] or 0
    consultant.review_count = ConsultantReview.objects.filter(
        consultant=consultant,
        is_approved=True
    ).count()
    consultant.save(update_fields=['rating', 'review_count', 'updated_at'])


@receiver(post_save, sender=Appointment)
def handle_appointment_status_change(sender, instance, **kwargs):
    """
    اقدامات پس از تغییر وضعیت نوبت
    """
    # اگر نوبت تکمیل شد، آمار مشاور را بروز کن
    if instance.status == Appointment.Status.COMPLETED:
        # می‌توان اینجا نوتیفیکیشن ارسال کرد
        pass
