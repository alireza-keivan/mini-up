"""
Django Management Command: Cleanup Expired Unpaid Coupon Usages

This command removes CouponUsage records for orders that were never paid.
It also decrements the coupon's used_count to free up those slots.

Usage:
    python manage.py cleanup_unpaid_coupons
    python manage.py cleanup_unpaid_coupons --dry-run
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from apps.coupons.models import Coupon, CouponUsage
from apps.orders.models import Order


class Command(BaseCommand):
    help = 'پاکسازی کوپن‌های استفاده‌شده در سفارشات پرداخت‌نشده'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='نمایش تغییرات بدون اعمال آن‌ها'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 حالت آزمایشی - هیچ تغییری اعمال نمی‌شود'))
        
        # پیدا کردن سفارشات منقضی‌شده که هنوز پرداخت نشده‌اند
        expired_unpaid_orders = Order.objects.filter(
            status__in=[Order.Status.PENDING, Order.Status.FAILED],
            expires_at__lt=timezone.now(),
            coupon__isnull=False  # فقط سفارشاتی که کوپن دارند
        ).select_related('coupon')
        
        total_orders = expired_unpaid_orders.count()
        
        if total_orders == 0:
            self.stdout.write(self.style.SUCCESS('✅ هیچ کوپن پرداخت‌نشده‌ای برای پاکسازی یافت نشد'))
            return
        
        self.stdout.write(f'📊 تعداد سفارشات منقضی‌شده با کوپن: {total_orders}')
        
        cleaned_count = 0
        coupons_updated = {}
        
        for order in expired_unpaid_orders:
            coupon = order.coupon
            
            # پیدا کردن CouponUsage مربوط به این سفارش
            usages = CouponUsage.objects.filter(
                order=order,
                coupon=coupon
            )
            
            usage_count = usages.count()
            
            if usage_count > 0:
                if not dry_run:
                    with transaction.atomic():
                        # حذف CouponUsage
                        usages.delete()
                        
                        # کاهش used_count کوپن
                        if coupon.used_count >= usage_count:
                            coupon.used_count -= usage_count
                            coupon.save(update_fields=['used_count'])
                
                # آمار
                if coupon.code not in coupons_updated:
                    coupons_updated[coupon.code] = 0
                coupons_updated[coupon.code] += usage_count
                
                cleaned_count += usage_count
                
                self.stdout.write(
                    f'  - سفارش {order.order_number}: کوپن {coupon.code} آزاد شد'
                )
        
        # نمایش خلاصه
        self.stdout.write(self.style.SUCCESS(f'\n✅ تعداد کوپن‌های پاکسازی شده: {cleaned_count}'))
        
        if coupons_updated:
            self.stdout.write('\n📈 کوپن‌های به‌روزرسانی شده:')
            for code, count in coupons_updated.items():
                coupon = Coupon.objects.get(code=code)
                self.stdout.write(
                    f'  - {code}: {count} استفاده آزاد شد (used_count: {coupon.used_count})'
                )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  این یک آزمایش بود. برای اعمال تغییرات، بدون --dry-run اجرا کنید'))
