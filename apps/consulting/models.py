# apps/consulting/models.py

"""
Consulting App Models - Ticket-Based Support System

سیستم پشتیبانی و مشاوره شامل:
- ConsultingCategory: دسته‌بندی تیکت‌ها
- SupportTicket: تیکت‌های پشتیبانی با شناسه 7 رقمی
- TicketMessage: پیام‌های چت (از کاربر و پشتیبان)
- TicketAttachment: فایل‌های ضمیمه پیام‌ها (تصاویر تا 5MB)
"""

import uuid
import random
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from django.core.exceptions import ValidationError


def validate_image_size(image):
    """تأیید حجم تصویر (حداکثر 5MB)"""
    if image.size > 5 * 1024 * 1024:  # 5MB
        raise ValidationError('حجم فایل نباید بیشتر از ۵ مگابایت باشد.')


def generate_ticket_id():
    """تولید شناسه 7 رقمی یکتا برای تیکت"""
    while True:
        ticket_id = str(random.randint(1000000, 9999999))
        if not SupportTicket.objects.filter(ticket_id=ticket_id).exists():
            return ticket_id


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY
# ═══════════════════════════════════════════════════════════════════════════════

class ConsultingCategory(models.Model):
    """
    دسته‌بندی تیکت‌های پشتیبانی
    مثال: پشتیبانی فنی، پشتیبانی مالی، سوالات عمومی, ...
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(
        max_length=100,
        verbose_name='نام دسته‌بندی'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        allow_unicode=True,
        verbose_name='اسلاگ'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='آیکون',
        help_text='نام آیکون (مثلاً: support, help, question_answer)'
    )
    
    image = models.ImageField(
        upload_to='consulting/categories/',
        blank=True,
        null=True,
        verbose_name='تصویر'
    )
    
    # Settings
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='ترتیب')
    
    # SEO
    meta_title = models.CharField(max_length=60, blank=True, verbose_name='عنوان متا')
    meta_description = models.CharField(max_length=160, blank=True, verbose_name='توضیحات متا')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'دسته‌بندی تیکت'
        verbose_name_plural = 'دسته‌بندی‌های تیکت'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def ticket_count(self):
        """تعداد تیکت‌های فعال این دسته"""
        return self.tickets.exclude(status='closed').count()


# ═══════════════════════════════════════════════════════════════════════════════
# SUPPORT TICKET
# ═══════════════════════════════════════════════════════════════════════════════

class SupportTicket(models.Model):
    """
    تیکت پشتیبانی
    هر کاربر می‌تواند تیکت ایجاد کند و با پشتیبان (ناشناس) گفتگو کند
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار پاسخ'
        IN_PROGRESS = 'in_progress', 'در حال بررسی'
        ANSWERED = 'answered', 'پاسخ داده شده'
        CLOSED = 'closed', 'بسته شده'
    
    class Priority(models.TextChoices):
        LOW = 'low', 'کم'
        MEDIUM = 'medium', 'متوسط'
        HIGH = 'high', 'زیاد'
        URGENT = 'urgent', 'فوری'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # شناسه 7 رقمی
    ticket_id = models.CharField(
        max_length=7,
        unique=True,
        default=generate_ticket_id,
        editable=False,
        verbose_name='شماره تیکت',
        help_text='شناسه 7 رقمی یکتا'
    )
    
    # کاربر (باید لاگین باشد)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_tickets',
        verbose_name='کاربر'
    )
    
    # دسته‌بندی
    category = models.ForeignKey(
        ConsultingCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name='دسته‌بندی'
    )
    
    # موضوع تیکت
    subject = models.CharField(
        max_length=200,
        verbose_name='موضوع',
        help_text='خلاصه کوتاه از مشکل یا سوال'
    )
    
    # اولین پیام (توضیحات اولیه)
    initial_message = models.TextField(
        verbose_name='توضیحات اولیه',
        help_text='شرح کامل مشکل یا سوال'
    )
    
    # وضعیت
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='وضعیت'
    )
    
    # اولویت
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        null=True,
        blank=True,
        verbose_name='اولویت'
    )
    
    # پشتیبان (ناشناس - فقط برای ادمین)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        verbose_name='پشتیبان تخصیص داده شده',
        help_text='پشتیبانی که به این تیکت اختصاص داده شده (برای کاربر نمایش داده نمی‌شود)'
    )
    
    # تایم‌استمپ‌ها
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان ایجاد تیکت'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='آخرین بروزرسانی'
    )
    last_response_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان آخرین پاسخ',
        help_text='زمانی که آخرین پیام به تیکت اضافه شد'
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان بسته شدن'
    )
    
    # آمار
    message_count = models.PositiveIntegerField(
        default=0,
        verbose_name='تعداد پیام‌ها'
    )
    
    class Meta:
        verbose_name = 'تیکت پشتیبانی'
        verbose_name_plural = 'تیکت‌های پشتیبانی'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ticket_id']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'priority']),
        ]
    
    def __str__(self):
        return f'#{self.ticket_id} - {self.subject[:30]}'
    
    def close(self):
        """بستن تیکت"""
        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()
        self.save(update_fields=['status', 'closed_at', 'updated_at'])
    
    def reopen(self):
        """بازگشایی تیکت"""
        self.status = self.Status.PENDING
        self.closed_at = None
        self.save(update_fields=['status', 'closed_at', 'updated_at'])
    
    def mark_as_answered(self):
        """علامت‌گذاری به عنوان پاسخ داده شده"""
        self.status = self.Status.ANSWERED
        self.last_response_at = timezone.now()
        self.save(update_fields=['status', 'last_response_at', 'updated_at'])
    
    def mark_as_in_progress(self):
        """علامت‌گذاری به عنوان در حال بررسی"""
        self.status = self.Status.IN_PROGRESS
        self.save(update_fields=['status', 'updated_at'])
    
    @property
    def is_closed(self):
        return self.status == self.Status.CLOSED
    
    @property
    def response_time(self):
        """زمان پاسخ (اولین پاسخ پشتیبان)"""
        first_admin_message = self.messages.filter(is_staff_reply=True).first()
        if first_admin_message:
            return first_admin_message.created_at - self.created_at
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# TICKET MESSAGE
# ═══════════════════════════════════════════════════════════════════════════════

class TicketMessage(models.Model):
    """
    پیام‌های چت تیکت
    هم کاربر و هم پشتیبان می‌توانند پیام بفرستند
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='تیکت'
    )
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ticket_messages',
        verbose_name='فرستنده'
    )
    
    # محتوا
    message = models.TextField(
        verbose_name='متن پیام',
        help_text='محتوای پیام'
    )
    
    # آیا این پیام از طرف پشتیبان است؟
    is_staff_reply = models.BooleanField(
        default=False,
        verbose_name='پاسخ پشتیبان',
        help_text='آیا این پیام از طرف پشتیبان است؟ (برای کاربر به عنوان "پشتیبان" نمایش داده می‌شود)'
    )
    
    # آیا کاربر این پیام را خوانده است؟
    is_read = models.BooleanField(
        default=False,
        verbose_name='خوانده شده'
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان خواندن'
    )
    
    # تایم‌استمپ
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان ارسال'
    )
    
    class Meta:
        verbose_name = 'پیام تیکت'
        verbose_name_plural = 'پیام‌های تیکت'
        ordering = ['created_at']
    
    def __str__(self):
        sender_type = 'پشتیبان' if self.is_staff_reply else 'کاربر'
        return f'{sender_type} - {self.ticket.ticket_id} - {self.message[:30]}'
    
    def mark_as_read(self):
        """علامت‌گذاری به عنوان خوانده شده"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # بروزرسانی تیکت
        if is_new:
            self.ticket.message_count = self.ticket.messages.count()
            self.ticket.last_response_at = self.created_at
            
            # اگر پیام از پشتیبان باشد، وضعیت را به "پاسخ داده شده" تغییر بده
            if self.is_staff_reply:
                self.ticket.status = SupportTicket.Status.ANSWERED
            else:
                # اگر پیام از کاربر باشد و تیکت بسته نباشد، وضعیت را به "در انتظار پاسخ" تغییر بده
                if self.ticket.status != SupportTicket.Status.CLOSED:
                    self.ticket.status = SupportTicket.Status.PENDING
            
            self.ticket.save(update_fields=['message_count', 'last_response_at', 'status', 'updated_at'])


# ═══════════════════════════════════════════════════════════════════════════════
# TICKET ATTACHMENT
# ═══════════════════════════════════════════════════════════════════════════════

class TicketAttachment(models.Model):
    """
    فایل‌های ضمیمه پیام‌های تیکت
    فقط تصاویر با حجم حداکثر 5MB
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    message = models.ForeignKey(
        TicketMessage,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='پیام'
    )
    
    file = models.ImageField(
        upload_to='consulting/tickets/attachments/%Y/%m/%d/',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp']),
            validate_image_size
        ],
        verbose_name='فایل',
        help_text='فقط تصاویر با حجم حداکثر 5 مگابایت'
    )
    
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name='حجم فایل (بایت)'
    )
    
    original_filename = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='نام اصلی فایل'
    )
    
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان آپلود'
    )
    
    class Meta:
        verbose_name = 'فایل ضمیمه'
        verbose_name_plural = 'فایل‌های ضمیمه'
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f'Attachment {self.id} - {self.message.ticket.ticket_id}'
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            if not self.original_filename:
                self.original_filename = self.file.name
        super().save(*args, **kwargs)
    
    @property
    def file_size_mb(self):
        """حجم فایل به مگابایت"""
        return round(self.file_size / (1024 * 1024), 2)
