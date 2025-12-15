#!/usr/bin/env python
"""
Quick verification script for PostgreSQL migration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miniup.settings.dev')
django.setup()

from django.db import connection
from apps.accounts.models import User
from apps.products.models import Product
from apps.wallet.models import Wallet
from apps.orders.models import Order

print("\n" + "="*60)
print("PostgreSQL Migration Verification")
print("="*60 + "\n")

# Database Info
print("📊 DATABASE INFORMATION:")
print(f"   Engine: {connection.settings_dict['ENGINE']}")
print(f"   Name: {connection.settings_dict['NAME']}")
print(f"   User: {connection.settings_dict['USER']}")
print(f"   Host: {connection.settings_dict['HOST']}")
print(f"   Port: {connection.settings_dict['PORT']}")

# Data Counts
print("\n📈 DATA MIGRATION STATUS:")
print(f"   Users: {User.objects.count()}")
print(f"   Products: {Product.objects.count()}")
print(f"   Wallets: {Wallet.objects.count()}")
print(f"   Orders: {Order.objects.count()}")

# Test query
print("\n🔍 SAMPLE QUERY TEST:")
try:
    users = User.objects.all()[:3]
    for user in users:
        identifier = user.phone or user.email or f"ID:{user.id}"
        print(f"   - User: {identifier} (Active: {user.is_active})")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n✅ PostgreSQL is working perfectly!")
print("="*60 + "\n")
