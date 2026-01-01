import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miniup.settings')
django.setup()

from apps.products.models import Product, Category
from decimal import Decimal

# Gaming product data
gaming_products = [
    {
        'name': 'ماوس گیمینگ لاجیتک G502 HERO',
        'slug': 'logitech-g502-hero-gaming-mouse',
        'description': 'ماوس گیمینگ با سنسور HERO 25K و 11 دکمه قابل برنامه‌ریزی',
        'short_description': 'ماوس گیمینگ حرفه‌ای با دقت بالا',
        'price': Decimal('3500000'),
        'category_name': 'ماوس گیمینگ'
    },
    {
        'name': 'کیبورد مکانیکال ریزر BlackWidow V3',
        'slug': 'razer-blackwidow-v3-mechanical-keyboard',
        'description': 'کیبورد مکانیکال گیمینگ با سوییچ‌های Green و نورپردازی RGB Chroma',
        'short_description': 'کیبورد مکانیکال حرفه‌ای گیمینگ',
        'price': Decimal('4200000'),
        'category_name': 'کیبورد گیمینگ'
    },
    {
        'name': 'هدست استیل‌سریز Arctis 7',
        'slug': 'steelseries-arctis-7-headset',
        'description': 'هدست وایرلس گیمینگ با صدای فوق‌العاده و باتری 24 ساعته',
        'short_description': 'هدست وایرلس با کیفیت صدای عالی',
        'price': Decimal('5800000'),
        'category_name': 'هدست گیمینگ'
    },
    {
        'name': 'ماوس پد ریزر Goliathus Extended',
        'slug': 'razer-goliathus-extended-mousepad',
        'description': 'ماوس پد بزرگ با سطح بافت شده و لبه‌های دوخته شده',
        'short_description': 'ماوس پد گیمینگ سایز بزرگ',
        'price': Decimal('650000'),
        'category_name': 'ماوس پد'
    },
    {
        'name': 'مانیتور گیمینگ ASUS ROG Swift 27"',
        'slug': 'asus-rog-swift-27-gaming-monitor',
        'description': 'مانیتور 27 اینچ با رفرش ریت 240Hz و زمان پاسخ 1ms',
        'short_description': 'مانیتور گیمینگ با رفرش بالا',
        'price': Decimal('18500000'),
        'category_name': 'مانیتور گیمینگ'
    },
    {
        'name': 'صندلی گیمینگ DXRacer Formula Series',
        'slug': 'dxracer-formula-gaming-chair',
        'description': 'صندلی ارگونومیک گیمینگ با پشتی تنظیم‌پذیر و کیفیت ساخت عالی',
        'short_description': 'صندلی گیمینگ حرفه‌ای',
        'price': Decimal('9500000'),
        'category_name': 'صندلی گیمینگ'
    },
    {
        'name': 'ماوس گیمینگ ریزر DeathAdder V2',
        'slug': 'razer-deathadder-v2-gaming-mouse',
        'description': 'ماوس گیمینگ با سنسور Focus+ 20K DPI و سوییچ‌های نوری',
        'short_description': 'ماوس گیمینگ با دقت بالا',
        'price': Decimal('2800000'),
        'category_name': 'ماوس گیمینگ'
    },
    {
        'name': 'کیبورد کورسیر K95 RGB Platinum',
        'slug': 'corsair-k95-rgb-platinum-keyboard',
        'description': 'کیبورد مکانیکال پرمیوم با سوییچ Cherry MX و 6 کلید ماکرو',
        'short_description': 'کیبورد مکانیکال پریمیوم',
        'price': Decimal('5500000'),
        'category_name': 'کیبورد گیمینگ'
    },
    {
        'name': 'هدست هایپرX Cloud II',
        'slug': 'hyperx-cloud-ii-gaming-headset',
        'description': 'هدست گیمینگ با صدای 7.1 مجازی و میکروفون حذف نویز',
        'short_description': 'هدست گیمینگ با صدای 7.1',
        'price': Decimal('3200000'),
        'category_name': 'هدست گیمینگ'
    },
    {
        'name': 'وب‌کم لاجیتک C920 HD Pro',
        'slug': 'logitech-c920-hd-pro-webcam',
        'description': 'وب‌کم Full HD 1080p برای استریم و ضبط ویدیو',
        'short_description': 'وب‌کم Full HD برای استریمینگ',
        'price': Decimal('2400000'),
        'category_name': 'وب کم'
    },
    {
        'name': 'کنترلر Xbox Wireless سری X/S',
        'slug': 'xbox-wireless-controller-series-xs',
        'description': 'کنترلر بی‌سیم ایکس‌باکس با اتصال بلوتوث و باتری 40 ساعته',
        'short_description': 'کنترلر بی‌سیم Xbox',
        'price': Decimal('2900000'),
        'category_name': 'کنترلر گیمینگ'
    },
    {
        'name': 'ماوس لاجیتک G Pro X Superlight',
        'slug': 'logitech-g-pro-x-superlight-mouse',
        'description': 'ماوس وایرلس فوق سبک 63 گرمی برای بازی‌های حرفه‌ای',
        'short_description': 'ماوس وایرلس فوق سبک',
        'price': Decimal('4500000'),
        'category_name': 'ماوس گیمینگ'
    },
    {
        'name': 'کیبورد مینی HyperX Alloy Origins 60',
        'slug': 'hyperx-alloy-origins-60-keyboard',
        'description': 'کیبورد مکانیکال 60 درصد با طراحی کامپکت و سوییچ HyperX',
        'short_description': 'کیبورد مکانیکال کامپکت',
        'price': Decimal('3400000'),
        'category_name': 'کیبورد گیمینگ'
    },
    {
        'name': 'میکروفون Blue Yeti X',
        'slug': 'blue-yeti-x-usb-microphone',
        'description': 'میکروفون USB چهار الگوی قطبی برای استریم و پادکست',
        'short_description': 'میکروفون حرفه‌ای استریمینگ',
        'price': Decimal('5200000'),
        'category_name': 'میکروفون'
    },
    {
        'name': 'هدست بی‌سیم لاجیتک G733',
        'slug': 'logitech-g733-wireless-headset',
        'description': 'هدست وایرلس سبک با نورپردازی RGB و صدای فضایی',
        'short_description': 'هدست وایرلس سبک و راحت',
        'price': Decimal('4200000'),
        'category_name': 'هدست گیمینگ'
    },
    {
        'name': 'ماوس پد RGB کورسیر MM700',
        'slug': 'corsair-mm700-rgb-mousepad',
        'description': 'ماوس پد بزرگ با نورپردازی RGB و پورت شارژ USB',
        'short_description': 'ماوس پد RGB با قابلیت شارژ',
        'price': Decimal('1800000'),
        'category_name': 'ماوس پد'
    },
    {
        'name': 'مانیتور گیمینگ Samsung Odyssey G7',
        'slug': 'samsung-odyssey-g7-gaming-monitor',
        'description': 'مانیتور 32 اینچ منحنی با رفرش 240Hz و تکنولوژی QLED',
        'short_description': 'مانیتور منحنی QLED گیمینگ',
        'price': Decimal('22000000'),
        'category_name': 'مانیتور گیمینگ'
    },
    {
        'name': 'چراغ نواری Philips Hue Play',
        'slug': 'philips-hue-play-light-bar',
        'description': 'نوار LED هوشمند برای محیط گیمینگ با کنترل از طریق اپلیکیشن',
        'short_description': 'نوار LED هوشمند RGB',
        'price': Decimal('3500000'),
        'category_name': 'نورپردازی'
    },
    {
        'name': 'کنترلر DualSense پلی‌استیشن 5',
        'slug': 'ps5-dualsense-wireless-controller',
        'description': 'کنترلر بی‌سیم PS5 با فیدبک لمسی و ماشه‌های تطبیقی',
        'short_description': 'کنترلر DualSense پلی‌استیشن',
        'price': Decimal('3800000'),
        'category_name': 'کنترلر گیمینگ'
    },
    {
        'name': 'کولر پردازنده NZXT Kraken Z73',
        'slug': 'nzxt-kraken-z73-cpu-cooler',
        'description': 'کولر مایع 360mm با نمایشگر LCD و RGB سینک‌شده',
        'short_description': 'کولر مایع با نمایشگر LCD',
        'price': Decimal('12500000'),
        'category_name': 'کولینگ'
    }
]

print("�� شروع ایجاد محصولات گیمینگ...")
print("=" * 60)

created_count = 0
skipped_count = 0

for product_data in gaming_products:
    category_name = product_data.pop('category_name')
    
    # Get or create category
    category, cat_created = Category.objects.get_or_create(
        name=category_name,
        defaults={
            'slug': category_name.replace(' ', '-').lower(),
            'is_active': True,
            'sort_order': 0
        }
    )
    
    if cat_created:
        print(f"✨ دسته‌بندی جدید: {category_name}")
    
    # Check if product already exists
    if Product.objects.filter(slug=product_data['slug']).exists():
        print(f"⏭️  محصول موجود است: {product_data['name']}")
        skipped_count += 1
        continue
    
    # Create product
    product = Product.objects.create(
        category=category,
        sub_type=Product.ProductSubType.GAMING,
        is_active=True,
        stock=50,
        **product_data
    )
    
    created_count += 1
    print(f"✅ ایجاد شد: {product.name} - {product.price:,} تومان")

print("=" * 60)
print(f"✨ تعداد محصولات ایجاد شده: {created_count}")
print(f"⏭️  تعداد محصولات موجود: {skipped_count}")
print(f"📦 مجموع محصولات گیمینگ: {Product.objects.filter(sub_type=Product.ProductSubType.GAMING).count()}")
print("\n🎉 تمام شد!")
