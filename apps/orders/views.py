from django.shortcuts import render
from .services import CartService

def cart_view(request):
    """
    صفحه نمایش سبد خرید
    """
    cart = CartService.get_cart(request)
    cart_items = cart.items.select_related('product', 'variant', 'product__category', 'product__brand').all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'title': 'سبد خرید',
    }
    
    return render(request, 'orders/cart.html', context)
