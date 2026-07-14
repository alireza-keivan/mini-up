#!/usr/bin/env python
"""
Populate database with virtual service categories and products for testing.
Run with: python populate_virtual_services.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miniup.settings.dev')
django.setup()

from apps.products.models import Product, Category
from apps.accounts.models import User
from decimal import Decimal

def populate_data():
    # Get or create a superuser for vendor - use first existing superuser or create one
    try:
        vendor = User.objects.filter(is_superuser=True, is_staff=True).first()
        if not vendor:
            # Create a new admin user
            vendor = User.objects.create_superuser(
                phone='09123456789',
                email='admin@miniup.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
            )
            print(f"✅ Created admin user with phone: 09123456789")
        else:
            print(f"✅ Using existing admin user: {vendor.phone}")
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        return

    # Categories and their products
    categories_data = {
        'خدمات شبکه‌های اجتماعی': [
            {'name': 'افزایش فالوور اینستاگرام', 'price': 50000, 'description': 'افزایش فالوور واقعی و فعال اینستاگرام'},
            {'name': 'افزایش لایک پست', 'price': 25000, 'description': 'لایک واقعی برای پست‌های اینستاگرام'},
            {'name': 'افزایش ویو استوری', 'price': 15000, 'description': 'افزایش بازدید استوری‌های اینستاگرام'},
            {'name': 'افزایش کامنت', 'price': 30000, 'description': 'کامنت واقعی و مرتبط برای پست‌ها'},
            {'name': 'افزایش فالوور توییتر', 'price': 45000, 'description': 'فالوور فعال و واقعی توییتر'},
            {'name': 'افزایش سابسکرایبر یوتیوب', 'price': 80000, 'description': 'سابسکرایبر واقعی برای کانال یوتیوب'},
        ],
        'خدمات استریم و پخش زنده': [
            {'name': 'افزایش بینندگان لایو', 'price': 100000, 'description': 'افزایش تعداد بینندگان پخش زنده'},
            {'name': 'خرید هدیه برای استریمر', 'price': 50000, 'description': 'ارسال هدایای مجازی در پخش زنده'},
            {'name': 'افزایش دنبال‌کننده توییچ', 'price': 60000, 'description': 'فالوور واقعی برای کانال توییچ'},
            {'name': 'افزایش ویو ویدیو', 'price': 35000, 'description': 'افزایش بازدید ویدیوهای آپلود شده'},
            {'name': 'تبلیغات در استریم', 'price': 150000, 'description': 'نمایش تبلیغات در پخش‌های زنده'},
        ],
        'خدمات موزیک و پادکست': [
            {'name': 'افزایش پلی اسپاتیفای', 'price': 40000, 'description': 'افزایش تعداد پخش آهنگ در اسپاتیفای'},
            {'name': 'افزایش فالوور هنرمند', 'price': 55000, 'description': 'افزایش فالوور پروفایل هنرمند'},
            {'name': 'افزایش شنونده پادکست', 'price': 45000, 'description': 'افزایش تعداد شنونده پادکست'},
            {'name': 'افزایش لایک موزیک', 'price': 20000, 'description': 'لایک برای آهنگ‌ها و آلبوم‌ها'},
            {'name': 'ثبت در پلی‌لیست', 'price': 75000, 'description': 'قرار گرفتن آهنگ در پلی‌لیست‌های محبوب'},
        ],
        'خدمات بازی و گیمینگ': [
            {'name': 'بوست اکانت بازی', 'price': 200000, 'description': 'افزایش رنک و سطح در بازی‌ها'},
            {'name': 'کوچینگ بازی', 'price': 150000, 'description': 'آموزش تخصصی بازی توسط بازیکنان حرفه‌ای'},
            {'name': 'فارم کردن منابع', 'price': 80000, 'description': 'جمع‌آوری منابع و آیتم در بازی'},
            {'name': 'انجام ماموریت‌ها', 'price': 100000, 'description': 'تکمیل ماموریت‌های سخت بازی'},
            {'name': 'تیم یابی رنک', 'price': 50000, 'description': 'پیدا کردن تیم برای بازی رنک'},
        ],
        'خدمات طراحی و گرافیک': [
            {'name': 'طراحی لوگو', 'price': 300000, 'description': 'طراحی لوگوی حرفه‌ای و منحصر به فرد'},
            {'name': 'طراحی بنر شبکه اجتماعی', 'price': 150000, 'description': 'بنر و کاور برای شبکه‌های اجتماعی'},
            {'name': 'طراحی پوستر', 'price': 200000, 'description': 'پوستر تبلیغاتی و اطلاع‌رسانی'},
            {'name': 'ویرایش عکس حرفه‌ای', 'price': 100000, 'description': 'رتوش و ویرایش عکس'},
            {'name': 'طراحی کارت ویزیت', 'price': 120000, 'description': 'کارت ویزیت شخصی و تجاری'},
            {'name': 'طراحی اینفوگرافیک', 'price': 250000, 'description': 'اینفوگرافیک جذاب و اطلاعاتی'},
        ],
        'خدمات ویدیو و انیمیشن': [
            {'name': 'تدوین ویدیو', 'price': 180000, 'description': 'تدوین حرفه‌ای ویدیوهای کوتاه و بلند'},
            {'name': 'ساخت اینترو', 'price': 150000, 'description': 'اینترو حرفه‌ای برای ویدیوها'},
            {'name': 'موشن گرافیک', 'price': 300000, 'description': 'انیمیشن موشن گرافیک'},
            {'name': 'زیرنویس و ترجمه', 'price': 80000, 'description': 'زیرنویس فارسی و انگلیسی'},
            {'name': 'افکت ویژه', 'price': 250000, 'description': 'اضافه کردن جلوه‌های ویژه به ویدیو'},
        ],
        'خدمات نویسندگی و محتوا': [
            {'name': 'نویسندگی مقاله', 'price': 120000, 'description': 'نوشتن مقاله تخصصی و عمومی'},
            {'name': 'تولید محتوای شبکه اجتماعی', 'price': 100000, 'description': 'کپشن و محتوا برای پست‌ها'},
            {'name': 'ترجمه متن', 'price': 90000, 'description': 'ترجمه حرفه‌ای فارسی و انگلیسی'},
            {'name': 'ویراستاری', 'price': 80000, 'description': 'ویراستاری ادبی و علمی متون'},
            {'name': 'نویسندگی اسکریپت', 'price': 150000, 'description': 'نوشتن اسکریپت برای ویدیو و پادکست'},
        ],
        'خدمات صوتی و دوبلاژ': [
            {'name': 'دوبلاژ حرفه‌ای', 'price': 200000, 'description': 'دوبلاژ برای ویدیو و انیمیشن'},
            {'name': 'گویندگی', 'price': 150000, 'description': 'گویندگی برای تبلیغات و مستند'},
            {'name': 'میکس و مستر', 'price': 180000, 'description': 'میکس و مسترینگ حرفه‌ای صدا'},
            {'name': 'ضبط پادکست', 'price': 120000, 'description': 'ضبط و تنظیم کیفیت پادکست'},
            {'name': 'ساخت جینگل', 'price': 100000, 'description': 'ساخت جینگل تبلیغاتی'},
        ],
        'خدمات مشاوره و آموزش': [
            {'name': 'مشاوره کسب‌وکار', 'price': 250000, 'description': 'مشاوره راه‌اندازی و توسعه کسب‌وکار'},
            {'name': 'مشاوره دیجیتال مارکتینگ', 'price': 200000, 'description': 'استراتژی بازاریابی دیجیتال'},
            {'name': 'آموزش برنامه‌نویسی', 'price': 180000, 'description': 'آموزش خصوصی برنامه‌نویسی'},
            {'name': 'مشاوره سئو', 'price': 220000, 'description': 'بهینه‌سازی وبسایت برای موتورهای جستجو'},
            {'name': 'آموزش شبکه‌های اجتماعی', 'price': 150000, 'description': 'آموزش اینستاگرام و شبکه‌های اجتماعی'},
        ],
        'خدمات برنامه‌نویسی': [
            {'name': 'توسعه وبسایت', 'price': 500000, 'description': 'طراحی و توسعه وبسایت اختصاصی'},
            {'name': 'توسعه اپلیکیشن', 'price': 800000, 'description': 'ساخت اپلیکیشن موبایل'},
            {'name': 'رفع باگ و خطا', 'price': 150000, 'description': 'پیدا کردن و رفع باگ‌های نرم‌افزار'},
            {'name': 'طراحی دیتابیس', 'price': 300000, 'description': 'طراحی و بهینه‌سازی پایگاه داده'},
            {'name': 'توسعه بات', 'price': 200000, 'description': 'ساخت ربات تلگرام و دیسکورد'},
        ],
    }

    print("\n🚀 Starting database population...\n")
    
    total_categories = 0
    total_products = 0

    for category_name, products in categories_data.items():
        # Create category
        category, created = Category.objects.get_or_create(
            name=category_name,
            defaults={
                'slug': category_name.replace(' ', '-').replace('‌', '-'),
                'is_active': True,
            }
        )
        if created:
            total_categories += 1
            print(f"✅ Created category: {category_name}")
        else:
            print(f"⏭️  Category already exists: {category_name}")

        # Create products
        for product_data in products:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                category=category,
                defaults={
                    'slug': product_data['name'].replace(' ', '-').replace('‌', '-'),
                    'short_description': product_data['description'],
                    'description': f"{product_data['description']}. این خدمات با کیفیت بالا و تحویل سریع ارائه می‌شود.",
                    'price': Decimal(product_data['price']),
                    'product_type': Product.ProductType.VIRTUAL,
                    'sub_type': Product.ProductSubType.VIRTUAL_SERVICE,
                    'is_active': True,
                    'stock': 999,  # Virtual services have unlimited stock
                    'track_stock': False,  # Don't track stock for virtual services
                }
            )
            if created:
                total_products += 1
                print(f"  ➕ Added product: {product_data['name']} - {product_data['price']:,} تومان")
            else:
                print(f"  ⏭️  Product already exists: {product_data['name']}")

    print("\n" + "="*60)
    print(f"✨ Population complete!")
    print(f"📁 Categories created: {total_categories}")
    print(f"📦 Products created: {total_products}")
    print(f"🌐 View at: http://127.0.0.1:8000/virtual-services/")
    print("="*60 + "\n")

if __name__ == '__main__':
    populate_data()
