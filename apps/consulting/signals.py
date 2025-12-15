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


# ═══════════════════════════════════════════════════════════════════════════════
# TICKET NOTIFICATION SIGNALS
# ═══════════════════════════════════════════════════════════════════════════════

from .models import TicketMessage, SupportTicket


@receiver(post_save, sender=TicketMessage)
def notify_ticket_message(sender, instance, created, **kwargs):
    """
    ارسال اعلان پس از ارسال پیام در تیکت
    """
    if not created:
        return
    
    # فقط برای پیام‌های کارمندان به کاربر اعلان ارسال شود
    if instance.is_staff_reply:
        try:
            from apps.content.services import NotificationService
            NotificationService.notify_ticket_response(instance.ticket)
        except Exception as e:
            print(f"Failed to send ticket response notification: {e}")


@receiver(post_save, sender=SupportTicket)
def notify_ticket_status_change(sender, instance, created, **kwargs):
    """
    ارسال اعلان هنگام تغییر وضعیت تیکت
    """
    if created:
        return
    
    # اگر تیکت بسته شد
    if hasattr(instance, '_old_status') and instance._old_status != 'closed' and instance.status == 'closed':
        try:
            from apps.content.services import NotificationService
            NotificationService.notify_ticket_closed(instance)
        except Exception as e:
            print(f"Failed to send ticket closed notification: {e}")
