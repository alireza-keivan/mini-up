#!/usr/bin/env python
"""
Populate physical products for gaming and peripheral categories.
Creates diverse products with varied attributes for filtering demonstration.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miniup.settings')
django.setup()

from apps.products.models import Category, Brand, Product
from decimal import Decimal

def create_categories():
    """Create gaming and peripheral categories."""
    gaming_category, _ = Category.objects.get_or_create(
        slug='gaming-products',
        defaults={
            'name': 'محصولات گیمینگ',
            'name_en': 'Gaming Products',
            'description': 'تجهیزات و لوازم گیمینگ حرفه‌ای',
            'icon': 'fa-gamepad',
            'is_active': True,
            'is_featured': True,
            'sort_order': 1
        }
    )
    
    peripheral_category, _ = Category.objects.get_or_create(
        slug='buy-products',
        defaults={
            'name': 'محصولات جانبی',
            'name_en': 'Buy Products',
            'description': 'لوازم جانبی کامپیوتر و موبایل',
            'icon': 'fa-laptop',
            'is_active': True,
            'is_featured': True,
            'sort_order': 2
        }
    )
    
    return gaming_category, peripheral_category


def create_brands():
    """Create popular brands."""
    brands_data = [
        ('Razer', 'razer', 'برند پیشرو در تجهیزات گیمینگ'),
        ('Logitech', 'logitech', 'برند معتبر در لوازم جانبی'),
        ('SteelSeries', 'steelseries', 'برند حرفه‌ای گیمینگ'),
        ('HyperX', 'hyperx', 'هدست و کیبورد گیمینگ'),
        ('Corsair', 'corsair', 'قدرت و کیفیت در گیمینگ'),
        ('ASUS ROG', 'asus-rog', 'برند Republic of Gamers'),
        ('Anker', 'anker', 'لوازم جانبی با کیفیت'),
        ('Samsung', 'samsung', 'محصولات الکترونیک سامسونگ'),
        ('Apple', 'apple', 'محصولات اپل'),
        ('Xiaomi', 'xiaomi', 'محصولات شیائومی'),
    ]
    
    brands = {}
    for name, slug, desc in brands_data:
        brand, _ = Brand.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'name_en': name,
                'description': desc,
                'is_active': True
            }
        )
        brands[slug] = brand
    
    return brands


def create_gaming_products(category, brands):
    """Create gaming products with diverse attributes."""
    
    gaming_products = [
        # Gaming Mice
        {
            'name': 'ماوس گیمینگ Razer DeathAdder V3',
            'name_en': 'Razer DeathAdder V3 Gaming Mouse',
            'slug': 'razer-deathadder-v3',
            'brand': brands['razer'],
            'price': 4500000,
            'original_price': 5200000,
            'stock': 25,
            'short_description': 'ماوس گیمینگ حرفه‌ای با سنسور نوری 30000 DPI',
            'description': 'ماوس گیمینگ Razer DeathAdder V3 با سنسور Focus Pro 30K و سوئیچ‌های نوری نسل سوم',
            'specifications': {
                'DPI': '30000',
                'سنسور': 'Focus Pro 30K Optical',
                'سوئیچ': 'Razer Optical Gen-3',
                'وزن': '59 گرم',
                'اتصال': 'سیم + بی‌سیم',
                'RGB': 'بله'
            },
            'weight': 59,
        },
        {
            'name': 'ماوس گیمینگ Logitech G502 Hero',
            'name_en': 'Logitech G502 Hero Gaming Mouse',
            'slug': 'logitech-g502-hero',
            'brand': brands['logitech'],
            'price': 2800000,
            'original_price': 3200000,
            'stock': 40,
            'short_description': 'ماوس گیمینگ با 11 دکمه قابل برنامه‌ریزی',
            'description': 'ماوس گیمینگ Logitech G502 Hero با سنسور HERO 25K و وزن قابل تنظیم',
            'specifications': {
                'DPI': '25600',
                'سنسور': 'HERO 25K',
                'دکمه': '11 دکمه',
                'وزن': '121 گرم',
                'اتصال': 'سیمی',
                'RGB': 'بله'
            },
            'weight': 121,
        },
        {
            'name': 'ماوس بی‌سیم Razer Viper Ultimate',
            'name_en': 'Razer Viper Ultimate Wireless',
            'slug': 'razer-viper-ultimate',
            'brand': brands['razer'],
            'price': 5800000,
            'stock': 15,
            'short_description': 'ماوس بی‌سیم فوق سبک با سنسور 20K DPI',
            'description': 'ماوس گیمینگ بی‌سیم Razer Viper Ultimate با باتری 70 ساعته',
            'specifications': {
                'DPI': '20000',
                'سنسور': 'Focus+ Optical',
                'وزن': '74 گرم',
                'باتری': '70 ساعت',
                'اتصال': 'بی‌سیم 2.4GHz',
                'RGB': 'بله'
            },
            'weight': 74,
        },
        
        # Gaming Keyboards
        {
            'name': 'کیبورد مکانیکال Corsair K70 RGB Pro',
            'name_en': 'Corsair K70 RGB Pro Mechanical',
            'slug': 'corsair-k70-rgb-pro',
            'brand': brands['corsair'],
            'price': 6500000,
            'original_price': 7200000,
            'stock': 20,
            'short_description': 'کیبورد مکانیکال با سوئیچ Cherry MX',
            'description': 'کیبورد گیمینگ مکانیکال Corsair K70 RGB Pro با نورپردازی RGB پیشرفته',
            'specifications': {
                'سوئیچ': 'Cherry MX Red/Blue/Brown',
                'نوع': 'مکانیکال',
                'RGB': 'Per-key RGB',
                'اتصال': 'سیمی USB',
                'Anti-Ghosting': 'بله',
                'Media Keys': 'دارد'
            },
            'weight': 1200,
        },
        {
            'name': 'کیبورد بی‌سیم Logitech G915 TKL',
            'name_en': 'Logitech G915 TKL Wireless',
            'slug': 'logitech-g915-tkl',
            'brand': brands['logitech'],
            'price': 8900000,
            'stock': 12,
            'short_description': 'کیبورد مکانیکال بی‌سیم با سوئیچ low-profile',
            'description': 'کیبورد گیمینگ بی‌سیم Logitech G915 TKL با باتری 40 ساعته',
            'specifications': {
                'سوئیچ': 'GL Tactile/Linear/Clicky',
                'نوع': 'مکانیکال Low-Profile',
                'RGB': 'Lightsync RGB',
                'باتری': '40 ساعت',
                'اتصال': 'Lightspeed Wireless',
                'فرمت': 'TKL (Tenkeyless)'
            },
            'weight': 810,
        },
        
        # Gaming Headsets
        {
            'name': 'هدست گیمینگ HyperX Cloud II',
            'name_en': 'HyperX Cloud II Gaming Headset',
            'slug': 'hyperx-cloud-ii',
            'brand': brands['hyperx'],
            'price': 3200000,
            'original_price': 3800000,
            'stock': 35,
            'short_description': 'هدست گیمینگ با صدای 7.1 مجازی',
            'description': 'هدست گیمینگ HyperX Cloud II با درایور 53mm و میکروفون قابل جدا',
            'specifications': {
                'درایور': '53mm',
                'فرکانس': '15Hz - 25KHz',
                'صدا': '7.1 Virtual Surround',
                'میکروفون': 'قابل جداسازی',
                'اتصال': 'USB + 3.5mm',
                'وزن': '275 گرم'
            },
            'weight': 275,
        },
        {
            'name': 'هدست بی‌سیم SteelSeries Arctis 7',
            'name_en': 'SteelSeries Arctis 7 Wireless',
            'slug': 'steelseries-arctis-7',
            'brand': brands['steelseries'],
            'price': 4800000,
            'stock': 22,
            'short_description': 'هدست بی‌سیم با باتری 24 ساعته',
            'description': 'هدست گیمینگ بی‌سیم SteelSeries Arctis 7 با صدای فوق‌العاده',
            'specifications': {
                'درایور': '40mm Neodymium',
                'فرکانس': '20Hz - 20KHz',
                'باتری': '24 ساعت',
                'اتصال': 'بی‌سیم 2.4GHz',
                'میکروفون': 'ClearCast Bidirectional',
                'سازگاری': 'PC, PS, Xbox, Mobile'
            },
            'weight': 353,
        },
        
        # Gaming Monitors
        {
            'name': 'مانیتور گیمینگ ASUS ROG Swift 27"',
            'name_en': 'ASUS ROG Swift 27" Gaming Monitor',
            'slug': 'asus-rog-swift-27',
            'brand': brands['asus-rog'],
            'price': 18500000,
            'original_price': 21000000,
            'stock': 8,
            'short_description': 'مانیتور 27 اینچ با رفرش ریت 240Hz',
            'description': 'مانیتور گیمینگ ASUS ROG Swift با پنل IPS و G-Sync',
            'specifications': {
                'سایز': '27 اینچ',
                'رزولوشن': '2560x1440 (QHD)',
                'پنل': 'IPS',
                'رفرش ریت': '240Hz',
                'زمان پاسخ': '1ms',
                'HDR': 'HDR10',
                'فناوری': 'G-Sync Compatible'
            },
            'weight': 6200,
        },
        {
            'name': 'مانیتور گیمینگ Samsung Odyssey G7',
            'name_en': 'Samsung Odyssey G7 Gaming Monitor',
            'slug': 'samsung-odyssey-g7',
            'brand': brands['samsung'],
            'price': 15800000,
            'stock': 10,
            'short_description': 'مانیتور منحنی 32 اینچ با 240Hz',
            'description': 'مانیتور منحنی Samsung Odyssey G7 با پنل QLED',
            'specifications': {
                'سایز': '32 اینچ',
                'رزولوشن': '2560x1440 (QHD)',
                'پنل': 'QLED VA Curved',
                'رفرش ریت': '240Hz',
                'زمان پاسخ': '1ms',
                'انحنا': '1000R',
                'فناوری': 'FreeSync Premium Pro'
            },
            'weight': 7400,
        },
        
        # Gaming Chairs
        {
            'name': 'صندلی گیمینگ Razer Iskur',
            'name_en': 'Razer Iskur Gaming Chair',
            'slug': 'razer-iskur-chair',
            'brand': brands['razer'],
            'price': 16500000,
            'stock': 6,
            'short_description': 'صندلی گیمینگ حرفه‌ای با تکیه‌گاه کمری',
            'description': 'صندلی گیمینگ Razer Iskur با طراحی ارگونومیک و تکیه‌گاه لومبار داخلی',
            'specifications': {
                'جنس': 'چرم مصنوعی Multi-layered',
                'ظرفیت وزن': '136 کیلوگرم',
                'ارتفاع': 'قابل تنظیم',
                'دسته': 'قابل تنظیم 4D',
                'تکیه‌گاه': 'لومبار داخلی',
                'چرخ': '65mm PU Caster'
            },
            'weight': 32000,
        },
    ]
    
    created_products = []
    for product_data in gaming_products:
        product, created = Product.objects.get_or_create(
            slug=product_data['slug'],
            defaults={
                **product_data,
                'category': category,
                'product_type': Product.ProductType.PHYSICAL,
                'sub_type': Product.ProductSubType.GAMING,
                'delivery_type': Product.DeliveryType.SHIPPING,
                'track_stock': True,
                'is_active': True,
                'is_featured': True,
            }
        )
        created_products.append(product)
        print(f"{'✅ Created' if created else '⚠️  Already exists'}: {product.name}")
    
    return created_products


def create_peripheral_products(category, brands):
    """Create peripheral/accessory products."""
    
    peripheral_products = [
        # USB Hubs
        {
            'name': 'هاب USB-C آنکر 7 پورت',
            'name_en': 'Anker 7-Port USB-C Hub',
            'slug': 'anker-7port-usbc-hub',
            'brand': brands['anker'],
            'price': 1800000,
            'original_price': 2200000,
            'stock': 50,
            'short_description': 'هاب 7 پورت با پورت شارژ 100W',
            'description': 'هاب USB-C آنکر با 7 پورت USB 3.0 و توان شارژ 100 وات',
            'specifications': {
                'پورت': '7x USB 3.0',
                'شارژ': '100W Power Delivery',
                'سرعت': '5Gbps',
                'سازگاری': 'MacBook, PC, Tablet',
                'طول کابل': '60 سانتی‌متر'
            },
            'weight': 125,
        },
        {
            'name': 'هاب Thunderbolt 4 هایپر',
            'name_en': 'HyperDrive Thunderbolt 4 Hub',
            'slug': 'hyperdrive-tb4-hub',
            'brand': brands['anker'],
            'price': 4500000,
            'stock': 20,
            'short_description': 'هاب Thunderbolt 4 با 11 پورت',
            'description': 'هاب حرفه‌ای Thunderbolt 4 با پشتیبانی از دو مانیتور 4K',
            'specifications': {
                'پورت': '11 پورت متنوع',
                'Thunderbolt': '40Gbps',
                'شارژ': '96W',
                'مانیتور': '2x 4K @ 60Hz',
                'سازگاری': 'Mac, PC'
            },
            'weight': 280,
        },
        
        # Power Banks
        {
            'name': 'پاوربانک آنکر 20000mAh',
            'name_en': 'Anker PowerCore 20000mAh',
            'slug': 'anker-powercore-20000',
            'brand': brands['anker'],
            'price': 1500000,
            'original_price': 1800000,
            'stock': 60,
            'short_description': 'پاوربانک 20000 میلی‌آمپر با شارژ سریع',
            'description': 'پاوربانک Anker PowerCore با ظرفیت 20000mAh و فناوری PowerIQ',
            'specifications': {
                'ظرفیت': '20000mAh',
                'ورودی': 'USB-C 18W',
                'خروجی': '2x USB-A + 1x USB-C',
                'شارژ سریع': 'PowerIQ 2.0',
                'وزن': '356 گرم'
            },
            'weight': 356,
        },
        {
            'name': 'پاوربانک شیائومی 30000mAh',
            'name_en': 'Xiaomi Power Bank 30000mAh',
            'slug': 'xiaomi-powerbank-30000',
            'brand': brands['xiaomi'],
            'price': 2200000,
            'stock': 40,
            'short_description': 'پاوربانک 30000 با شارژ دو طرفه سریع',
            'description': 'پاوربانک شیائومی با ظرفیت بالا و شارژ سریع 65W',
            'specifications': {
                'ظرفیت': '30000mAh',
                'ورودی': 'USB-C 65W',
                'خروجی': '2x USB-A + 2x USB-C',
                'شارژ سریع': 'PD 3.0, QC 3.0',
                'وزن': '580 گرم'
            },
            'weight': 580,
        },
        
        # Phone Cases
        {
            'name': 'کاور ضد ضربه iPhone 15 Pro',
            'name_en': 'iPhone 15 Pro Protective Case',
            'slug': 'iphone-15-pro-case',
            'brand': brands['apple'],
            'price': 850000,
            'original_price': 1200000,
            'stock': 80,
            'short_description': 'کاور ضد ضربه با محافظ دوربین',
            'description': 'کاور سیلیکونی ضد ضربه برای iPhone 15 Pro با محافظ لنز',
            'specifications': {
                'مدل': 'iPhone 15 Pro',
                'جنس': 'سیلیکون + TPU',
                'محافظت': 'Drop Protection 2m',
                'رنگ': 'مشکی, آبی, سبز, قرمز',
                'محافظ لنز': 'دارد'
            },
            'weight': 45,
        },
        {
            'name': 'کاور چرمی Samsung S24 Ultra',
            'name_en': 'Samsung S24 Ultra Leather Case',
            'slug': 'samsung-s24-ultra-leather',
            'brand': brands['samsung'],
            'price': 680000,
            'stock': 70,
            'short_description': 'کاور چرمی اورجینال سامسونگ',
            'description': 'کاور چرمی اصل سامسونگ برای Galaxy S24 Ultra',
            'specifications': {
                'مدل': 'Samsung Galaxy S24 Ultra',
                'جنس': 'چرم طبیعی',
                'رنگ': 'مشکی, قهوه‌ای, آبی',
                'سازگاری': 'Wireless Charging',
                'برند': 'اورجینال سامسونگ'
            },
            'weight': 35,
        },
        
        # Cables
        {
            'name': 'کابل USB-C به USB-C آنکر 2 متری',
            'name_en': 'Anker USB-C to USB-C Cable 2m',
            'slug': 'anker-usbc-cable-2m',
            'brand': brands['anker'],
            'price': 450000,
            'original_price': 600000,
            'stock': 100,
            'short_description': 'کابل USB-C با توان 100W',
            'description': 'کابل USB-C آنکر با پشتیبانی از شارژ سریع 100W و انتقال داده',
            'specifications': {
                'طول': '2 متر',
                'توان': '100W (5A)',
                'سرعت داده': '480Mbps',
                'جنس': 'نایلون بافته',
                'استاندارد': 'USB 2.0'
            },
            'weight': 55,
        },
        {
            'name': 'کابل Lightning اپل اورجینال 1 متری',
            'name_en': 'Apple Lightning Cable 1m Original',
            'slug': 'apple-lightning-1m',
            'brand': brands['apple'],
            'price': 980000,
            'stock': 120,
            'short_description': 'کابل لایتنینگ اورجینال اپل',
            'description': 'کابل Lightning اصل اپل با گارانتی اورجینال',
            'specifications': {
                'طول': '1 متر',
                'توان': '20W',
                'سازگاری': 'iPhone, iPad, AirPods',
                'جنس': 'TPE',
                'اورجینال': 'Apple Original'
            },
            'weight': 22,
        },
        
        # Screen Protectors
        {
            'name': 'گلس iPhone 15 Pro Max شفاف',
            'name_en': 'iPhone 15 Pro Max Tempered Glass',
            'slug': 'iphone-15-promax-glass',
            'brand': brands['apple'],
            'price': 320000,
            'original_price': 450000,
            'stock': 150,
            'short_description': 'محافظ صفحه شیشه‌ای 9H',
            'description': 'محافظ صفحه نمایش شیشه‌ای با سختی 9H و پوشش oleophobic',
            'specifications': {
                'مدل': 'iPhone 15 Pro Max',
                'جنس': 'Tempered Glass',
                'سختی': '9H',
                'ضخامت': '0.33mm',
                'پوشش': 'Oleophobic',
                'تعداد': '2 عددی'
            },
            'weight': 15,
        },
        
        # Wireless Chargers
        {
            'name': 'شارژر بی‌سیم آنکر 15W',
            'name_en': 'Anker 15W Wireless Charger',
            'slug': 'anker-wireless-15w',
            'brand': brands['anker'],
            'price': 1100000,
            'stock': 45,
            'short_description': 'شارژر بی‌سیم سریع 15 وات',
            'description': 'شارژر وایرلس Anker با قابلیت شارژ سریع 15W برای iPhone و Samsung',
            'specifications': {
                'توان': '15W Fast Charge',
                'سازگاری': 'iPhone, Samsung, Qi',
                'محافظت': 'Over-heat, Over-charge',
                'LED': 'نشانگر وضعیت',
                'کابل': 'USB-C 1.2m'
            },
            'weight': 95,
        },
        {
            'name': 'شارژر بی‌سیم سه‌تایی سامسونگ',
            'name_en': 'Samsung 3-in-1 Wireless Charger',
            'slug': 'samsung-3in1-wireless',
            'brand': brands['samsung'],
            'price': 2800000,
            'stock': 25,
            'short_description': 'شارژر سه تایی برای گوشی، واچ و ایرپاد',
            'description': 'ایستگاه شارژ بی‌سیم سامسونگ برای شارژ همزمان سه دستگاه',
            'specifications': {
                'توان': '15W + 5W + 5W',
                'تعداد پد': '3 پد',
                'سازگاری': 'Galaxy Phone, Watch, Buds',
                'فناوری': 'Qi Wireless',
                'رنگ': 'مشکی, سفید'
            },
            'weight': 185,
        },
    ]
    
    created_products = []
    for product_data in peripheral_products:
        product, created = Product.objects.get_or_create(
            slug=product_data['slug'],
            defaults={
                **product_data,
                'category': category,
                'product_type': Product.ProductType.PHYSICAL,
                'sub_type': Product.ProductSubType.ACCESSORY,
                'delivery_type': Product.DeliveryType.SHIPPING,
                'track_stock': True,
                'is_active': True,
            }
        )
        created_products.append(product)
        print(f"{'✅ Created' if created else '⚠️  Already exists'}: {product.name}")
    
    return created_products


def main():
    print("=" * 80)
    print("CREATING PHYSICAL PRODUCTS")
    print("=" * 80)
    
    # Create categories
    print("\n📁 Creating categories...")
    gaming_category, peripheral_category = create_categories()
    print(f"✅ Gaming Category: {gaming_category.name}")
    print(f"✅ Peripheral Category: {peripheral_category.name}")
    
    # Create brands
    print("\n🏷️  Creating brands...")
    brands = create_brands()
    print(f"✅ Created {len(brands)} brands")
    
    # Create gaming products
    print("\n🎮 Creating gaming products...")
    gaming_products = create_gaming_products(gaming_category, brands)
    print(f"✅ Total gaming products: {len(gaming_products)}")
    
    # Create peripheral products
    print("\n💻 Creating peripheral products...")
    peripheral_products = create_peripheral_products(peripheral_category, brands)
    print(f"✅ Total peripheral products: {len(peripheral_products)}")
    
    print("\n" + "=" * 80)
    print(f"✅ COMPLETED!")
    print(f"   Gaming Products: {len(gaming_products)}")
    print(f"   Peripheral Products: {len(peripheral_products)}")
    print(f"   Total: {len(gaming_products) + len(peripheral_products)}")
    print("=" * 80)


if __name__ == '__main__':
    main()
