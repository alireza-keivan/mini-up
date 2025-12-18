# Virtual Services Page - Admin Guide
## Dynamic Content Management

**Date**: December 16, 2025  
**Status**: ✅ IMPLEMENTED  
**Page**: `/virtual-services/`

---

## 🎯 Overview

The Virtual Services page has been converted from **hard-coded content** to **fully dynamic** content managed through the Django admin panel.

### What Changed:
- ❌ **Old**: Hard-coded HTML with fixed categories and products
- ✅ **New**: Dynamic content fetched from database (Categories + Products)

---

## 📋 How It Works

### 1. **Categories** (Horizontal Sections)
Each horizontal bar/section on the page represents a **Category** with:
- Icon (emoji or font-awesome)
- Title (Category name)
- Description (optional)
- Products (displayed in grid)

### 2. **Products** (Cards in Grid)
Each product card shows:
- Product image
- Name
- Short description
- Price (with optional discount)
- Stock status badge
- "مشاهده" (View) button

---

## 🔧 Admin Management

### Step 1: Create/Edit Categories

**Path**: Admin Panel → Products → Categories

**Settings**:
```
Name: تلگرام پرمیوم
Name (English): Telegram Premium
Category Type: خدمات مجازی (Virtual)
Parent: (Leave empty for top-level)
Icon: ✈️ (or Font Awesome class like "fa-telegram")
Description: اشتراک پرمیوم با تمام امکانات ویژه
Sort Order: 1 (lower numbers appear first)
Is Active: ✓ (checked)
```

**Important Fields**:
- **Category Type**: MUST be "خدمات مجازی" (Virtual)
- **Parent**: Must be empty (null) to show on virtual services page
- **Sort Order**: Controls the order of sections (1, 2, 3...)
- **Icon**: Emoji (✈️, 📸, 👥) or Font Awesome class
- **Is Active**: Must be checked to display

---

### Step 2: Add Products to Categories

**Path**: Admin Panel → Products → Products

**Settings**:
```
Name: تلگرام پرمیوم ۱ ماهه
Category: تلگرام پرمیوم (select from dropdown)
Product Type: خدمات مجازی (Virtual)
Price: 89000
Original Price: 100000 (optional - for showing discount)
Stock: 100
Short Description: بدون محدودیت دانلود، استیکرهای پرمیوم
Sort Order: 1
Is Active: ✓
```

**Product Images**:
- Add at least 1 image per product
- First image will be used as thumbnail
- Recommended size: 800x600px or 4:3 ratio

**Important**:
- Products will only show if **Is Active** is checked
- Products are ordered by **Sort Order**, then by creation date
- Maximum 12 products shown per category

---

## 📊 Display Logic

### Categories Shown When:
1. ✅ `category_type` = "خدمات مجازی" (VIRTUAL)
2. ✅ `parent` = null (top-level categories)
3. ✅ `is_active` = True
4. ✅ Has at least 1 active product

### Products Shown When:
1. ✅ `is_active` = True
2. ✅ Belongs to the category
3. ✅ First 12 products (ordered by `sort_order`, then `-created_at`)

### Stock Badges:
- 🟢 **"موجود" (Available)**: stock > 50
- 🟠 **"محدود" (Limited)**: 0 < stock ≤ 50
- 🔴 **"ناموجود" (Out of Stock)**: stock = 0

---

## 🎨 Page Structure

```
┌─ Hero Section ─────────────────┐
│   Title: خدمات مجازی           │
│   Subtitle: Description        │
└────────────────────────────────┘

┌─ Category 1: تلگرام پرمیوم ────┐
│  [Product 1] [Product 2] ...   │
└────────────────────────────────┘

┌─ Category 2: فالوور اینستاگرام ─┐
│  [Product 1] [Product 2] ...   │
└────────────────────────────────┘

... (more categories)
```

---

## 🚀 Quick Start Guide

### To Add a New Service Category:

1. **Go to**: Admin → Products → Categories → Add Category
2. **Fill in**:
   ```
   Name: اسپاتیفای
   Category Type: خدمات مجازی
   Icon: 🎵
   Description: موسیقی بدون محدودیت
   Sort Order: 5
   Is Active: ✓
   ```
3. **Save**

### To Add Products to the Category:

1. **Go to**: Admin → Products → Products → Add Product
2. **Fill in**:
   ```
   Name: اسپاتیفای ۱ ماهه
   Category: اسپاتیفای
   Product Type: خدمات مجازی
   Price: 35000
   Stock: 50
   Sort Order: 1
   Is Active: ✓
   ```
3. **Upload Images** (in Product Images section)
4. **Save**

### To Reorder Categories:

1. **Go to**: Admin → Products → Categories
2. **Edit** each category
3. **Change** the "Sort Order" field:
   - Category 1: Sort Order = 1
   - Category 2: Sort Order = 2
   - Category 3: Sort Order = 3
4. **Save** each

---

## 📝 Examples

### Example 1: Telegram Premium Category

**Category**:
- Name: `تلگرام پرمیوم`
- Icon: `✈️`
- Sort Order: `1`

**Products**:
1. تلگرام پرمیوم ۱ ماهه - Price: 89,000
2. تلگرام پرمیوم ۳ ماهه - Price: 240,000
3. تلگرام پرمیوم ۶ ماهه - Price: 427,000
4. تلگرام پرمیوم ۱۲ ماهه - Price: 748,000

### Example 2: Instagram Followers

**Category**:
- Name: `فالوور اینستاگرام`
- Icon: `📸`
- Sort Order: `2`

**Products**:
1. ۱,۰۰۰ فالوور - Price: 45,000
2. ۵,۰۰۰ فالوور - Price: 189,000
3. ۱۰,۰۰۰ فالوور - Price: 350,000

---

## 🔍 Troubleshooting

### Category not showing?
**Check**:
- ✓ Category Type = "خدمات مجازی"
- ✓ Parent = (empty/null)
- ✓ Is Active = checked
- ✓ Has at least 1 active product

### Product not showing?
**Check**:
- ✓ Product → Is Active = checked
- ✓ Product → Category is correct
- ✓ Product has at least 1 image
- ✓ Not more than 12 products in category (increase limit in code if needed)

### Wrong order?
**Fix**:
- Edit Category/Product
- Change "Sort Order" field (lower = first)
- Save

---

## 💡 Tips

1. **Use Emojis for Icons**: Simple and effective (✈️, 📸, 👥, 🍎, 🎵)
2. **Keep Names Short**: Product names should be concise for better display
3. **Add Images**: Always add product images (required for good UX)
4. **Use Sort Order**: Control exact positioning of categories and products
5. **Stock Management**: Update stock regularly to keep badges accurate
6. **Descriptions**: Short descriptions appear below product name (2 lines max)

---

## 🎨 Customization

### To Change Max Products Per Category:

**File**: `apps/core/views.py`  
**Line**: Find `.order_by('sort_order', '-created_at')[:12]`  
**Change**: Replace `12` with desired number

### To Change Grid Columns:

**File**: `templates/core/virtual_services.html`  
**Find**: `grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))`  
**Change**: Adjust `280px` to change card width

### To Add More Badge Colors:

**File**: `templates/core/virtual_services.html`  
**Section**: `.vs-product__badge` styles  
**Add**: New badge classes with different colors

---

## 📦 Database Schema

### Categories Table:
```sql
id, name, name_en, slug, parent_id, category_type, 
description, icon, is_active, sort_order, created_at
```

### Products Table:
```sql
id, name, name_en, slug, category_id, brand_id,
product_type, price, original_price, stock,
short_description, is_active, sort_order, created_at
```

---

## 🎯 Summary

**Before**: 992 lines of hard-coded HTML  
**After**: Dynamic content from database

**Admin Control**:
- ✅ Add/Edit/Delete categories
- ✅ Add/Edit/Delete products
- ✅ Change order anytime
- ✅ Enable/Disable items
- ✅ Update prices instantly
- ✅ Manage stock levels
- ✅ Upload/Change images

**No Code Changes Needed** - Everything managed through admin panel! 🎉

---

**Created**: December 16, 2025  
**Template**: `templates/core/virtual_services.html`  
**View**: `apps/core/views.py → virtual_services()`  
**Old Template**: Backed up as `virtual_services_old_hardcoded.html`
