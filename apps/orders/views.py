from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from .services import CartService
from .models import CartItem
from apps.coupons.models import Coupon
import json

def cart_view(request):
    """
    صفحه نمایش سبد خرید
    """
    cart = CartService.get_cart(request)
    cart_items = cart.items.select_related('product', 'variant', 'product__category', 'product__brand').all()
    
    # محاسبه جمع کل
    subtotal = sum(item.line_total for item in cart_items)
    discount = sum(item.discount_amount for item in cart_items)
    
    # کوپن اعمال شده
    applied_coupon = None
    coupon_discount = 0
    if hasattr(cart, 'applied_coupon_code') and cart.applied_coupon_code:
        try:
            applied_coupon = Coupon.objects.get(code=cart.applied_coupon_code)
            coupon_discount = applied_coupon.calculate_discount(subtotal - discount)
        except Coupon.DoesNotExist:
            cart.applied_coupon_code = None
            cart.save()
    
    total = subtotal - discount - coupon_discount
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'cart_items_count': cart.total_items,
        'subtotal': subtotal,
        'discount': discount,
        'applied_coupon': applied_coupon,
        'coupon_discount': coupon_discount,
        'total': total,
        'title': 'سبد خرید',
    }
    
    return render(request, 'orders/cart.html', context)


@require_POST
def update_cart_item(request, item_id):
    """
    بروزرسانی تعداد آیتم سبد خرید
    """
    try:
        cart = CartService.get_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        CartService.update_item_quantity(cart_item, quantity)
        
        return JsonResponse({
            'success': True,
            'message': 'تعداد محصول بروزرسانی شد'
        })
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'خطا در بروزرسانی'
        }, status=500)


@require_POST
def remove_cart_item(request, item_id):
    """
    حذف آیتم از سبد خرید
    """
    try:
        cart = CartService.get_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        CartService.remove_item(cart_item)
        
        return JsonResponse({
            'success': True,
            'message': 'محصول از سبد خرید حذف شد'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'خطا در حذف محصول'
        }, status=500)


@require_POST
def apply_coupon(request):
    """
    اعمال کد تخفیف
    """
    try:
        cart = CartService.get_cart(request)
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code', '').strip().upper()
        
        if not coupon_code:
            return JsonResponse({
                'success': False,
                'message': 'لطفاً کد تخفیف را وارد کنید'
            }, status=400)
        
        # بررسی وجود کوپن
        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'کد تخفیف نامعتبر است'
            }, status=404)
        
        # محاسبه مجموع سبد
        cart_items = cart.items.select_related('product').all()
        subtotal = sum(item.line_total for item in cart_items)
        discount = sum(item.discount_amount for item in cart_items)
        cart_total = subtotal - discount
        
        # بررسی اعتبار کوپن
        user = request.user if request.user.is_authenticated else None
        can_use, message = coupon.can_use(user, cart_total)
        
        if not can_use:
            return JsonResponse({
                'success': False,
                'message': message
            }, status=400)
        
        # ذخیره کد کوپن در سبد
        cart.applied_coupon_code = coupon_code
        cart.save()
        
        return JsonResponse({
            'success': True,
            'message': f'کد تخفیف {coupon.get_discount_display()} اعمال شد',
            'discount': float(coupon.calculate_discount(cart_total))
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'خطا در اعمال کد تخفیف'
        }, status=500)


@require_POST
def remove_coupon(request):
    """
    حذف کد تخفیف
    """
    try:
        cart = CartService.get_cart(request)
        cart.applied_coupon_code = None
        cart.save()
        
        return JsonResponse({
            'success': True,
            'message': 'کد تخفیف حذف شد'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'خطا در حذف کد تخفیف'
        }, status=500)
