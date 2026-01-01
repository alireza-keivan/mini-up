# apps/orders/models.py

import uuid
import secrets
from decimal import Decimal
from django.db import models, transaction
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone


class Cart(models.Model):
    """
    Shopping cart for users.
    Authenticated users have persistent carts, guests use session-based carts.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart',
        verbose_name='کاربر'
    )
    
    # For guest users
    session_key = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        verbose_name='کلید نشست'
    )
    
    # Applied coupon
    applied_coupon_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='کد تخفیف اعمال شده'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'سبد خرید'
        verbose_name_plural = 'سبدهای خرید'
    
    def __str__(self):
        if self.user:
            return f'سبد خرید {self.user}'
        return f'سبد خرید مهمان ({self.session_key[:8]}...)'
    
    @property
    def total_items(self):
        """Get total number of items in cart."""
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    @property
    def subtotal(self):
        """Calculate subtotal before discounts."""
        total = Decimal('0')
        for item in self.items.select_related('product', 'variant'):
            total += item.line_total
        return total
    
    @property
    def total_discount(self):
        """Calculate total discount amount."""
        total = Decimal('0')
        for item in self.items.select_related('product', 'variant'):
            total += item.discount_amount
        return total
    
    @property
    def total(self):
        """Calculate final total."""
        return self.subtotal - self.total_discount
    
    def clear(self):
        """Remove all items from cart."""
        self.items.all().delete()
    
    def merge_with(self, other_cart):
        """
        Merge another cart into this one.
        Used when guest user logs in.
        """
        for item in other_cart.items.all():
            existing = self.items.filter(
                product=item.product,
                variant=item.variant
            ).first()
            
            if existing:
                existing.quantity += item.quantity
                existing.save()
            else:
                item.cart = self
                item.save()
        
        other_cart.delete()
    
    @classmethod
    def get_or_create_cart(cls, request):
        """Get or create cart for current user/session."""
        if request.user.is_authenticated:
            cart, created = cls.objects.get_or_create(user=request.user)
            
            # Merge session cart if exists
            session_key = request.session.session_key
            if session_key:
                try:
                    guest_cart = cls.objects.get(session_key=session_key, user__isnull=True)
                    cart.merge_with(guest_cart)
                except cls.DoesNotExist:
                    pass
            
            return cart
        else:
            if not request.session.session_key:
                request.session.create()
            
            cart, created = cls.objects.get_or_create(
                session_key=request.session.session_key,
                user__isnull=True
            )
            return cart


class CartItem(models.Model):
    """Individual items in shopping cart."""
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='سبد خرید'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='محصول'
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart_items',
        verbose_name='نوع محصول'
    )
    
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='تعداد'
    )
    
    # For game currency orders
    game_user_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='شناسه کاربری بازی'
    )
    currency_amount = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='مقدار ارز بازی'
    )
    
    # Custom order data for virtual services
    custom_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='داده‌های سفارشی سفارش',
        help_text='داده‌های فیلدهای سفارشی برای خدمات مجازی'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ افزودن')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'آیتم سبد خرید'
        verbose_name_plural = 'آیتم‌های سبد خرید'
        unique_together = ['cart', 'product', 'variant']
    
    def __str__(self):
        return f'{self.quantity}x {self.product.name}'
    
    @property
    def unit_price(self):
        """Get unit price from variant or product."""
        if self.variant:
            return Decimal(str(self.variant.price))
        return Decimal(str(self.product.price))
    
    @property
    def original_price(self):
        """Get original price before discount."""
        if self.variant and self.variant.original_price:
            return Decimal(str(self.variant.original_price))
        if self.product.original_price:
            return Decimal(str(self.product.original_price))
        return self.unit_price
    
    @property
    def line_total(self):
        """Calculate line total."""
        if self.currency_amount and self.product.product_type == 'game_currency':
            # For game currency, calculate based on rate
            from apps.products.models import GameCurrencyRate
            rate = GameCurrencyRate.get_rate_for_amount(self.product, self.currency_amount)
            if rate:
                return Decimal(str(rate.calculate_price(self.currency_amount)))
        
        return self.unit_price * self.quantity
    
    @property
    def discount_amount(self):
        """Calculate discount for this item."""
        if self.original_price > self.unit_price:
            return (self.original_price - self.unit_price) * self.quantity
        return Decimal('0')
    
    def is_available(self):
        """Check if item is still available for purchase."""
        if not self.product.is_active:
            return False
        
        if self.product.product_type == 'virtual':
            # Check digital inventory
            from apps.products.models import DigitalInventory
            available = DigitalInventory.get_available_count(
                self.product, 
                self.variant
            )
            return available >= self.quantity
        
        if self.variant:
            return self.variant.stock >= self.quantity
        
        return self.product.stock >= self.quantity


class Order(models.Model):
    """
    Main order model containing all order information.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار پرداخت'
        PROCESSING = 'processing', 'در حال پردازش'
        CONFIRMED = 'confirmed', 'تایید شده'
        PREPARING = 'preparing', 'در حال آماده‌سازی'
        SHIPPED = 'shipped', 'ارسال شده'
        DELIVERED = 'delivered', 'تحویل داده شده'
        COMPLETED = 'completed', 'تکمیل شده'
        CANCELLED = 'cancelled', 'لغو شده'
        REFUNDED = 'refunded', 'مسترد شده'
        FAILED = 'failed', 'ناموفق'
    
    class PaymentMethod(models.TextChoices):
        ZARINPAL = 'zarinpal', 'زرین‌پال'
        IDPAY = 'idpay', 'آیدی‌پی'
        WALLET = 'wallet', 'کیف پول'
        MIXED = 'mixed', 'ترکیبی'  # Wallet + Gateway
    
    # Order identification
    order_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name='شماره سفارش'
    )
    tracking_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='کد پیگیری'
    )
    
    # Customer
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='کاربر'
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='وضعیت'
    )
    
    # Payment info
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True,
        verbose_name='روش پرداخت'
    )
    
    # Pricing
    subtotal = models.PositiveIntegerField(
        default=0,
        verbose_name='جمع کل'
    )
    discount_amount = models.PositiveIntegerField(
        default=0,
        verbose_name='تخفیف محصولات'
    )
    coupon_discount = models.PositiveIntegerField(
        default=0,
        verbose_name='تخفیف کوپن'
    )
    shipping_cost = models.PositiveIntegerField(
        default=0,
        verbose_name='هزینه ارسال'
    )
    wallet_used = models.PositiveIntegerField(
        default=0,
        verbose_name='پرداخت از کیف پول'
    )
    total = models.PositiveIntegerField(
        default=0,
        verbose_name='مبلغ نهایی'
    )
    amount_payable = models.PositiveIntegerField(
        default=0,
        verbose_name='مبلغ قابل پرداخت',
        help_text='مبلغ نهایی پس از کسر کیف پول'
    )
    
    # Coupon
    coupon = models.ForeignKey(
        'coupons.Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='کوپن'
    )
    
    # Shipping address (for physical products)
    shipping_address = models.ForeignKey(
        'accounts.Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='آدرس ارسال'
    )
    
    # Shipping details snapshot (in case address is modified later)
    shipping_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='اطلاعات ارسال'
    )
    
    # Order notes
    customer_note = models.TextField(
        blank=True,
        verbose_name='یادداشت مشتری'
    )
    admin_note = models.TextField(
        blank=True,
        verbose_name='یادداشت ادمین'
    )
    
    # Tracking
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='آدرس IP'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پرداخت')
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ ارسال')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تحویل')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تکمیل')
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ لغو')
    
    # Expiry for pending orders
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='انقضای سفارش'
    )
    
    class Meta:
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارشات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f'سفارش {self.order_number}'
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        if not self.tracking_code:
            self.tracking_code = self._generate_tracking_code()
        super().save(*args, **kwargs)
    
    def _generate_order_number(self):
        """Generate unique order number: YYYYMMDD-XXXXX"""
        from django.utils import timezone
        import random
        
        date_part = timezone.now().strftime('%Y%m%d')
        
        for _ in range(10):  # Try up to 10 times
            random_part = ''.join([str(random.randint(0, 9)) for _ in range(5)])
            order_number = f'{date_part}-{random_part}'
            
            if not Order.objects.filter(order_number=order_number).exists():
                return order_number
        
        # Fallback with UUID
                # Fallback with UUID
        return f'{date_part}-{uuid.uuid4().hex[:5].upper()}'

    def _generate_tracking_code(self):
        """Generate a random unique tracking code."""
        code = secrets.token_hex(8).upper()
        while Order.objects.filter(tracking_code=code).exists():
            code = secrets.token_hex(8).upper()
        return code

    @property
    def is_paid(self):
        return self.status in {
            self.Status.CONFIRMED,
            self.Status.PROCESSING,
            self.Status.PREPARING,
            self.Status.SHIPPED,
            self.Status.DELIVERED,
            self.Status.COMPLETED
        }

    @property
    def is_completed(self):
        return self.status == self.Status.COMPLETED

    @property
    def is_cancelled(self):
        return self.status in {self.Status.CANCELLED, self.Status.REFUNDED}

    def mark_paid(self):
        """Mark order as paid after successful gateway callback."""
        if not self.is_paid:
            self.status = self.Status.CONFIRMED
            self.paid_at = timezone.now()
            self.save(update_fields=['status', 'paid_at', 'updated_at'])

    def mark_cancelled(self, reason=None):
        """Cancel order with optional admin note."""
        self.status = self.Status.CANCELLED
        self.cancelled_at = timezone.now()
        if reason:
            self.admin_note += f'\n[لغو] {reason}'
        self.save(update_fields=['status', 'cancelled_at', 'admin_note', 'updated_at'])

    def mark_completed(self):
        """Mark order as fully completed."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

    def capture_inventory(self):
        """
        Reserve / sell digital inventory items.
        Called after payment is confirmed.
        """
        from apps.products.models import DigitalInventory

        for item in self.items.all():
            if item.product.product_type == 'virtual':
                # For digital auto delivery
                available_items = list(
                    DigitalInventory.objects.filter(
                        product=item.product,
                        variant=item.variant,
                        status=DigitalInventory.Status.AVAILABLE
                    )[:item.quantity]
                )

                if len(available_items) < item.quantity:
                    raise ValueError('Not enough digital inventory items')

                for inv in available_items:
                    inv.mark_sold(order_item=item)

            else:
                # Reduce stock for normal items
                if item.variant:
                    item.variant.stock -= item.quantity
                    item.variant.save()
                else:
                    item.product.stock -= item.quantity
                    item.product.save()

    def snapshot_shipping_address(self):
        """Capture the shipping address at the time of purchase."""
        if not self.shipping_address:
            return

        self.shipping_data = {
            'full_name': self.shipping_address.full_name,
            'phone': self.shipping_address.phone,
            'state': self.shipping_address.state,
            'city': self.shipping_address.city,
            'address': self.shipping_address.address,
            'postal_code': self.shipping_address.postal_code
        }
        self.save(update_fields=['shipping_data', 'updated_at'])
        
class OrderItem(models.Model):
    """Item of an order."""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='سفارش'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='محصول'
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='order_items',
        verbose_name='نوع محصول'
    )

    quantity = models.PositiveIntegerField(default=1, verbose_name='تعداد')

    unit_price = models.PositiveIntegerField(verbose_name='قیمت واحد')
    original_price = models.PositiveIntegerField(verbose_name='قیمت اصلی')
    total_price = models.PositiveIntegerField(verbose_name='قیمت کل')
    discount_amount = models.PositiveIntegerField(default=0, verbose_name='تخفیف')

    # Game currency fields
    currency_amount = models.PositiveIntegerField(null=True, blank=True, verbose_name='مقدار ارز')
    game_user_id = models.CharField(max_length=100, blank=True, verbose_name='شناسه بازی')

    # Digital delivery details (auto filled)
    delivery_data = models.JSONField(default=dict, blank=True, verbose_name='اطلاعات تحویل')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'آیتم سفارش'
        verbose_name_plural = 'آیتم‌های سفارش'

    def __str__(self):
        return f'{self.quantity}x {self.product.name}'

    def bind_inventory(self):
        """
        Bind assigned DigitalInventory items to item.delivery_data
        """
        from apps.products.models import DigitalInventory

        inv_items = DigitalInventory.objects.filter(order_item=self)
        if not inv_items.exists():
            return

        delivery_list = []
        for inv in inv_items:
            delivery_list.append({
                'code': inv.code,
                'username': inv.username,
                'password': inv.password,
                'extra_data': inv.extra_data
            })

        self.delivery_data = {
            'items': delivery_list,
            'count': len(delivery_list)
        }
        self.save(update_fields=['delivery_data'])

class OrderStatusHistory(models.Model):
    """
    تاریخچه تغییر وضعیت سفارش
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='سفارش'
    )
    old_status = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='وضعیت قبلی'
    )
    new_status = models.CharField(
        max_length=20,
        verbose_name='وضعیت جدید'
    )
    note = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='تغییر توسط'
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ تغییر'
    )

    class Meta:
        verbose_name = 'تاریخچه وضعیت'
        verbose_name_plural = 'تاریخچه وضعیت‌ها'
        ordering = ['-changed_at']

    def __str__(self):
        return f'{self.order.order_number}: {self.old_status} → {self.new_status}'