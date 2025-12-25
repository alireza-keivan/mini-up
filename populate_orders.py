#!/usr/bin/env python
"""
Populate sample orders for testing
"""
import os
import sys
import django
from datetime import timedelta
import random

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miniup.settings')
django.setup()

from django.utils import timezone

from django.contrib.auth import get_user_model
from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from decimal import Decimal

User = get_user_model()

def create_sample_orders():
    """Create 10 sample orders with different statuses"""
    
    # Get or create a test user
    user = User.objects.first()
    if not user:
        print("❌ No users found. Please create a user first.")
        return
    
    # Get some products
    products = list(Product.objects.filter(is_active=True)[:5])
    if not products:
        print("❌ No products found. Please create products first.")
        return
    
    print(f"✅ Found user: {user.phone or user.email}")
    print(f"✅ Found {len(products)} products")
    
    # Order statuses to create
    statuses = [
        ('processing', 'در حال پردازش'),
        ('processing', 'در حال پردازش'),
        ('processing', 'در حال پردازش'),
        ('delivered', 'تحویل شده'),
        ('delivered', 'تحویل شده'),
        ('delivered', 'تحویل شده'),
        ('cancelled', 'لغو شده'),
        ('cancelled', 'لغو شده'),
        ('confirmed', 'تایید شده'),
        ('shipped', 'ارسال شده'),
    ]
    
    orders_created = 0
    
    for idx, (status_code, status_label) in enumerate(statuses, 1):
        try:
            # Generate order details with random suffix to avoid duplicates
            order_number = f'ORD-{timezone.now().strftime("%Y%m%d")}-{random.randint(2000, 9999)}'
            tracking_code = f'TRK-{random.randint(100000, 999999)}'
            
            # Calculate dates
            created_at = timezone.now() - timedelta(days=random.randint(1, 30))
            
            # Random selection of products for this order
            num_items = random.randint(1, 3)
            selected_products = random.sample(products, min(num_items, len(products)))
            
            # Calculate totals
            subtotal = sum(p.price * random.randint(1, 2) for p in selected_products)
            discount_amount = int(subtotal * random.uniform(0, 0.1))  # 0-10% discount
            shipping_cost = 0 if any(p.product_type == 'virtual' for p in selected_products) else 50000
            total = subtotal - discount_amount + shipping_cost
            
            # Create order
            order = Order.objects.create(
                order_number=order_number,
                tracking_code=tracking_code,
                user=user,
                status=status_code,
                payment_method='zarinpal',
                subtotal=subtotal,
                discount_amount=discount_amount,
                shipping_cost=shipping_cost,
                total=total,
                amount_payable=total,
                paid_at=created_at if status_code not in ['cancelled', 'pending'] else None,
                created_at=created_at,
                updated_at=created_at,
            )
            
            # Create order items
            for product in selected_products:
                quantity = random.randint(1, 2)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=product.price,
                    original_price=product.price,
                    total_price=product.price * quantity,
                    discount_amount=0,
                )
            
            orders_created += 1
            print(f"✅ Created order {idx}/10: {order_number} - {status_label}")
            
        except Exception as e:
            print(f"❌ Error creating order {idx}: {e}")
            continue
    
    print(f"\n🎉 Successfully created {orders_created} sample orders!")
    print(f"📊 Status breakdown:")
    print(f"   - در حال پردازش: 3 orders")
    print(f"   - تحویل شده: 3 orders")
    print(f"   - لغو شده: 2 orders")
    print(f"   - تایید شده: 1 order")
    print(f"   - ارسال شده: 1 order")

if __name__ == '__main__':
    create_sample_orders()
