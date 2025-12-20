"""
Product management models for Mini-up.
Handles virtual services, gaming products, accessories, and game currencies.
"""

from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
import uuid


class Category(models.Model):
    """
    Product categories - flat structure.
    Examples: Spotify, Gaming Headsets, PlayStation Plus
    """
    
    name = models.CharField(max_length=100, verbose_name='نام')
    name_en = models.CharField(max_length=100, blank=True, verbose_name='نام انگلیسی')
    slug = models.SlugField(max_length=120, unique=True, allow_unicode=True, verbose_name='اسلاگ')
    
    description = models.TextField(blank=True, verbose_name='توضیحات')
    image = models.ImageField(
        upload_to='categories/',
        null=True,
        blank=True,
        verbose_name='تصویر'
    )
    icon = models.CharField(max_length=50, blank=True, verbose_name='آیکون')  # Font Awesome class
    
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_featured = models.BooleanField(default=False, verbose_name='ویژه')
    
    sort_order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'sort_order']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_en or self.name, allow_unicode=True)
        super().save(*args, **kwargs)
    
    def get_active_products_count(self):
        """Get count of active products in this category."""
        return self.products.filter(is_active=True).count()
    
    def get_active_products(self):
        """Get all active products for this category."""
        return self.products.filter(is_active=True).select_related('brand').prefetch_related('images')


class Brand(models.Model):
    """Product brands for physical products."""
    
    name = models.CharField(max_length=100, verbose_name='نام')
    name_en = models.CharField(max_length=100, blank=True, verbose_name='نام انگلیسی')
    slug = models.SlugField(max_length=120, unique=True, allow_unicode=True, verbose_name='اسلاگ')
    
    logo = models.ImageField(
        upload_to='brands/',
        null=True,
        blank=True,
        verbose_name='لوگو'
    )
    description = models.TextField(blank=True, verbose_name='توضیحات')
    website = models.URLField(blank=True, verbose_name='وب‌سایت')
    
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = 'برند'
        verbose_name_plural = 'برندها'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_en or self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Base product model for all product types.
    Uses product_type to differentiate between virtual, physical, and game currency.
    """
    
    class ProductType(models.TextChoices):
        VIRTUAL = 'virtual', 'خدمات مجازی'
        PHYSICAL = 'physical', 'محصول فیزیکی'
        GAME_CURRENCY = 'game_currency', 'ارز بازی'
    
    class ProductSubType(models.TextChoices):
        # Physical sub-types
        ACCESSORY = 'accessory', 'محصولات جانبی'
        GAMING = 'gaming', 'محصولات گیمینگ'
        # Virtual sub-types
        VIRTUAL_SERVICE = 'virtual_service', 'خدمات مجازی'
        MINI_APP = 'mini_app', 'مینی اپ'
    
    class DeliveryType(models.TextChoices):
        INSTANT = 'instant', 'تحویل فوری (خودکار)'
        MANUAL = 'manual', 'تحویل دستی'
        SHIPPING = 'shipping', 'ارسال پستی'
    
    # Basic Info
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    sku = models.CharField(max_length=50, unique=True, blank=True, verbose_name='کد محصول')
    
    name = models.CharField(max_length=200, verbose_name='نام محصول')
    name_en = models.CharField(max_length=200, blank=True, verbose_name='نام انگلیسی')
    slug = models.SlugField(
        max_length=220,
        unique=True,
        allow_unicode=True,
        verbose_name='اسلاگ',
        help_text='شناسه یکتا و قابل خواندن برای URL؛ معمولاً از نام انگلیسی تولید می‌شود. از حروف، اعداد و خط تیره استفاده کنید.'
    )
    
    # Classification
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='دسته‌بندی'
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='برند'
    )
    
    product_type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.VIRTUAL,
        verbose_name='نوع محصول'
    )
    # Sub-type to distinguish the two flavors within virtual/physical groups
    sub_type = models.CharField(
        max_length=30,
        choices=ProductSubType.choices,
        null=True,
        blank=True,
        verbose_name='نوع',
        help_text='زیرنوع محصول را مشخص کنید تا در صفحات مجموعه‌بندی شود (مثال: محصولات جانبی، محصولات گیمینگ، خدمات مجازی، مینی اپ)'
    )
    delivery_type = models.CharField(
        max_length=20,
        choices=DeliveryType.choices,
        default=DeliveryType.INSTANT,
        verbose_name='نوع تحویل'
    )
    
    # Description
    short_description = models.CharField(max_length=500, blank=True, verbose_name='توضیح کوتاه')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    specifications = models.JSONField(default=dict, blank=True, verbose_name='مشخصات فنی')
    # attach help_text after field definition to avoid changing constructor signature in a large file
    specifications.help_text = (
        'فرمت JSON برای مشخصات فنی. مثال: {"وزن": "200g", "رنگ": "مشکی", "cpu": "Intel i5"}. '
        'برای محصولات مجازی می‌تواند شامل اطلاعاتی مثل {"duration": "1 ماه", "platform": "PC"} باشد.'
    )
    # Pricing
    price = models.PositiveIntegerField(verbose_name='قیمت (تومان)')
    original_price = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='قیمت اصلی (قبل از تخفیف)'
    )
    cost_price = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='قیمت تمام‌شده'
    )
    
    # Inventory (for physical products)
    stock = models.PositiveIntegerField(default=0, verbose_name='موجودی')
    low_stock_threshold = models.PositiveIntegerField(default=5, verbose_name='آستانه هشدار موجودی')
    track_stock = models.BooleanField(default=True, verbose_name='پیگیری موجودی')
    
    # Physical product details
    weight = models.PositiveIntegerField(null=True, blank=True, verbose_name='وزن (گرم)')
    dimensions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='ابعاد',
        help_text='{"length": 0, "width": 0, "height": 0}'
    )
    
    # Media
    main_image = models.ImageField(
        upload_to='products/%Y/%m/',
        verbose_name='تصویر اصلی'
    )
    
    # SEO
    meta_title = models.CharField(max_length=70, blank=True, verbose_name='عنوان متا')
    meta_description = models.CharField(max_length=160, blank=True, verbose_name='توضیحات متا')
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_featured = models.BooleanField(default=False, verbose_name='ویژه')
    is_new = models.BooleanField(default=True, verbose_name='جدید')
    is_bestseller = models.BooleanField(default=False, verbose_name='پرفروش')
    
    # Statistics
    view_count = models.PositiveIntegerField(default=0, verbose_name='تعداد بازدید')
    sales_count = models.PositiveIntegerField(default=0, verbose_name='تعداد فروش')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['product_type']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    # Template compatibility properties
    @property
    def image(self):
        """Alias for main_image to match template expectations."""
        return self.main_image
    
    @property
    def compare_price(self):
        """Alias for original_price to match template expectations."""
        return self.original_price
    
    @property
    def average_rating(self):
        """Calculate average rating from reviews."""
        from django.db.models import Avg
        result = self.reviews.filter(is_approved=True).aggregate(Avg('rating'))
        return result['rating__avg'] or 0
    
    @property
    def primary_image(self):
        """Alias for main_image for gaming_products template."""
        return self.main_image
    
    @property
    def discount_percent(self):
        """Alias for discount_percentage for gaming_products template."""
        return self.discount_percentage
    
    @property
    def final_price(self):
        """Return the final price after discount."""
        return self.price
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_en or self.name, allow_unicode=True)
        if not self.sku:
            self.sku = self._generate_sku()
        super().save(*args, **kwargs)
    
    def _generate_sku(self):
        """Generate unique SKU based on product type and category."""
        prefix_map = {
            'virtual': 'VRT',
            'physical': 'PHY',
            'game_currency': 'GMC',
        }
        prefix = prefix_map.get(self.product_type, 'PRD')
        unique_id = str(uuid.uuid4().hex)[:8].upper()
        return f'{prefix}-{unique_id}'
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage if original_price exists."""
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0
    
    @property
    def is_in_stock(self):
        """Check if product is in stock."""
        if not self.track_stock:
            return True
        return self.stock > 0
    
    @property
    def is_low_stock(self):
        """Check if stock is below threshold."""
        if not self.track_stock:
            return False
        return self.stock <= self.low_stock_threshold
    
    @property
    def is_digital(self):
        """Check if product is digital (virtual or game currency)."""
        return self.product_type in ['virtual', 'game_currency']
    
    @property
    def requires_shipping(self):
        """Check if product requires shipping."""
        return self.product_type == 'physical'
    
    def decrease_stock(self, quantity=1):
        """Decrease stock after purchase."""
        if self.track_stock and self.stock >= quantity:
            self.stock -= quantity
            self.save(update_fields=['stock'])
            return True
        return False
    
    def increase_stock(self, quantity=1):
        """Increase stock (e.g., after order cancellation)."""
        if self.track_stock:
            self.stock += quantity
            self.save(update_fields=['stock'])


class ProductImage(models.Model):
    """Additional images for products."""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='محصول'
    )
    image = models.ImageField(upload_to='products/%Y/%m/', verbose_name='تصویر')
    alt_text = models.CharField(max_length=200, blank=True, verbose_name='متن جایگزین')
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name='ترتیب')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = 'تصویر محصول'
        verbose_name_plural = 'تصاویر محصولات'
        ordering = ['sort_order']
    
    def __str__(self):
        return f'{self.product.name} - Image {self.pk}'


class ProductVariant(models.Model):
    """
    Product variants for different options (e.g., duration, size, color).
    Used for services with different durations or physical products with variants.
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name='محصول'
    )
    
    name = models.CharField(max_length=100, verbose_name='نام نوع')
    sku = models.CharField(max_length=50, unique=True, blank=True, verbose_name='کد نوع')
    
    # Variant attributes (JSON for flexibility)
    # e.g., {"duration": "1 month", "color": "black", "size": "XL"}
    attributes = models.JSONField(default=dict, verbose_name='ویژگی‌ها')
    
    price = models.PositiveIntegerField(verbose_name='قیمت (تومان)')
    original_price = models.PositiveIntegerField(null=True, blank=True, verbose_name='قیمت اصلی')
    
    stock = models.PositiveIntegerField(default=0, verbose_name='موجودی')
    
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name='ترتیب')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'نوع محصول'
        verbose_name_plural = 'انواع محصول'
        ordering = ['sort_order', 'price']
    
    def __str__(self):
        return f'{self.product.name} - {self.name}'
    
    def save(self, *args, **kwargs):
        if not self.sku:
            unique_id = str(uuid.uuid4().hex)[:6].upper()
            self.sku = f'{self.product.sku}-{unique_id}'
        super().save(*args, **kwargs)
    
    @property
    def discount_percentage(self):
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0


class DigitalInventory(models.Model):
    """
    Digital inventory for auto-delivery products.
    Stores codes, accounts, or credentials that are delivered automatically upon purchase.
    """
    
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'موجود'
        RESERVED = 'reserved', 'رزرو شده'
        SOLD = 'sold', 'فروخته شده'
        EXPIRED = 'expired', 'منقضی'
    
    class CredentialType(models.TextChoices):
        ACCOUNT = 'account', 'اکانت (یوزرنیم/پسورد)'
        CODE = 'code', 'کد فعال‌سازی'
        LICENSE = 'license', 'لایسنس'
        GIFT_CARD = 'gift_card', 'گیفت کارت'
        SUBSCRIPTION = 'subscription', 'اشتراک'
        LINK = 'link', 'لینک دانلود'
        CUSTOM = 'custom', 'سفارشی'
    # ═══════════════════════════════════════════════════════════════
    
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='digital_inventory',
        verbose_name='محصول'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='digital_inventory',
        verbose_name='نوع محصول'
    )
    
    # The actual digital content
    code = models.TextField(verbose_name='کد/اطلاعات')
    
    # For account-based products
    username = models.CharField(max_length=200, blank=True, verbose_name='نام کاربری')
    password = models.CharField(max_length=200, blank=True, verbose_name='رمز عبور')
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='اطلاعات اضافی',
        help_text='داده‌های اضافی مانند PIN، کلید فعال‌سازی و...'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        verbose_name='وضعیت'
    )
    
    # Tracking
    order_item = models.ForeignKey(
        'orders.OrderItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivered_inventory',
        verbose_name='آیتم سفارش'
    )
    sold_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ فروش')
    
    # Optional expiry
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ انقضا')
    
    # Batch tracking
    batch_id = models.CharField(max_length=50, blank=True, verbose_name='شناسه دسته')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'موجودی دیجیتال'
        verbose_name_plural = 'موجودی‌های دیجیتال'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f'{self.product.name} - {self.status}'
    
    @property
    def is_available(self):
        """Check if inventory item is available for sale."""
        from django.utils import timezone
        if self.status != self.Status.AVAILABLE:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True
    
    def reserve(self):
        """Reserve item for a purchase."""
        if self.is_available:
            self.status = self.Status.RESERVED
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False
    
    def mark_sold(self, order_item):
        """Mark item as sold and link to order."""
        from django.utils import timezone
        self.status = self.Status.SOLD
        self.order_item = order_item
        self.sold_at = timezone.now()
        self.save(update_fields=['status', 'order_item', 'sold_at', 'updated_at'])
    
    def release(self):
        """Release reserved item back to available."""
        if self.status == self.Status.RESERVED:
            self.status = self.Status.AVAILABLE
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False
    
    @classmethod
    def get_available_item(cls, product, variant=None):
        """Get one available inventory item for a product."""
        from django.utils import timezone
        
        queryset = cls.objects.filter(
            product=product,
            status=cls.Status.AVAILABLE
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        )
        
        if variant:
            queryset = queryset.filter(variant=variant)
        
        return queryset.first()
    
    @classmethod
    def get_available_count(cls, product, variant=None):
        """Get count of available inventory items."""
        from django.utils import timezone
        
        queryset = cls.objects.filter(
            product=product,
            status=cls.Status.AVAILABLE
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        )
        
        if variant:
            queryset = queryset.filter(variant=variant)
        
        return queryset.count()


class GameCurrencyRate(models.Model):
    """
    Dynamic pricing for game currencies based on amount.
    Allows different rates for different purchase amounts.
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='currency_rates',
        verbose_name='محصول'
    )
    
    # Amount range
    min_amount = models.PositiveIntegerField(verbose_name='حداقل مقدار')
    max_amount = models.PositiveIntegerField(null=True, blank=True, verbose_name='حداکثر مقدار')
    
    # Price per unit
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='قیمت هر واحد (تومان)'
    )
    
    # Unit info
    unit_name = models.CharField(
        max_length=50,
        default='واحد',
        verbose_name='نام واحد',
        help_text='مثال: UC، Diamond، V-Bucks'
    )
    
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'نرخ ارز بازی'
        verbose_name_plural = 'نرخ‌های ارز بازی'
        ordering = ['product', 'min_amount']
    
    def __str__(self):
        return f'{self.product.name} - {self.min_amount}+ {self.unit_name}'
    
    def calculate_price(self, amount):
        """Calculate total price for given amount."""
        return int(amount * float(self.price_per_unit))
    
    @classmethod
    def get_rate_for_amount(cls, product, amount):
        """Get appropriate rate for given amount."""
        return cls.objects.filter(
            product=product,
            min_amount__lte=amount,
            is_active=True
        ).filter(
            models.Q(max_amount__isnull=True) | models.Q(max_amount__gte=amount)
        ).order_by('-min_amount').first()


class ProductReview(models.Model):
    """Customer reviews for products."""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='محصول'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_reviews',
        verbose_name='کاربر'
    )
    
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='امتیاز'
    )
    title = models.CharField(max_length=200, blank=True, verbose_name='عنوان')
    comment = models.TextField(verbose_name='نظر')
    
    # Moderation
    is_approved = models.BooleanField(default=False, verbose_name='تایید شده')
    is_featured = models.BooleanField(default=False, verbose_name='ویژه')
    
    # Verification
    is_verified_purchase = models.BooleanField(default=False, verbose_name='خرید تایید شده')
    
    # Response from admin
    admin_response = models.TextField(blank=True, verbose_name='پاسخ مدیر')
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پاسخ')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'نظر محصول'
        verbose_name_plural = 'نظرات محصولات'
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # One review per user per product
    
    def __str__(self):
        return f'{self.user} - {self.product.name} ({self.rating}⭐)'


class ProductFAQ(models.Model):
    """Frequently asked questions for products."""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='faqs',
        verbose_name='محصول'
    )
    
    question = models.CharField(max_length=500, verbose_name='سوال')
    answer = models.TextField(verbose_name='پاسخ')
    
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name='ترتیب')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'سوال متداول محصول'
        verbose_name_plural = 'سوالات متداول محصولات'
        ordering = ['sort_order']
    
    def __str__(self):
        return f'{self.product.name} - {self.question[:50]}'


class Wishlist(models.Model):
    """User wishlist for products."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist',
        verbose_name='کاربر'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlisted_by',
        verbose_name='محصول'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ افزودن')
    
    class Meta:
        verbose_name = 'علاقه‌مندی'
        verbose_name_plural = 'علاقه‌مندی‌ها'
        unique_together = ['user', 'product']
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user} - {self.product.name}'


class RecentlyViewed(models.Model):
    """Track recently viewed products for users."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recently_viewed',
        verbose_name='کاربر'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='viewed_by',
        verbose_name='محصول'
    )
    
    viewed_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بازدید')
    view_count = models.PositiveIntegerField(default=1, verbose_name='تعداد بازدید')
    
    class Meta:
        verbose_name = 'بازدید اخیر'
        verbose_name_plural = 'بازدیدهای اخیر'
        unique_together = ['user', 'product']
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f'{self.user} viewed {self.product.name}'
    
    @classmethod
    @classmethod
    def record_view(cls, user, product, max_items=20):
        """Record a product view, limiting stored items per user."""
        if not user.is_authenticated:
            return None
        
        # Update or create the view record
        obj, created = cls.objects.update_or_create(
            user=user,
            product=product,
            defaults={}  # viewed_at auto-updates due to auto_now=True
        )
        
        # Increment view count separately (cleaner approach)
        if not created:
            cls.objects.filter(pk=obj.pk).update(view_count=models.F('view_count') + 1)
            obj.refresh_from_db()
        
        # Delete old records beyond max_items (single query)
        old_ids = list(
            cls.objects.filter(user=user)
            .order_by('-viewed_at')
            .values_list('id', flat=True)[max_items:]
        )
        if old_ids:
            cls.objects.filter(id__in=old_ids).delete()

        return obj

class ProductTag(models.Model):
    """برچسب محصولات برای دسته‌بندی و فیلتر"""
    
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='نام برچسب'
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        allow_unicode=True,
        verbose_name='اسلاگ'
    )
    color = models.CharField(
        max_length=7,
        default='#6366f1',
        verbose_name='رنگ',
        help_text='کد رنگ HEX مانند #6366f1'
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='آیکون',
        help_text='نام آیکون از Heroicons یا FontAwesome'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    priority = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='اولویت نمایش'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = 'برچسب'
        verbose_name_plural = 'برچسب‌ها'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('products:tag_detail', kwargs={'slug': self.slug})


class WishlistItem(models.Model):
    """
    آیتم‌های لیست علاقه‌مندی
    این مدل برای سازگاری با WishlistItemSerializer اضافه شده
    """
    
    wishlist = models.ForeignKey(
        'Wishlist',
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='لیست علاقه‌مندی'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
        verbose_name='محصول'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wishlist_items',
        verbose_name='نوع محصول'
    )
    
    note = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='یادداشت'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ افزودن')
    
    class Meta:
        verbose_name = 'آیتم علاقه‌مندی'
        verbose_name_plural = 'آیتم‌های علاقه‌مندی'
        unique_together = ['wishlist', 'product', 'variant']
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.wishlist.user} - {self.product.name}'