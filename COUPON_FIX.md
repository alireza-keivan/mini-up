# 🎯 Coupon Usage Fix - Critical Issue Resolved

## 📋 Problem Description

**Issue**: Coupons were being marked as "used" immediately when an order was created, even if the user never completed the payment. This caused several problems:

1. ❌ Users could apply a coupon, create an order, but not pay
2. ❌ The coupon would be marked as used and increment `used_count`
3. ❌ The coupon slot would be wasted even though no actual purchase happened
4. ❌ Users couldn't reuse the coupon even though they didn't complete payment
5. ❌ Coupons with limited usage (`max_uses`) would run out incorrectly

## ✅ Solution Implemented

### Core Changes

#### 1. **Delayed Coupon Marking** (apps/orders/services.py)

**Before**: Coupon was marked as used during `create_order_from_cart()`
```python
# علامت‌گذاری استفاده از کوپن
if coupon:
    OrderService._mark_coupon_used(coupon, user, order)  # ❌ TOO EARLY!
```

**After**: Coupon is marked as used only after successful payment in `confirm_payment()`
```python
# ✅ اینجا است که کوپن باید علامت‌گذاری شود (فقط پس از پرداخت موفق)
if order.coupon:
    OrderService._mark_coupon_used(order.coupon, order.user, order)
```

#### 2. **Improved `_mark_coupon_used()` Method**

Added duplicate check to prevent double-marking:
```python
@staticmethod
def _mark_coupon_used(coupon, user, order):
    """
    ثبت استفاده از کوپن (فقط اگر قبلاً ثبت نشده باشد)
    
    این متد فقط باید پس از پرداخت موفق فراخوانی شود.
    """
    # بررسی اینکه آیا این کوپن قبلاً برای این سفارش ثبت شده
    existing_usage = CouponUsage.objects.filter(
        coupon=coupon,
        user=user,
        order=order
    ).exists()
    
    if existing_usage:
        return  # Already marked, skip
    
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
```

#### 3. **Updated Coupon Validation** (apps/coupons/services.py)

Now only counts PAID orders when checking usage limits:

```python
# Check per-user usage limit (فقط سفارشات پرداخت شده)
user_usage_count = CouponUsage.objects.filter(
    coupon=coupon,
    user=user,
    order__status__in=[
        Order.Status.PAID,
        Order.Status.PROCESSING,
        Order.Status.SHIPPED,
        Order.Status.DELIVERED,
        Order.Status.COMPLETED
    ]
).count()
```

#### 4. **Cleanup Management Command**

Created `cleanup_unpaid_coupons` management command to clean up old unpaid orders:

```bash
# پاکسازی کوپن‌های سفارشات منقضی‌شده
python manage.py cleanup_unpaid_coupons

# نمایش بدون اعمال تغییرات
python manage.py cleanup_unpaid_coupons --dry-run
```

This command:
- ✅ Finds expired unpaid orders with coupons
- ✅ Deletes their `CouponUsage` records
- ✅ Decrements coupon `used_count`
- ✅ Frees up coupon slots for legitimate users

---

## 🔄 Complete Coupon Flow

### Scenario 1: Successful Purchase ✅

1. User applies coupon code → **Validated** (not marked as used)
2. Order created with coupon → **Stored in order.coupon field**
3. User pays successfully → **Payment confirmed**
4. `confirm_payment()` is called → **Coupon marked as used NOW**
5. `CouponUsage` created → **`used_count` incremented**

**Result**: ✅ Coupon properly marked as used

### Scenario 2: Abandoned Payment ❌→✅

1. User applies coupon code → **Validated** (not marked as used)
2. Order created with coupon → **Stored in order.coupon field**
3. User abandons payment → **Order expires after 1 hour**
4. Coupon is **NOT marked as used** → **User can reapply it!**

**Result**: ✅ Coupon remains available for legitimate use

### Scenario 3: Failed Payment ❌→✅

1. User applies coupon code → **Validated**
2. Order created with coupon → **Stored**
3. Payment fails → **Order status = FAILED**
4. Coupon is **NOT marked as used** → **Can be reused**

**Result**: ✅ Coupon slot not wasted

---

## 📊 Database Schema

### CouponUsage Model
```python
class CouponUsage(models.Model):
    coupon = ForeignKey(Coupon)
    user = ForeignKey(User)
    order = ForeignKey(Order)  # 🔑 KEY: Links to actual order
    discount_amount = DecimalField()
    used_at = DateTimeField(auto_now_add=True)
```

**Important**: 
- `CouponUsage` is only created AFTER payment success
- It's linked to the `Order` for audit trail
- Can be cleaned up if order expires unpaid

---

## 🧪 Testing Scenarios

### Test 1: Apply Coupon Without Payment
```python
# 1. Create order with coupon
order = OrderService.create_order_from_cart(
    user=user,
    cart=cart,
    coupon=coupon
)

# 2. Check coupon NOT marked as used yet
assert CouponUsage.objects.filter(order=order).count() == 0
assert coupon.used_count == 0  # Unchanged

# 3. Confirm payment
OrderService.confirm_payment(order, ref_id='123456')

# 4. NOW coupon is marked as used
assert CouponUsage.objects.filter(order=order).count() == 1
assert Coupon.objects.get(id=coupon.id).used_count == 1
```

### Test 2: Reuse Coupon After Abandoned Order
```python
# 1. Create order with coupon (don't pay)
order1 = OrderService.create_order_from_cart(
    user=user,
    cart=cart,
    coupon=coupon
)

# 2. Order expires (no payment)
order1.expires_at = timezone.now() - timedelta(hours=2)
order1.save()

# 3. User can apply same coupon again
is_valid, message, _ = CouponService.validate_coupon(
    code=coupon.code,
    user=user,
    cart_total=1000000
)

assert is_valid == True  # ✅ Coupon is still valid!
```

### Test 3: Cleanup Command
```bash
# Run cleanup for expired unpaid orders
python manage.py cleanup_unpaid_coupons

# Output:
# 📊 تعداد سفارشات منقضی‌شده با کوپن: 5
#   - سفارش ORD-123456: کوپن SUMMER30 آزاد شد
#   - سفارش ORD-123457: کوپن FIRST20 آزاد شد
# ✅ تعداد کوپن‌های پاکسازی شده: 5
```

---

## 🔧 Configuration

### Order Expiration Time

Orders expire after 1 hour by default (set in `create_order_from_cart`):
```python
expires_at=timezone.now() + timedelta(hours=1)
```

To change this, update the timedelta value in:
- `apps/orders/services.py` → `create_order_from_cart()`

### Automatic Cleanup (Optional)

Add to crontab for automatic cleanup every hour:
```bash
# Cleanup expired unpaid coupons every hour
0 * * * * cd /path/to/mini-up && source bin/activate && python manage.py cleanup_unpaid_coupons >> /var/log/coupon_cleanup.log 2>&1
```

Or use Celery Beat for scheduled tasks:
```python
# celerybeat_schedule (if using Celery)
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-unpaid-coupons': {
        'task': 'apps.coupons.tasks.cleanup_unpaid_coupons',
        'schedule': crontab(minute=0, hour='*/1'),  # Every hour
    },
}
```

---

## 🎯 Benefits

### For Users:
✅ Can abandon cart without losing coupon
✅ Can retry payment with same coupon if it fails
✅ Fair usage - no wasted coupon slots

### For Business:
✅ Accurate coupon usage statistics
✅ No artificial shortage of coupon slots
✅ Better conversion tracking
✅ Clean database (no orphaned CouponUsage records)

### For Developers:
✅ Clear separation of concerns
✅ Atomic transactions for payment confirmation
✅ Easy to audit coupon usage
✅ Automatic cleanup mechanism

---

## 📈 Metrics to Monitor

1. **Coupon Application Rate**: How many times coupons are applied
2. **Coupon Conversion Rate**: (Paid orders with coupons) / (Orders created with coupons)
3. **Abandoned Coupon Orders**: Orders with coupons that expired unpaid
4. **Cleanup Impact**: How many CouponUsage records are cleaned up weekly

Example query:
```python
from django.db.models import Count, Q

# Abandoned coupon orders (last 7 days)
abandoned = Order.objects.filter(
    coupon__isnull=False,
    status=Order.Status.PENDING,
    expires_at__lt=timezone.now(),
    created_at__gte=timezone.now() - timedelta(days=7)
).count()

# Successful coupon orders (last 7 days)
successful = Order.objects.filter(
    coupon__isnull=False,
    status__in=[Order.Status.PAID, Order.Status.COMPLETED],
    created_at__gte=timezone.now() - timedelta(days=7)
).count()

conversion_rate = (successful / (successful + abandoned)) * 100 if (successful + abandoned) > 0 else 0

print(f"Coupon Conversion Rate: {conversion_rate:.2f}%")
```

---

## 🔒 Security Considerations

1. **Race Conditions**: The `_mark_coupon_used()` method checks for existing usage to prevent double-marking
2. **Transaction Safety**: All coupon operations use `@transaction.atomic` decorator
3. **Validation Before Use**: Always validate coupon before applying
4. **Audit Trail**: `CouponUsage` keeps full history with order reference

---

## 📚 Related Files

- `apps/coupons/models.py` - Coupon and CouponUsage models
- `apps/coupons/services.py` - CouponService with validation logic
- `apps/orders/services.py` - OrderService with payment confirmation
- `apps/orders/models.py` - Order model with status tracking
- `apps/coupons/management/commands/cleanup_unpaid_coupons.py` - Cleanup command

---

## 🚀 Deployment Checklist

- [x] Update `apps/orders/services.py` - Move coupon marking to payment confirmation
- [x] Update `apps/coupons/services.py` - Count only paid orders in validation
- [x] Create cleanup management command
- [x] Test coupon application flow
- [x] Test payment confirmation flow
- [x] Test abandoned order scenario
- [ ] Run cleanup command on production (if needed): `python manage.py cleanup_unpaid_coupons`
- [ ] Set up automated cleanup schedule (cron/celery)
- [ ] Monitor coupon conversion metrics

---

**Fixed By**: AI Assistant  
**Date**: December 15, 2025  
**Issue**: Coupons marked as used before payment completion  
**Impact**: High - Affects all coupon-based promotions  
**Status**: ✅ RESOLVED
