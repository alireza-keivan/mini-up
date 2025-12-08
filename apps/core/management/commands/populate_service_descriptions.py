# apps/core/management/commands/populate_service_descriptions.py

from django.core.management.base import BaseCommand
from apps.core.models import ServiceDescription


class Command(BaseCommand):
    help = 'پر کردن جدول توضیحات خدمات با داده‌های پیش‌فرض'

    def handle(self, *args, **options):
        # حذف داده‌های قبلی
        ServiceDescription.objects.all().delete()
        
        # ایجاد توضیحات خدمات
        descriptions = [
            {
                'service_type': 'virtual',
                'title': 'خدمات مجازی',
                'description': 'تلگرام پرمیوم، اسپاتیفای، اپل آیدی، نتفلیکس و سایر خدمات مجازی با بهترین قیمت و کیفیت. تحویل فوری و پشتیبانی ۲۴ ساعته.',
                'is_active': True
            },
            {
                'service_type': 'mini_game',
                'title': 'مینی گیم',
                'description': 'خرید جم، سکه و کوین بازی‌های محبوب مثل کلش، پابجی، فری فایر با قیمت استثنایی. شارژ سریع و امن حساب بازی شما.',
                'is_active': True
            },
            {
                'service_type': 'gaming_products',
                'title': 'محصولات گیمینگ',
                'description': 'گیفت کارت پلی استیشن، ایکس باکس، استیم، گوگل پلی و ایتونز با قیمت مناسب. کد دیجیتال با تحویل آنی پس از خرید.',
                'is_active': True
            },
            {
                'service_type': 'accessories',
                'title': 'لوازم جانبی گیمینگ',
                'description': 'فن خنک‌کننده موبایل، دسته بازی، هدست گیمینگ و سایر لوازم جانبی با کیفیت بالا. ارسال سریع به سراسر کشور.',
                'is_active': True
            }
        ]
        
        created_count = 0
        for desc_data in descriptions:
            desc, created = ServiceDescription.objects.get_or_create(
                service_type=desc_data['service_type'],
                defaults=desc_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ ایجاد شد: {desc.get_service_type_display()}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'• از قبل وجود دارد: {desc.get_service_type_display()}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ تعداد {created_count} توضیح جدید ایجاد شد.')
        )
        self.stdout.write(
            self.style.SUCCESS(f'✓ مجموع توضیحات: {ServiceDescription.objects.count()}')
        )
