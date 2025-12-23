"""
بانک‌های ایران با شماره BIN و لوگو
این فایل شامل اطلاعات کامل بانک‌های ایران برای تشخیص از روی 6 رقم اول شماره کارت است.
"""

IRANIAN_BANKS = {
    # بانک ملی ایران
    '603799': {
        'name': 'ملی',
        'full_name': 'بانک ملی ایران',
        'color': '#00629B',
        'logo': 'fa-landmark'
    },
    
    # بانک سپه
    '589210': {
        'name': 'سپه',
        'full_name': 'بانک سپه',
        'color': '#00A651',
        'logo': 'fa-university'
    },
    
    # بانک صنعت و معدن
    '627961': {
        'name': 'صنعت و معدن',
        'full_name': 'بانک صنعت و معدن',
        'color': '#00629B',
        'logo': 'fa-industry'
    },
    
    # بانک کشاورزی
    '603770': {
        'name': 'کشاورزی',
        'full_name': 'بانک کشاورزی',
        'color': '#00A651',
        'logo': 'fa-seedling'
    },
    '639217': {
        'name': 'کشاورزی',
        'full_name': 'بانک کشاورزی',
        'color': '#00A651',
        'logo': 'fa-seedling'
    },
    
    # بانک مسکن
    '628023': {
        'name': 'مسکن',
        'full_name': 'بانک مسکن',
        'color': '#FF7900',
        'logo': 'fa-home'
    },
    
    # بانک توسعه تعاون
    '502908': {
        'name': 'توسعه تعاون',
        'full_name': 'بانک توسعه تعاون',
        'color': '#009639',
        'logo': 'fa-handshake'
    },
    
    # بانک توسعه صادرات
    '627648': {
        'name': 'توسعه صادرات',
        'full_name': 'بانک توسعه صادرات ایران',
        'color': '#002D72',
        'logo': 'fa-ship'
    },
    '207177': {
        'name': 'توسعه صادرات',
        'full_name': 'بانک توسعه صادرات ایران',
        'color': '#002D72',
        'logo': 'fa-ship'
    },
    
    # پست بانک
    '627760': {
        'name': 'پست بانک',
        'full_name': 'پست بانک ایران',
        'color': '#F39200',
        'logo': 'fa-envelope'
    },
    
    # بانک توسعه اقتصاد نوین
    '627412': {
        'name': 'اقتصاد نوین',
        'full_name': 'بانک اقتصاد نوین',
        'color': '#6B2C91',
        'logo': 'fa-chart-line'
    },
    
    # بانک پارسیان
    '622106': {
        'name': 'پارسیان',
        'full_name': 'بانک پارسیان',
        'color': '#ED1B24',
        'logo': 'fa-credit-card'
    },
    '627884': {
        'name': 'پارسیان',
        'full_name': 'بانک پارسیان',
        'color': '#ED1B24',
        'logo': 'fa-credit-card'
    },
    '639347': {
        'name': 'پارسیان',
        'full_name': 'بانک پارسیان',
        'color': '#ED1B24',
        'logo': 'fa-credit-card'
    },
    
    # بانک پاسارگاد
    '502229': {
        'name': 'پاسارگاد',
        'full_name': 'بانک پاسارگاد',
        'color': '#FFCD00',
        'logo': 'fa-star'
    },
    '639347': {
        'name': 'پاسارگاد',
        'full_name': 'بانک پاسارگاد',
        'color': '#FFCD00',
        'logo': 'fa-star'
    },
    
    # بانک کارآفرین
    '627488': {
        'name': 'کارآفرین',
        'full_name': 'بانک کارآفرین',
        'color': '#00A651',
        'logo': 'fa-briefcase'
    },
    '502910': {
        'name': 'کارآفرین',
        'full_name': 'بانک کارآفرین',
        'color': '#00A651',
        'logo': 'fa-briefcase'
    },
    
    # بانک سامان
    '621986': {
        'name': 'سامان',
        'full_name': 'بانک سامان',
        'color': '#0066B3',
        'logo': 'fa-building'
    },
    
    # بانک سینا
    '639346': {
        'name': 'سینا',
        'full_name': 'بانک سینا',
        'color': '#8B1538',
        'logo': 'fa-university'
    },
    
    # بانک سرمایه
    '639607': {
        'name': 'سرمایه',
        'full_name': 'بانک سرمایه',
        'color': '#009639',
        'logo': 'fa-coins'
    },
    
    # بانک شهر
    '502806': {
        'name': 'شهر',
        'full_name': 'بانک شهر',
        'color': '#00A4E4',
        'logo': 'fa-city'
    },
    '504706': {
        'name': 'شهر',
        'full_name': 'بانک شهر',
        'color': '#00A4E4',
        'logo': 'fa-city'
    },
    
    # بانک دی
    '502938': {
        'name': 'دی',
        'full_name': 'بانک دی',
        'color': '#00629B',
        'logo': 'fa-calendar'
    },
    
    # بانک صادرات
    '603769': {
        'name': 'صادرات',
        'full_name': 'بانک صادرات ایران',
        'color': '#0066B3',
        'logo': 'fa-globe'
    },
    '903769': {
        'name': 'صادرات',
        'full_name': 'بانک صادرات ایران',
        'color': '#0066B3',
        'logo': 'fa-globe'
    },
    
    # بانک تجارت
    '627353': {
        'name': 'تجارت',
        'full_name': 'بانک تجارت',
        'color': '#002D72',
        'logo': 'fa-store'
    },
    '585983': {
        'name': 'تجارت',
        'full_name': 'بانک تجارت',
        'color': '#002D72',
        'logo': 'fa-store'
    },
    
    # بانک رفاه کارگران
    '589463': {
        'name': 'رفاه',
        'full_name': 'بانک رفاه کارگران',
        'color': '#00A651',
        'logo': 'fa-users'
    },
    
    # بانک ملت
    '610433': {
        'name': 'ملت',
        'full_name': 'بانک ملت',
        'color': '#ED1B24',
        'logo': 'fa-flag'
    },
    '991975': {
        'name': 'ملت',
        'full_name': 'بانک ملت',
        'color': '#ED1B24',
        'logo': 'fa-flag'
    },
    
    # بانک تات (موسسه اعتباری توسعه)
    '636214': {
        'name': 'تات',
        'full_name': 'موسسه اعتباری توسعه',
        'color': '#8B1538',
        'logo': 'fa-chart-bar'
    },
    
    # بانک قوامین
    '639599': {
        'name': 'قوامین',
        'full_name': 'بانک قوامین',
        'color': '#009639',
        'logo': 'fa-shield-alt'
    },
    
    # بانک انصار
    '627381': {
        'name': 'انصار',
        'full_name': 'بانک انصار',
        'color': '#00629B',
        'logo': 'fa-hands-helping'
    },
    
    # بانک مهر ایران
    '606373': {
        'name': 'مهر ایران',
        'full_name': 'بانک مهر ایران',
        'color': '#8B1538',
        'logo': 'fa-sun'
    },
    
    # بانک حکمت ایرانیان
    '636949': {
        'name': 'حکمت ایرانیان',
        'full_name': 'بانک حکمت ایرانیان',
        'color': '#6B2C91',
        'logo': 'fa-book'
    },
    
    # بانک خاورمیانه
    '585947': {
        'name': 'خاورمیانه',
        'full_name': 'بانک خاورمیانه',
        'color': '#002D72',
        'logo': 'fa-map'
    },
    
    # بانک آینده
    '636214': {
        'name': 'آینده',
        'full_name': 'بانک آینده',
        'color': '#00A4E4',
        'logo': 'fa-rocket'
    },
    
    # بانک گردشگری
    '505785': {
        'name': 'گردشگری',
        'full_name': 'بانک گردشگری',
        'color': '#00A651',
        'logo': 'fa-plane'
    },
    
    # بانک ایران زمین
    '505785': {
        'name': 'ایران زمین',
        'full_name': 'بانک ایران زمین',
        'color': '#8B1538',
        'logo': 'fa-mountain'
    },
    
    # بانک رسالت
    '504172': {
        'name': 'رسالت',
        'full_name': 'بانک رسالت',
        'color': '#009639',
        'logo': 'fa-mosque'
    },
    
    # موسسه اعتباری کوثر
    '505801': {
        'name': 'کوثر',
        'full_name': 'موسسه اعتباری کوثر',
        'color': '#6B2C91',
        'logo': 'fa-water'
    },
    
    # موسسه اعتباری ملل
    '606256': {
        'name': 'ملل',
        'full_name': 'موسسه اعتباری ملل',
        'color': '#002D72',
        'logo': 'fa-globe-americas'
    },
    
    # موسسه اعتباری نور
    '507677': {
        'name': 'نور',
        'full_name': 'موسسه اعتباری نور',
        'color': '#FFCD00',
        'logo': 'fa-lightbulb'
    },
    
    # بانک ایران ونزوئلا
    '505809': {
        'name': 'ایران ونزوئلا',
        'full_name': 'بانک مشترک ایران و ونزوئلا',
        'color': '#ED1B24',
        'logo': 'fa-handshake'
    },
}


def detect_bank_from_card_number(card_number):
    """
    تشخیص بانک از روی شماره کارت (6 رقم اول - BIN)
    
    Args:
        card_number (str): شماره کارت 16 رقمی
        
    Returns:
        dict: اطلاعات بانک یا None
    """
    if not card_number or len(card_number) < 6:
        return None
    
    # بررسی 6 رقم اول
    bin_code = card_number[:6]
    
    if bin_code in IRANIAN_BANKS:
        return IRANIAN_BANKS[bin_code]
    
    # اگر پیدا نشد، سعی کن با 4 رقم اول
    bin_code_4 = card_number[:4]
    
    # بعضی بانک‌ها فقط 4 رقم اول معتبره
    for key, value in IRANIAN_BANKS.items():
        if key.startswith(bin_code_4):
            return value
    
    return None


def get_bank_logo_html(bank_info, size='1.5em'):
    """
    ساخت HTML لوگوی بانک
    
    Args:
        bank_info (dict): اطلاعات بانک از detect_bank_from_card_number
        size (str): سایز آیکون
        
    Returns:
        str: HTML لوگوی بانک
    """
    if not bank_info:
        return '<i class="fas fa-university" style="font-size: 1.5em; color: #999;"></i>'
    
    return f'<i class="fas {bank_info["logo"]}" style="font-size: {size}; color: {bank_info["color"]};"></i>'


def get_bank_name_from_card(card_number):
    """
    دریافت نام بانک از روی شماره کارت
    
    Args:
        card_number (str): شماره کارت
        
    Returns:
        str: نام بانک یا "نامشخص"
    """
    bank_info = detect_bank_from_card_number(card_number)
    return bank_info['full_name'] if bank_info else 'بانک نامشخص'


def get_all_banks_list():
    """
    دریافت لیست تمام بانک‌های یکتا برای نمایش در select
    
    Returns:
        list: لیست تاپل (نام، نام کامل)
    """
    unique_banks = {}
    for bin_code, info in IRANIAN_BANKS.items():
        if info['name'] not in unique_banks:
            unique_banks[info['name']] = info['full_name']
    
    return sorted(unique_banks.items(), key=lambda x: x[1])
