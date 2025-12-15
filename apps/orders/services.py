# apps/orders/services.py

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory
import timedelta ############## MAYBE WRONG

# ═══════════════════════════════════════════════════════════════════════════════
# CART SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class CartService:
    """
    سرویس مدیریت سبد خرید
    """

    @staticmethod
    def get_cart(request):
        """دریافت یا ایجاد سبد خرید"""
        return Cart.get_or_create_cart(request)

    @staticmethod
    @transaction.atomic
    def add_item(cart, product, variant=None, quantity=1, game_user_id='', currency_amount=None):
        """
        افزودن آیتم به سبد خرید
        
        Args:
            cart: سبد خرید
            product: محصول
            variant: واریانت (اختیاری)
            quantity: تعداد
            game_user_id: شناسه بازی (برای ارز بازی)
            currency_amount: مقدار ارز بازی
        
        Returns:
            CartItem
        """
        # بررسی فعال بودن محصول
        if not product.is_active:
            raise ValidationError('این محصول در حال حاضر قابل خرید نیست.')

        # بررسی موجودی
        if product.product_type != 'virtual':
            stock = variant.stock if variant else product.stock
            if stock < quantity:
                raise ValidationError(f'موجودی کافی نیست. موجودی فعلی: {stock}')

        # بررسی آیتم تکراری
        existing = cart.items.filter(product=product, variant=variant).first()

        if existing:
            new_quantity = existing.quantity + quantity
            
            # بررسی موجودی برای مجموع
            if product.product_type != 'virtual':
                stock = variant.stock if variant else product.stock
                if stock < new_quantity:
                    raise ValidationError(f'موجودی کافی نیست. حداکثر قابل سفارش: {stock}')
            
            existing.quantity = new_quantity
            existing.save()
            return existing

        # ایجاد آیتم جدید
        item = CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variant,
            quantity=quantity,
            game_user_id=game_user_id,
            currency_amount=currency_amount
        )

        return item

    @staticmethod
    @transaction.atomic
    def update_item_quantity(cart_item, quantity):
        """بروزرسانی تعداد آیتم"""
        if quantity < 1:
            raise ValidationError('تعداد باید حداقل ۱ باشد.')

        product = cart_item.product
        variant = cart_item.variant

        # بررسی موجودی
        if product.product_type != 'virtual':
            stock = variant.stock if variant else product.stock
            if stock < quantity:
                raise ValidationError(f'موجودی کافی نیست. حداکثر قابل سفارش: {stock}')

        cart_item.quantity = quantity
        cart_item.save()
        return cart_item

    @staticmethod
    @transaction.atomic
    def remove_item(cart_item):
        """حذف آیتم از سبد"""
        cart_item.delete()

    @staticmethod
    @transaction.atomic
    def clear_cart(cart):
        """خالی کردن سبد"""
        cart.clear()

    @staticmethod
    def validate_cart_items(cart):
        """
        بررسی اعتبار تمام آیتم‌های سبد
        
        Returns:
            tuple: (valid_items, invalid_items)
        """
        valid = []
        invalid = []

        for item in cart.items.select_related('product', 'variant'):
            if item.is_available():
                valid.append(item)
            else:
                invalid.append({
                    'item': item,
                    'reason': 'موجودی کافی نیست یا محصول غیرفعال شده است.'
                })

        return valid, invalid


# ═══════════════════════════════════════════════════════════════════════════════
# ORDER SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class OrderService:
    """
    سرویس مدیریت سفارشات
    """

    # ─────────────────────────────────────────────────────────────────────────
    # CREATE ORDER
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_order_from_cart(
        user,
        cart,
        shipping_address=None,
        coupon=None,
        use_wallet=False,
        wallet_amount=0,
        payment_method='zarinpal',
        customer_note='',
        ip_address=None,
        user_agent=''
    ):
        """
        ایجاد سفارش از سبد خرید
        
        Args:
            user: کاربر
            cart: سبد خرید
            shipping_address: آدرس ارسال (اختیاری)
            coupon: کوپن تخفیف (اختیاری)
            use_wallet: استفاده از کیف پول
            wallet_amount: مبلغ کیف پول
            payment_method: روش پرداخت
            customer_note: یادداشت مشتری
            ip_address: آی‌پی کاربر
            user_agent: User Agent
            
        Returns:
            Order instance
            
        Raises:
            ValidationError: در صورت خطا
        """
        # بررسی خالی نبودن سبد
        if not cart.items.exists():
            raise ValidationError('سبد خرید شما خالی است.')

        # اعتبارسنجی آیتم‌ها
        valid_items, invalid_items = CartService.validate_cart_items(cart)
        
        if invalid_items:
            item_names = [item['item'].product.name for item in invalid_items]
            raise ValidationError(
                f'برخی محصولات قابل سفارش نیستند: {", ".join(item_names)}'
            )

        # محاسبه مبالغ
        subtotal = cart.subtotal
        discount_amount = cart.total_discount
        
        # محاسبه تخفیف کوپن
        coupon_discount = Decimal('0')
        if coupon:
            coupon_discount = OrderService._calculate_coupon_discount(coupon, subtotal)
        
        # محاسبه هزینه ارسال
        shipping_cost = OrderService._calculate_shipping_cost(cart, shipping_address)
        
        # محاسبه جمع کل
        total = subtotal - discount_amount - coupon_discount + shipping_cost
        
        # اعتبارسنجی کیف پول
        actual_wallet_amount = Decimal('0')
        if use_wallet and wallet_amount > 0:
            actual_wallet_amount = OrderService._validate_wallet_usage(
                user, wallet_amount, total
            )
        
        # مبلغ قابل پرداخت
        amount_payable = total - actual_wallet_amount
        
        # ساخت شماره سفارش
        order_number = Order.generate_order_number()
        tracking_code = Order.generate_tracking_code()
        
        # آماده‌سازی دیتای آدرس
        shipping_data = None
        if shipping_address:
            shipping_data = {
                'full_name': shipping_address.full_name,
                'phone': shipping_address.phone,
                'province': shipping_address.province,
                'city': shipping_address.city,
                'address': shipping_address.address,
                'postal_code': shipping_address.postal_code,
            }
        
        # ایجاد سفارش
        order = Order.objects.create(
            user=user,
            order_number=order_number,
            tracking_code=tracking_code,
            status=Order.Status.PENDING,
            payment_method=payment_method,
            subtotal=subtotal,
            discount_amount=discount_amount,
            coupon=coupon,
            coupon_discount=coupon_discount,
            shipping_cost=shipping_cost,
            wallet_used=actual_wallet_amount,
            total=total,
            amount_payable=amount_payable,
            shipping_address=shipping_address,
            shipping_data=shipping_data,
            customer_note=customer_note,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else '',
            expires_at=timezone.now() + timedelta(hours=1)  # ۱ ساعت فرصت پرداخت
        )
        
        # ایجاد آیتم‌های سفارش
        for cart_item in valid_items:
            OrderService._create_order_item(order, cart_item)
        
        # ⚠️ IMPORTANT: کوپن در اینجا علامت‌گذاری نمی‌شود!
        # کوپن فقط باید پس از پرداخت موفق علامت‌گذاری شود (در confirm_payment)
        # چون کاربر ممکن است سفارش را ایجاد کند ولی پرداخت نکند
        
        # ثبت تاریخچه وضعیت
        OrderStatusHistory.objects.create(
            order=order,
            old_status='',
            new_status=Order.Status.PENDING,
            note='سفارش ایجاد شد'
        )
        
        return order

    @staticmethod
    def _calculate_coupon_discount(coupon, subtotal):
        """محاسبه تخفیف کوپن"""
        if coupon.discount_type == 'percentage':
            discount = (subtotal * coupon.discount_value) / 100
            if coupon.max_discount:
                discount = min(discount, coupon.max_discount)
        else:
            discount = coupon.discount_value
        
        return min(discount, subtotal)

    @staticmethod
    def _calculate_shipping_cost(cart, shipping_address):
        """محاسبه هزینه ارسال"""
        from django.conf import settings
        
        # بررسی محصولات فیزیکی
        has_physical = any(
            item.product.product_type == 'physical' 
            for item in cart.items.select_related('product')
        )
        
        if not has_physical:
            return Decimal('0')
        
        # هزینه ارسال ثابت
        shipping_rate = Decimal(getattr(settings, 'FLAT_SHIPPING_RATE', 50000))
        free_threshold = Decimal(getattr(settings, 'FREE_SHIPPING_THRESHOLD', 500000))
        
        # ارسال رایگان برای سفارشات بالای حد معین
        if cart.subtotal >= free_threshold:
            return Decimal('0')
        
        return shipping_rate

    @staticmethod
    def _validate_wallet_usage(user, requested_amount, total):
        """اعتبارسنجی استفاده از کیف پول"""
        wallet = getattr(user, 'wallet', None)
        
        if not wallet:
            raise ValidationError('کیف پول شما فعال نیست.')
        
        available_balance = wallet.available_balance
        
        if requested_amount > available_balance:
            raise ValidationError(
                f'موجودی کیف پول کافی نیست. موجودی: {available_balance:,} تومان'
            )
        
        # حداکثر استفاده برابر با کل سفارش
        return min(Decimal(str(requested_amount)), total)

    @staticmethod
    def _create_order_item(order, cart_item):
        """ایجاد آیتم سفارش از آیتم سبد"""
        product = cart_item.product
        variant = cart_item.variant
        
        # قیمت فعلی
        if variant:
            unit_price = variant.price
            original_price = variant.original_price or variant.price
        else:
            unit_price = product.price
            original_price = product.original_price or product.price
        
        quantity = cart_item.quantity
        total_price = unit_price * quantity
        discount = (original_price - unit_price) * quantity
        
        # Snapshot از محصول
        product_snapshot = {
            'name': product.name,
            'slug': product.slug,
            'sku': product.sku,
            'product_type': product.product_type,
        }
        
        if variant:
            product_snapshot['variant_name'] = variant.name
            product_snapshot['variant_sku'] = variant.sku
        
        return OrderItem.objects.create(
            order=order,
            product=product,
            variant=variant,
            quantity=quantity,
            unit_price=unit_price,
            original_price=original_price,
            total_price=total_price,
            discount_amount=discount,
            product_snapshot=product_snapshot,
            game_user_id=cart_item.game_user_id,
            currency_amount=cart_item.currency_amount
        )

    @staticmethod
    def _mark_coupon_used(coupon, user, order):
        """
        ثبت استفاده از کوپن (فقط اگر قبلاً ثبت نشده باشد)
        
        این متد فقط باید پس از پرداخت موفق فراخوانی شود.
        اگر کاربر سفارش را ایجاد کند ولی پرداخت نکند، کوپن نباید مصرف شود.
        """
        from apps.coupons.models import CouponUsage
        
        # بررسی اینکه آیا این کوپن قبلاً برای این سفارش ثبت شده
        existing_usage = CouponUsage.objects.filter(
            coupon=coupon,
            user=user,
            order=order
        ).exists()
        
        if existing_usage:
            # کوپن قبلاً برای این سفارش ثبت شده (احتمالاً در نسخه قدیمی کد)
            return
        
        # ثبت استفاده جدید
        CouponUsage.objects.create(
            coupon=coupon,
            user=user,
            order=order,
            discount_amount=order.coupon_discount
        )
        
        # افزایش شمارنده استفاده
        coupon.used_count += 1
        coupon.save(update_fields=['used_count'])

    # ─────────────────────────────────────────────────────────────────────────
    # PAYMENT CONFIRMATION
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def confirm_payment(order, ref_id, card_pan=''):
        """
        تأیید پرداخت موفق
        
        Args:
            order: سفارش
            ref_id: کد پیگیری بانک
            card_pan: شماره کارت (اختیاری)
        """
        if order.status != Order.Status.PENDING:
            raise ValidationError('این سفارش قبلاً پرداخت شده است.')
        
        old_status = order.status
        now = timezone.now()
        
        # بروزرسانی سفارش
        order.status = Order.Status.PROCESSING  # تغییر به processing بعد از پرداخت موفق
        order.paid_at = now
        order.payment_ref_id = ref_id
        order.payment_card_pan = card_pan
        order.save(update_fields=[
            'status', 'paid_at', 'payment_ref_id', 'payment_card_pan'
        ])
        
        # ✅ اینجا است که کوپن باید علامت‌گذاری شود (فقط پس از پرداخت موفق)
        if order.coupon:
            OrderService._mark_coupon_used(order.coupon, order.user, order)
        
        # کسر از کیف پول
        if order.wallet_used > 0:
            OrderService._deduct_wallet(order)
        
        # کسر از موجودی (برای محصولات فیزیکی)
        OrderService._capture_inventory(order)
        
        # خالی کردن سبد خرید
        if order.user:
            Cart.objects.filter(user=order.user).delete()
        
        # ثبت تاریخچه
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=Order.Status.PROCESSING,
            note='پرداخت با موفقیت انجام شد'
        )

        return order

    @staticmethod
    def _deduct_wallet(order):
        """کسر مبلغ استفاده‌شده از کیف پول"""
        wallet = getattr(order.user, 'wallet', None)
        if not wallet:
            return
        
        wallet.withdraw(
            amount=order.wallet_used,
            description=f'استفاده از کیف پول برای سفارش {order.order_number}',
            related_order=order
        )

    @staticmethod
    def _capture_inventory(order):
        """کسر موجودی کالاهای فیزیکی پس از پرداخت موفق"""
        for item in order.items.select_related('product', 'variant'):
            product = item.product
            variant = item.variant
            
            if product.product_type == 'virtual':
                continue
            
            qty = item.quantity
            
            if variant:
                if variant.stock < qty:
                    raise ValidationError(
                        f'موجودی واریانت {variant.name} کافی نیست.'
                    )
                variant.stock -= qty
                variant.save(update_fields=['stock'])
            else:
                if product.stock < qty:
                    raise ValidationError(
                        f'موجودی محصول {product.name} کافی نیست.'
                    )
                product.stock -= qty
                product.save(update_fields=['stock'])

    # ─────────────────────────────────────────────────────────────────────────
    # CANCEL ORDER
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def cancel_order(order, note=''):
        """
        لغو سفارش
        
        شرایط:
        - سفارش باید در وضعیت PENDING یا PAID باشد
        - اگر PAID باشد، باید مبلغ به کیف پول برگشت داده شود
        """
        if order.is_cancelled:
            raise ValidationError('سفارش قبلاً لغو شده است.')

        if order.is_completed:
            raise ValidationError('سفارش تکمیل‌شده قابل لغو نیست.')

        old_status = order.status
        now = timezone.now()

        # بازگشت مبلغ کیف پول
        if order.is_paid and order.amount_payable > 0:
            OrderService._refund_to_wallet(order)

        # بروزرسانی وضعیت
        order.status = Order.Status.CANCELLED
        order.cancelled_at = now
        order.save(update_fields=['status', 'cancelled_at'])

        # ثبت تاریخچه
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=Order.Status.CANCELLED,
            note=note or 'سفارش لغو شد'
        )

        return order

    @staticmethod
    def _refund_to_wallet(order):
        """بازگشت مبلغ سفارش به کیف پول"""
        wallet = getattr(order.user, 'wallet', None)
        if not wallet:
            return
        
        wallet.deposit(
            amount=order.amount_payable,
            description=f'بازگشت مبلغ سفارش لغوشده {order.order_number}',
            related_order=order
        )

    # ─────────────────────────────────────────────────────────────────────────
    # UPDATE STATUS
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def update_status(order, new_status, note=''):
        """
        تغییر وضعیت سفارش (ارسال - تحویل - تکمیل)
        """
        old_status = order.status

        if old_status == new_status:
            return order

        now = timezone.now()

        # قانون‌های منطقی وضعیت‌ها
        if new_status == Order.Status.SHIPPED:
            order.shipped_at = now

        elif new_status == Order.Status.DELIVERED:
            order.delivered_at = now

        elif new_status == Order.Status.COMPLETED:
            order.completed_at = now

        order.status = new_status
        order.save()

        # ثبت تاریخچه
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=new_status,
            note=note or f'تغییر وضعیت سفارش به {new_status}'
        )

        return order

    # ─────────────────────────────────────────────────────────────────────────
    # EXPIRATION HANDLER
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def expire_order(order):
        """
        انقضای خودکار سفارش بعد از پایان زمان پرداخت
        """
        if order.status != Order.Status.PENDING:
            return order
        
        old_status = order.status

        order.status = Order.Status.CANCELLED
        order.cancelled_at = timezone.now()
        order.save(update_fields=['status', 'cancelled_at'])

        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=Order.Status.CANCELLED,
            note='انقضای خودکار سفارش'
        )

        return order