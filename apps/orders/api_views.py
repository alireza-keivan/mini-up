# apps/orders/api_views.py

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from .models import Cart, CartItem, Order
from .services import CartService, OrderService
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    CheckoutSerializer,
    CheckoutPreviewSerializer,
)
from apps.products.models import Product, ProductVariant


# ═══════════════════════════════════════════════════════════════════════════════
# CART API VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class CartAPIView(APIView):
    """
    مشاهده سبد خرید
    
    GET: دریافت سبد خرید فعلی
    DELETE: خالی کردن سبد خرید
    """
    permission_classes = [AllowAny]

    def get(self, request):
        cart = CartService.get_cart(request)
        serializer = CartSerializer(cart)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def delete(self, request):
        cart = CartService.get_cart(request)
        CartService.clear_cart(cart)
        return Response({
            'success': True,
            'message': 'سبد خرید خالی شد.'
        })


class CartAddItemAPIView(APIView):
    """
    افزودن محصول به سبد خرید
    
    POST: افزودن آیتم جدید
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # دریافت محصول
        product = get_object_or_404(Product, id=data['product_id'], is_active=True)
        
        # دریافت واریانت (اختیاری)
        variant = None
        if data.get('variant_id'):
            variant = get_object_or_404(
                ProductVariant, 
                id=data['variant_id'], 
                product=product,
                is_active=True
            )
        
        # دریافت سبد
        cart = CartService.get_cart(request)
        
        try:
            item = CartService.add_item(
                cart=cart,
                product=product,
                variant=variant,
                quantity=data.get('quantity', 1),
                game_user_id=data.get('game_user_id', ''),
                currency_amount=data.get('currency_amount')
            )
            
            return Response({
                'success': True,
                'message': 'محصول به سبد خرید اضافه شد.',
                'data': CartItemSerializer(item).data
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CartItemAPIView(APIView):
    """
    مدیریت آیتم سبد خرید
    
    PATCH: بروزرسانی تعداد
    DELETE: حذف آیتم
    """
    permission_classes = [AllowAny]

    def get_cart_item(self, request, item_id):
        cart = CartService.get_cart(request)
        return get_object_or_404(CartItem, id=item_id, cart=cart)

    def patch(self, request, item_id):
        cart_item = self.get_cart_item(request, item_id)
        
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_item = CartService.update_item_quantity(
                cart_item=cart_item,
                quantity=serializer.validated_data['quantity']
            )
            
            return Response({
                'success': True,
                'message': 'تعداد بروزرسانی شد.',
                'data': CartItemSerializer(updated_item).data
            })
            
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, item_id):
        cart_item = self.get_cart_item(request, item_id)
        CartService.remove_item(cart_item)
        
        return Response({
            'success': True,
            'message': 'آیتم از سبد حذف شد.'
        })


class CartValidateAPIView(APIView):
    """
    اعتبارسنجی سبد خرید قبل از پرداخت
    """
    permission_classes = [AllowAny]

    def get(self, request):
        cart = CartService.get_cart(request)
        valid_items, invalid_items = CartService.validate_cart_items(cart)
        
        invalid_data = []
        for item in invalid_items:
            invalid_data.append({
                'product_name': item['item'].product.name,
                'reason': item['reason']
            })
        
        return Response({
            'success': len(invalid_items) == 0,
            'valid_count': len(valid_items),
            'invalid_items': invalid_data
        })


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKOUT API VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class CheckoutPreviewAPIView(APIView):
    """
    پیش‌نمایش سفارش قبل از پرداخت
    
    محاسبه مبالغ با در نظر گرفتن کوپن و کیف پول
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        cart = CartService.get_cart(request)
        
        if not cart.items.exists():
            return Response({
                'success': False,
                'message': 'سبد خرید خالی است.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # محاسبات اولیه
        subtotal = cart.subtotal
        discount = cart.total_discount
        
        # کوپن
        coupon_discount = 0
        coupon = None
        if data.get('coupon_code'):
            try:
                from apps.coupons.services import CouponService
                coupon = CouponService.validate_coupon(
                    code=data['coupon_code'],
                    user=request.user,
                    cart_total=subtotal
                )
                coupon_discount = CouponService.calculate_discount(coupon, subtotal)
            except ValidationError as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # هزینه ارسال
        shipping_cost = OrderService._calculate_shipping_cost(cart, None)
        
        # جمع کل
        total = subtotal - discount - coupon_discount + shipping_cost
        
        # کیف پول
        wallet_amount = 0
        wallet_available = 0
        if data.get('use_wallet'):
            wallet = getattr(request.user, 'wallet', None)
            if wallet:
                wallet_available = wallet.available_balance
                requested = data.get('wallet_amount', 0)
                wallet_amount = min(requested, wallet_available, total)
        
        amount_payable = total - wallet_amount
        
        return Response({
            'success': True,
            'data': {
                'subtotal': int(subtotal),
                'discount': int(discount),
                'coupon_discount': int(coupon_discount),
                'shipping_cost': int(shipping_cost),
                'total': int(total),
                'wallet_available': int(wallet_available),
                'wallet_used': int(wallet_amount),
                'amount_payable': int(amount_payable),
            }
        })


class CheckoutAPIView(APIView):
    """
    ثبت نهایی سفارش
    
    POST: ایجاد سفارش و دریافت لینک پرداخت
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        user = request.user
        cart = CartService.get_cart(request)
        
        if not cart.items.exists():
            return Response({
                'success': False,
                'message': 'سبد خرید خالی است.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # دریافت آدرس
        shipping_address = None
        if data.get('shipping_address_id'):
            from apps.accounts.models import UserAddress
            shipping_address = get_object_or_404(
                UserAddress,
                id=data['shipping_address_id'],
                user=user
            )
        
        # دریافت کوپن
        coupon = None
        if data.get('coupon_code'):
            try:
                from apps.coupons.services import CouponService
                coupon = CouponService.validate_coupon(
                    code=data['coupon_code'],
                    user=user,
                    cart_total=cart.subtotal
                )
            except ValidationError as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # ایجاد سفارش
        try:
            order = OrderService.create_order_from_cart(
                user=user,
                cart=cart,
                shipping_address=shipping_address,
                coupon=coupon,
                use_wallet=data.get('use_wallet', False),
                wallet_amount=data.get('wallet_amount', 0),
                payment_method=data.get('payment_method', 'zarinpal'),
                customer_note=data.get('customer_note', ''),
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # اگر مبلغ قابل پرداخت صفر است
            if order.amount_payable <= 0:
                OrderService.confirm_payment(order, ref_id='wallet_only')
                return Response({
                    'success': True,
                    'message': 'سفارش با موفقیت ثبت شد.',
                    'data': {
                        'order_id': str(order.id),
                        'order_number': order.order_number,
                        'payment_required': False
                    }
                })
            
            # ایجاد لینک پرداخت
            payment_url = self._create_payment_url(request, order)
            
            return Response({
                'success': True,
                'message': 'سفارش ایجاد شد. لطفاً پرداخت را انجام دهید.',
                'data': {
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                    'amount_payable': int(order.amount_payable),
                    'payment_required': True,
                    'payment_url': payment_url
                }
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def _create_payment_url(self, request, order):
        """ایجاد لینک پرداخت با زرین‌پال"""
        from django.urls import reverse
        from apps.payments.services import ZarinPalService
        
        callback_url = request.build_absolute_uri(
            reverse('orders:payment_verify')
        )
        
        zarinpal = ZarinPalService(sandbox=True)
        result = zarinpal.request_payment(
            amount=int(order.amount_payable),
            description=f'پرداخت سفارش {order.order_number}',
            callback_url=callback_url,
            mobile=getattr(request.user, 'phone', None),
            email=getattr(request.user, 'email', None),
        )
        
        if result['success']:
            order.payment_authority = result['authority']
            order.save(update_fields=['payment_authority'])
            return result['payment_url']
        
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# ORDER API VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class OrderListAPIView(APIView):
    """
    لیست سفارشات کاربر
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        
        # فیلتر وضعیت
        status_filter = request.query_params.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        serializer = OrderListSerializer(orders, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

class OrderDetailAPIView(APIView):
    """
    مشاهده جزئیات سفارش
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(
            Order.objects.prefetch_related('items', 'status_history'),
            id=order_id,
            user=request.user
        )

        serializer = OrderDetailSerializer(order)
        return Response({
            'success': True,
            'data': serializer.data
        })


class PaymentVerifyAPIView(APIView):
    """
    تأیید پرداخت از درگاه پرداخت (مثلاً زرین‌پال)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        authority = request.GET.get("Authority")
        status_param = request.GET.get("Status")

        if not authority:
            return Response({
                "success": False,
                "message": "Authority ارسال نشده است."
            }, status=400)

        # یافتن سفارش
        order = Order.objects.filter(payment_authority=authority).first()
        if not order:
            return Response({
                "success": False,
                "message": "سفارشی با این Authority یافت نشد."
            }, status=404)

        # اگر پرداخت کنسل شده
        if status_param != "OK":
            return Response({
                "success": False,
                "message": "پرداخت توسط کاربر لغو شد."
            })

        # Verify with ZarinPal
        from apps.payments.services import ZarinPalService
        zarin = ZarinPalService(sandbox=True)

        result = zarin.verify_payment(
            authority=authority,
            amount=int(order.amount_payable)
        )

        if result['success']:
            # ثبت تکمیل پرداخت در سیستم سفارش
            OrderService.confirm_payment(order, ref_id=result.get("ref_id"))

            return Response({
                "success": True,
                "message": "پرداخت با موفقیت تایید شد.",
                "data": {
                    "order_id": str(order.id),
                    "order_number": order.order_number,
                    "ref_id": result.get("ref_id")
                }
            })

        else:
            return Response({
                "success": False,
                "message": result.get("error", "خطا در تایید پرداخت")
            }, status=400)
