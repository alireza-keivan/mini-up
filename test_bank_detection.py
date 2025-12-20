#!/usr/bin/env python
"""
اسکریپت تست تشخیص بانک از روی شماره کارت
می‌توانید این فایل را مستقیم اجرا کنید بدون نیاز به Django shell
"""

import sys
import os

# اضافه کردن مسیر پروژه به PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import تابع تشخیص بانک
from apps.accounts.bank_utils import (
    detect_bank_from_card_number,
    get_bank_name_from_card,
    IRANIAN_BANKS
)


def test_bank_detection():
    """تست تشخیص بانک‌های مختلف"""
    
    print("=" * 60)
    print("🧪 تست تشخیص بانک از روی شماره کارت")
    print("=" * 60)
    print()
    
    # شماره کارت‌های تست
    test_cards = [
        ('6037997878123456', 'بانک ملی ایران'),
        ('6104331234567890', 'بانک ملت'),
        ('6273531234567890', 'بانک تجارت'),
        ('6037691234567890', 'بانک صادرات'),
        ('5892101234567890', 'بانک سپه'),
        ('6219861234567890', 'بانک سامان'),
        ('6221061234567890', 'بانک پارسیان'),
        ('5022291234567890', 'بانک پاسارگاد'),
        ('6274881234567890', 'بانک کارآفرین'),
        ('6037701234567890', 'بانک کشاورزی'),
        ('6280231234567890', 'بانک مسکن'),
        ('6277601234567890', 'پست بانک'),
        ('1234567890123456', 'کارت نامعتبر'),
    ]
    
    success_count = 0
    
    for card_number, expected_bank in test_cards:
        bank_info = detect_bank_from_card_number(card_number)
        
        if bank_info:
            detected_name = bank_info['full_name']
            status = "✅" if expected_bank != 'کارت نامعتبر' else "⚠️"
            success_count += 1
            
            print(f"{status} {card_number[:6]}******{card_number[-4:]}")
            print(f"   📍 {detected_name}")
            print(f"   🎨 رنگ: {bank_info['color']}")
            print(f"   🏛️  آیکون: {bank_info['logo']}")
        else:
            status = "❌" if expected_bank != 'کارت نامعتبر' else "✅"
            print(f"{status} {card_number[:6]}******{card_number[-4:]}")
            print(f"   📍 بانک تشخیص داده نشد (انتظار: {expected_bank})")
        
        print()
    
    print("=" * 60)
    print(f"نتیجه: {success_count}/{len([c for c in test_cards if c[1] != 'کارت نامعتبر'])} بانک با موفقیت تشخیص داده شد")
    print("=" * 60)


def show_all_banks():
    """نمایش تمام بانک‌های پشتیبانی شده"""
    
    print("\n" + "=" * 60)
    print("📋 لیست کامل بانک‌های پشتیبانی شده")
    print("=" * 60)
    print()
    
    # گروه‌بندی بانک‌ها بر اساس نام
    unique_banks = {}
    for bin_code, info in IRANIAN_BANKS.items():
        if info['full_name'] not in unique_banks:
            unique_banks[info['full_name']] = {
                'bins': [bin_code],
                'info': info
            }
        else:
            unique_banks[info['full_name']]['bins'].append(bin_code)
    
    # مرتب‌سازی بر اساس نام
    sorted_banks = sorted(unique_banks.items())
    
    for idx, (full_name, data) in enumerate(sorted_banks, 1):
        info = data['info']
        bins = ', '.join(data['bins'])
        
        print(f"{idx:2d}. {full_name}")
        print(f"    🔢 BIN: {bins}")
        print(f"    🎨 رنگ: {info['color']}")
        print(f"    🏛️  آیکون: {info['logo']}")
        print()
    
    print(f"💡 جمع کل: {len(sorted_banks)} بانک با {len(IRANIAN_BANKS)} BIN code")
    print("=" * 60)


def interactive_test():
    """تست تعاملی - کاربر شماره کارت وارد می‌کند"""
    
    print("\n" + "=" * 60)
    print("🔍 تست تعاملی - تشخیص بانک")
    print("=" * 60)
    print()
    print("شماره کارت 16 رقمی خود را وارد کنید (یا 'q' برای خروج):")
    
    while True:
        card_number = input("\n💳 شماره کارت: ").strip()
        
        if card_number.lower() == 'q':
            print("👋 خروج از برنامه")
            break
        
        # حذف فاصله‌ها و خط تیره‌ها
        card_number = card_number.replace(' ', '').replace('-', '')
        
        # اعتبارسنجی
        if not card_number.isdigit():
            print("❌ خطا: فقط اعداد مجاز است")
            continue
        
        if len(card_number) != 16:
            print(f"❌ خطا: شماره کارت باید 16 رقم باشد (شما {len(card_number)} رقم وارد کردید)")
            continue
        
        # تشخیص بانک
        bank_info = detect_bank_from_card_number(card_number)
        
        print()
        print("-" * 40)
        
        if bank_info:
            print(f"✅ بانک تشخیص داده شد!")
            print(f"🏛️  نام بانک: {bank_info['full_name']}")
            print(f"📛 نام کوتاه: {bank_info['name']}")
            print(f"🎨 رنگ برند: {bank_info['color']}")
            print(f"🏛️  آیکون: {bank_info['logo']}")
            print(f"🔢 BIN: {card_number[:6]}")
            print(f"💳 شماره ماسک شده: {card_number[:4]}-{card_number[4:6]}**-****-{card_number[-4:]}")
        else:
            print(f"❌ بانک تشخیص داده نشد")
            print(f"🔢 BIN: {card_number[:6]}")
            print(f"💡 این کارت ممکن است:")
            print(f"   - از بانک خارجی باشد")
            print(f"   - BIN code جدیدی باشد که در دیتابیس نیست")
            print(f"   - شماره کارت نامعتبر باشد")
        
        print("-" * 40)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='تست تشخیص بانک از روی شماره کارت')
    parser.add_argument('--all', action='store_true', help='نمایش تمام بانک‌های پشتیبانی شده')
    parser.add_argument('--interactive', action='store_true', help='حالت تعاملی')
    parser.add_argument('--card', type=str, help='تست یک شماره کارت خاص')
    
    args = parser.parse_args()
    
    if args.all:
        show_all_banks()
    elif args.interactive:
        interactive_test()
    elif args.card:
        card_number = args.card.replace(' ', '').replace('-', '')
        bank_info = detect_bank_from_card_number(card_number)
        
        if bank_info:
            print(f"✅ {bank_info['full_name']}")
            print(f"   رنگ: {bank_info['color']}")
            print(f"   آیکون: {bank_info['logo']}")
        else:
            print("❌ بانک تشخیص داده نشد")
    else:
        # حالت پیش‌فرض: تست خودکار
        test_bank_detection()
        show_all_banks()
        
        print("\n💡 برای تست تعاملی:")
        print("   python test_bank_detection.py --interactive")
        print("\n💡 برای تست یک کارت خاص:")
        print("   python test_bank_detection.py --card 6037997878123456")
