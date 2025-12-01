# apps/coupons/api_views.py

"""
Coupon API Views
RESTful endpoints for coupon operations

All cart operations use apps.orders.models.Cart
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.shortcuts import get_object_or_404
from decimal import Decimal

from .models import Coupon, CouponUsage
from .services import CouponService
from .serializers import (
    CouponSerializer,
    CouponMinimalSerializer,
    CouponUsageSerializer,
    CouponValidateSerializer,
    CouponApplySerializer,
)


# ═══════════════════════════════════════════════════════════════════════════════
# COUPON VALIDATION API
# ═══════════════════════════════════════════════════════════════════════════════

class CouponValidateAPIView(APIView):
    """
    اعتبارسنجی کوپن
    POST /coupons/api/v1/validate/
    
    Body:
        - code: کد کوپن
        - cart_total: مجموع سبد خرید (اختیاری - اگر ارسال نشود از سبد خرید خوانده می‌شود)
    
    Returns:
        - is_valid: آیا معتبر است
        - message: پیام
        - coupon: اطلاعات کوپن (در صورت معتبر بودن)
        - estimated_discount: تخفیف تخمینی
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CouponValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        cart_total = serializer.validated_data.get('cart_total')
        
        # Get cart and items from orders app
        cart = self._get_cart(request)
        cart_items = []
        
        if cart:
            cart_items = list(cart.items.select_related('product', 'variant').all())
            # Use cart total if not provided
            if cart_total is None:
                cart_total = cart.total
        else:
            if cart_total is None:
                cart_total = Decimal('0')
        
        # Validate coupon
        is_valid, message, coupon = CouponService.validate_coupon(
            code=code,
            user=request.user,
            cart_total=cart_total,
            cart_items=cart_items
        )
        
        response_data = {
            'success': is_valid,
            'is_valid': is_valid,
            'message': message,
            'coupon': None,
            'estimated_discount': None,
        }
        
        if is_valid and coupon:
            # Calculate estimated discount
            discount_info = CouponService.calculate_discount(
                coupon=coupon,
                cart_total=cart_total,
                cart_items=cart_items
            )
            
            response_data['coupon'] = CouponSerializer(coupon).data
            response_data['estimated_discount'] = int(discount_info['discount_amount'])
            response_data['discount_percent'] = discount_info.get('discount_percent', 0)
            response_data['final_total'] = int(discount_info['final_total'])
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def _get_cart(self, request):
        """دریافت سبد خرید از اپ orders"""
        try:
            from apps.orders.models import Cart
            return Cart.get_or_create_cart(request)
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# COUPON APPLY API
# ═══════════════════════════════════════════════════════════════════════════════

class CouponApplyAPIView(APIView):
    """
    اعمال کوپن به سبد خرید
    POST /coupons/api/v1/apply/
    
    Body:
        - code: کد کوپن
    
    Returns:
        - success: آیا موفق بود
        - message: پیام
        - discount_amount: مبلغ تخفیف
        - final_total: مبلغ نهایی
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CouponApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        
        # Get cart from orders app
        cart = self._get_cart(request)
        
        if not cart or not cart.items.exists():
            return Response({
                'success': False,
                'message': 'سبد خرید شما خالی است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart_total = cart.total
        cart_items = list(cart.items.select_related('product', 'variant').all())
        
        # Apply coupon using service
        result = CouponService.apply_coupon(
            code=code,
            user=request.user,
            cart_total=cart_total,
            cart_items=cart_items
        )
        
        if not result['success']:
            return Response({
                'success': False,
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Store applied coupon in session
        # Note: Actual coupon binding to Order happens at checkout
        coupon = result['coupon']
        self._store_coupon_in_session(request, coupon, result['discount'])
        
        return Response({
            'success': True,
            'message': result['message'],
            'data': {
                'coupon_code': coupon.code,
                'coupon_description': coupon.description,
                'discount_amount': int(result['discount']),
                'discount_percent': result['details'].get('discount_percent', 0),
                'cart_total': int(cart_total),
                'final_total': int(result['final_total']),
            }
        }, status=status.HTTP_200_OK)
    
    def _get_cart(self, request):
        """دریافت سبد خرید از اپ orders"""
        try:
            from apps.orders.models import Cart
            return Cart.get_or_create_cart(request)
        except Exception:
            return None
    
    def _store_coupon_in_session(self, request, coupon, discount_amount):
        """
        ذخیره کوپن اعمال‌شده در session
        
        در مرحله checkout، این اطلاعات خوانده شده و به Order منتقل می‌شود.
        
        Args:
            request: HTTP request object
            coupon: شیء کوپن
            discount_amount: مبلغ تخفیف محاسبه‌شده
        """
        request.session['applied_coupon'] = {
            'id': coupon.id,
            'code': coupon.code,
            'discount_amount': int(discount_amount),
            'discount_type': coupon.discount_type,
            'discount_value': float(coupon.discount_value),
        }
        request.session.modified = True


# ═══════════════════════════════════════════════════════════════════════════════
# COUPON REMOVE API
# ═══════════════════════════════════════════════════════════════════════════════

class CouponRemoveAPIView(APIView):
    """
    حذف کوپن از سبد خرید
    POST /coupons/api/v1/remove/
    
    Returns:
        - success: آیا موفق بود
        - message: پیام
        - cart_total: مجموع سبد بدون تخفیف
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        cart = self._get_cart(request)
        
        # Check if coupon exists in session
        if 'applied_coupon' not in request.session:
            return Response({
                'success': False,
                'message': 'کوپنی اعمال نشده است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove coupon from session
        del request.session['applied_coupon']
        request.session.modified = True
        
        cart_total = cart.total if cart else 0
        
        return Response({
            'success': True,
            'message': 'کوپن با موفقیت حذف شد',
            'data': {
                'cart_total': int(cart_total),
                'final_total': int(cart_total),
                'discount_amount': 0,
            }
        }, status=status.HTTP_200_OK)
    
    def _get_cart(self, request):
        """دریافت سبد خرید از اپ orders"""
        try:
            from apps.orders.models import Cart
            return Cart.get_or_create_cart(request)
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# USER AVAILABLE COUPONS API
# ═══════════════════════════════════════════════════════════════════════════════

class UserAvailableCouponsAPIView(APIView):
    """
    دریافت لیست کوپن‌های قابل استفاده برای کاربر
    GET /coupons/api/v1/available/
    
    Returns:
        - success: bool
        - count: تعداد کوپن‌ها
        - data: لیست کوپن‌ها
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        coupons = CouponService.get_user_available_coupons(request.user)
        
        return Response({
            'success': True,
            'count': len(coupons),
            'data': CouponMinimalSerializer(coupons, many=True).data
        }, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════════════════
# USER COUPON USAGE HISTORY API
# ═══════════════════════════════════════════════════════════════════════════════

class UserCouponUsagesAPIView(APIView):
    """
    تاریخچه استفاده از کوپن‌های کاربر
    GET /coupons/api/v1/usages/
    
    Returns:
        - success: bool
        - count: تعداد استفاده‌ها
        - data: لیست استفاده‌ها
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        usages = CouponUsage.objects.filter(
            user=request.user
        ).select_related(
            'coupon', 'order'
        ).order_by('-used_at')
        
        return Response({
            'success': True,
            'count': usages.count(),
            'data': CouponUsageSerializer(usages, many=True).data
        }, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC COUPON CHECK API (for anonymous preview)
# ═══════════════════════════════════════════════════════════════════════════════

class CouponCheckAPIView(APIView):
    """
    بررسی سریع وجود و اعتبار کوپن (بدون نیاز به لاگین)
    GET /coupons/api/v1/check/<code>/
    
    فقط اطلاعات عمومی برمی‌گرداند، نه اعتبارسنجی کامل
    """
    permission_classes = [AllowAny]
    
    def get(self, request, code):
        coupon = CouponService.get_coupon_by_code(code)
        
        if not coupon:
            return Response({
                'success': False,
                'exists': False,
                'message': 'کوپن یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Return basic public info
        return Response({
            'success': True,
            'exists': True,
            'data': {
                'code': coupon.code,
                'description': coupon.description,
                'discount_display': self._get_discount_display(coupon),
                'min_purchase': int(coupon.min_purchase),
                'valid_until': coupon.valid_until.isoformat() if coupon.valid_until else None,
                'is_expired': coupon.status == Coupon.Status.EXPIRED,
                'is_active': coupon.is_active and coupon.is_valid,
            }
        }, status=status.HTTP_200_OK)
    
    def _get_discount_display(self, coupon) -> str:
        """نمایش تخفیف به صورت خوانا"""
        if coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
            text = f'{coupon.discount_value:.0f}%'
            if coupon.max_discount:
                text += f' (حداکثر {coupon.max_discount:,.0f} تومان)'
            return text
        return f'{coupon.discount_value:,.0f} تومان'


# ═══════════════════════════════════════════════════════════════════════════════
# APPLIED COUPON STATUS API
# ═══════════════════════════════════════════════════════════════════════════════

class AppliedCouponStatusAPIView(APIView):
    """
    وضعیت کوپن اعمال‌شده روی سبد خرید
    GET /coupons/api/v1/applied/
    
    Returns:
        - has_coupon: آیا کوپنی اعمال شده
        - coupon: اطلاعات کوپن
        - discount_amount: مبلغ تخفیف
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        cart = self._get_cart(request)
        cart_total = cart.total if cart else Decimal('0')
        
        # Check session for applied coupon
        session_coupon = request.session.get('applied_coupon')
        
        if not session_coupon:
            return Response({
                'success': True,
                'has_coupon': False,
                'coupon': None,
                'discount_amount': 0,
                'cart_total': int(cart_total),
                'final_total': int(cart_total)
            }, status=status.HTTP_200_OK)
        
        # Re-validate coupon (in case it expired or cart changed)
        coupon = CouponService.get_coupon_by_code(session_coupon['code'])
        
        if not coupon:
            # Coupon no longer valid → remove from session
            del request.session['applied_coupon']
            request.session.modified = True
            
            return Response({
                'success': False,
                'has_coupon': False,
                'message': 'کوپن دیگر معتبر نیست و حذف شد',
                'discount_amount': 0,
                'cart_total': int(cart_total),
                'final_total': int(cart_total),
            }, status=status.HTTP_200_OK)

        cart_items = list(cart.items.select_related('product', 'variant').all())

        # Re‑calculate discount dynamically
        discount_info = CouponService.calculate_discount(
            coupon=coupon,
            cart_total=cart_total,
            cart_items=cart_items
        )

        discount_amount = int(discount_info['discount_amount'])
        final_total = int(discount_info['final_total'])

        return Response({
            'success': True,
            'has_coupon': True,
            'coupon': CouponSerializer(coupon).data,
            'discount_amount': discount_amount,
            'discount_percent': discount_info.get('discount_percent', 0),
            'cart_total': int(cart_total),
            'final_total': final_total,
        }, status=status.HTTP_200_OK)

    def _get_cart(self, request):
        """دریافت سبد خرید از اپ orders"""
        try:
            from apps.orders.models import Cart
            return Cart.get_or_create_cart(request)
        except Exception:
            return None