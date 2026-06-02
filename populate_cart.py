#!/usr/bin/env python
"""
Script to populate cart with virtual and physical products for testing
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miniup.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from apps.products.models import Product
from apps.orders.services import CartService
from apps.orders.models import Cart

User = get_user_model()

def populate_cart(phone_number=None):
    """Populate cart with test products"""
    
    # Get user by phone number or use first non-superuser
    if phone_number:
        user = User.objects.filter(phone=phone_number).first()
        if not user:
            print(f"❌ User with phone {phone_number} not found!")
            print("Available users:")
            for u in User.objects.all()[:5]:
                print(f"  - {u.phone} ({u.first_name} {u.last_name})")
            return
    else:
        user = User.objects.filter(is_superuser=False).first()
        if not user:
            print("❌ No regular user found. Creating test user...")
            user = User.objects.create_user(
                phone='09123456789',
                email='test@example.com',
                password='testpass123',
                first_name='تست',
                last_name='کاربر'
            )
            print(f"✅ Created test user: {user.phone}")
    
    print(f"✅ Using user: {user.phone}")
    
    # Create a mock request object
    from django.contrib.sessions.backends.db import SessionStore
    
    class MockRequest:
        def __init__(self, user):
            self.user = user
            self.session = SessionStore()
            self.session.create()
    
    request = MockRequest(user)
    
    # Get or create cart
    cart = CartService.get_cart(request)
    
    # Clear existing items
    cart.items.all().delete()
    print(f"🧹 Cleared cart for user {user.phone}")
    
    # Get virtual products
    virtual_products = Product.objects.filter(
        product_type='virtual',
        is_active=True
    )[:3]
    
    print(f"\n📦 Adding {virtual_products.count()} virtual products...")
    for product in virtual_products:
        try:
            CartService.add_item(
                cart=cart,
                product=product,
                quantity=1
            )
            print(f"  ✅ Added: {product.name} ({product.price:,} تومان)")
        except Exception as e:
            print(f"  ❌ Failed to add {product.name}: {e}")
    
    # Get physical products
    physical_products = Product.objects.filter(
        product_type='physical',
        is_active=True
    )[:3]
    
    print(f"\n📦 Adding {physical_products.count()} physical products...")
    for product in physical_products:
        try:
            CartService.add_item(
                cart=cart,
                product=product,
                quantity=2
            )
            print(f"  ✅ Added: {product.name} ({product.price:,} تومان) x2")
        except Exception as e:
            print(f"  ❌ Failed to add {product.name}: {e}")
    
    # Get game currency products
    game_currency = Product.objects.filter(
        product_type='game_currency',
        is_active=True
    ).first()
    
    if game_currency:
        print(f"\n🎮 Adding game currency product...")
        try:
            CartService.add_item(
                cart=cart,
                product=game_currency,
                quantity=1,
                currency_amount=1000
            )
            print(f"  ✅ Added: {game_currency.name} (1000 currency)")
        except Exception as e:
            print(f"  ❌ Failed to add {game_currency.name}: {e}")
    
    # Show cart summary
    print(f"\n" + "="*60)
    print(f"🛒 Cart Summary for {user.phone}")
    print(f"="*60)
    
    cart_items = cart.items.select_related('product').all()
    
    if not cart_items:
        print("  ⚠️  Cart is empty!")
    else:
        subtotal = sum(item.original_price * item.quantity for item in cart_items)
        discount = sum(item.discount_amount for item in cart_items)
        total = subtotal - discount
        
        print(f"\n📝 Items ({cart_items.count()}):")
        for item in cart_items:
            product_type = "🎮" if item.product.product_type == 'virtual' else "📦"
            print(f"  {product_type} {item.product.name}")
            print(f"     Quantity: {item.quantity}")
            print(f"     Original: {item.original_price:,} تومان")
            print(f"     Price: {item.unit_price:,} تومان")
            if item.discount_amount > 0:
                print(f"     Discount: {item.discount_amount:,} تومان")
            print()
        
        print(f"💰 Financial Summary:")
        print(f"  جمع کل محصولات: {subtotal:,} تومان")
        if discount > 0:
            print(f"  تخفیف محصولات: {discount:,} تومان")
        print(f"  مبلغ قابل پرداخت: {total:,} تومان")
    
    print(f"\n✅ Cart populated successfully!")
    print(f"🌐 Visit: http://127.0.0.1:8000/orders/cart/")
    print()

if __name__ == '__main__':
    try:
        # Check if phone number is provided as argument
        phone = sys.argv[1] if len(sys.argv) > 1 else None
        if phone:
            print(f"📱 Populating cart for user: {phone}\n")
        populate_cart(phone)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
