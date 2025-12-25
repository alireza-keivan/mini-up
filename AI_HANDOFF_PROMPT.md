# AI Agent Handoff Prompt - Mini-Up E-commerce Platform

## Project Overview

You are taking over development of **Mini-Up**, a Django-based e-commerce platform with a modern cyberpunk/neon design aesthetic. The platform is designed for Persian/Farsi users with full RTL support and Jalali (Persian) calendar integration.

**Critical Context**: This is an active production project with real database content. The owner (Alireza) has specific design preferences: clean, minimal neon accents without excessive colors, functional UI over flashy aesthetics.

## Technology Stack

### Backend
- **Django 4.2.26** - Main web framework
- **Python 3.10** - Running in virtual environment (`/home/alireza/Documents/mini-up/`)
- **SQLite** - Database (`db.sqlite3`)
- **Gunicorn** - ASGI/WSGI server

### Frontend
- **Tailwind CSS** - Utility-first CSS framework
- **jQuery** - Required for Persian datepicker
- **Font Awesome** - Icons
- **Persian libraries**:
  - `persian-datepicker` v1.2.0 - Jalali calendar widget
  - `persian-date` v1.1.0 - Date handling
  - Custom `jalali_tags` Django template tags

### Key Dependencies
```
Django==4.2.26
django-jazzmin - Admin interface
Pillow - Image handling
django-cors-headers
gunicorn
```

## Project Structure

```
mini-up/
├── apps/
│   ├── accounts/     # User authentication, profile, orders view
│   ├── products/     # Product catalog
│   ├── orders/       # Order management
│   ├── payments/     # Payment processing
│   ├── wallet/       # User wallet system
│   ├── coupons/      # Discount coupons
│   ├── consulting/   # Consulting services
│   └── content/      # CMS content
├── miniup/           # Main Django project settings
│   ├── settings.py
│   └── urls.py
├── templates/        # Global templates
│   ├── base.html
│   └── orders/
│       └── order_list.html  # ⚠️ RECENTLY COMPLETELY REWRITTEN
├── static/           # Static assets
├── media/            # User-uploaded content
├── manage.py
└── requirements.txt
```

## Critical Files - MUST READ

### 1. `/home/alireza/Documents/mini-up/templates/orders/order_list.html` (579 lines)
**STATUS**: ✅ Production-ready, recently completed major rewrite

**Purpose**: Display user's order history with filtering capabilities

**Key Features**:
- Modern neon table design (not cards)
- 6 columns: Counter (#), Product Image, Date (Jalali), Status, Price, Profit
- Persian date range filtering with Jalali calendar widget
- Status filtering with 5 simplified categories
- Conditional "clear filters" button (red trash icon)
- Summary box showing: total orders, payment amount, items count, discount total
- Green checkmark icon for shipped orders
- All text in Farsi/Persian (RTL)

**Important Implementation Details**:
```django
<!-- Status filter uses comma-separated values for grouping -->
<option value="delivered,shipped,completed">تحویل داده شده</option>
<option value="processing,confirmed,preparing">در حال پردازش</option>

<!-- Clear button only appears when filters are active -->
{% if request.GET.status or request.GET.date_from or request.GET.date_to %}
    <a href="{% url 'orders:order_list' %}" class="clear-filters-btn">
        <i class="fas fa-trash-alt"></i>
    </a>
{% endif %}

<!-- Date inputs use text type (not HTML5 date) for Persian calendar -->
<input type="text" name="date_from" class="filter-select persian-date" 
       placeholder="۱۴۰۰/۰۱/۰۱">

<!-- Shipped status shows green checkmark -->
{% if order.status == 'shipped' %}
    <i class="fas fa-check-circle status-icon"></i>
{% endif %}
```

**Design Constraints**:
- ❌ NO gradient fills on buttons (transparent background only)
- ❌ NO colorful badges for status (white text only)
- ✅ Subtle neon borders (#bf00ff purple, #ff0055 pink, #00f5ff cyan)
- ✅ White text (#fff) for all data
- ✅ Red (#f44336) for destructive actions only
- ✅ Image hover: simple 1.05x scale, no border glow

### 2. `/home/alireza/Documents/mini-up/apps/accounts/views.py` (OrdersView class)
**STATUS**: ✅ Enhanced with comma-separated status filtering

**Key Logic**:
```python
class OrdersView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    
    def get_queryset(self):
        orders = Order.objects.filter(user=self.request.user).order_by('-created_at')
        
        # Handle multiple statuses separated by comma
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            if ',' in status_filter:
                statuses = [s.strip() for s in status_filter.split(',')]
                orders = orders.filter(status__in=statuses)
            else:
                orders = orders.filter(status=status_filter)
        
        # Date filtering (if implemented)
        # date_from = self.request.GET.get('date_from')
        # date_to = self.request.GET.get('date_to')
        
        return orders
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = context['orders']
        
        context['total_amount'] = orders.aggregate(
            total=Sum('total')
        )['total'] or 0
        
        context['total_discount'] = orders.aggregate(
            total=Sum('discount_amount')
        )['total'] or 0
        
        context['total_items'] = OrderItem.objects.filter(
            order__in=orders
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        return context
```

**⚠️ IMPORTANT**: The backend currently does NOT convert Persian dates to Gregorian. If date filtering needs to work, you must:
1. Capture Persian date from form (YYYY/MM/DD format)
2. Convert to Gregorian using `jdatetime` or similar
3. Filter queryset by converted dates

### 3. `/home/alireza/Documents/mini-up/apps/core/templatetags/jalali_tags.py`
**STATUS**: ✅ Working custom template tags

**Purpose**: Convert Gregorian dates to Persian/Jalali format

**Usage**:
```django
{% load jalali_tags %}
{{ order.created_at|jalali:"%Y/%m/%d" }}  <!-- 1403/09/24 -->
{{ order.created_at|jalali:"%H:%M" }}     <!-- 14:30 -->
```

### 4. Order Model Structure

**Location**: `apps/orders/models.py`

**Key Fields**:
```python
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('processing', 'در حال پردازش'),
        ('confirmed', 'تایید شده'),
        ('preparing', 'در حال آماده‌سازی'),
        ('shipped', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
        ('completed', 'تکمیل شده'),
        ('cancelled', 'لغو شده'),
        ('refunded', 'برگشت وجه'),
        ('failed', 'ناموفق'),
    ]
    
    user = ForeignKey(User)
    order_number = CharField(unique=True)  # Format: ORD-YYYYMMDD-XXXX
    status = CharField(choices=STATUS_CHOICES, default='pending')
    total = DecimalField()
    discount_amount = DecimalField(default=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    paid_at = DateTimeField(null=True, blank=True)
    
    @property
    def is_paid(self):
        return self.paid_at is not None
```

**OrderItem Model**:
```python
class OrderItem(models.Model):
    order = ForeignKey(Order)
    product = ForeignKey(Product)
    quantity = IntegerField()
    unit_price = DecimalField()        # ⚠️ NOT 'price'
    original_price = DecimalField()    # ⚠️ NOT 'product_price'
    total_price = DecimalField()       # ⚠️ NOT 'total'
    discount_amount = DecimalField()
```

### 5. `/home/alireza/Documents/mini-up/populate_orders.py`
**STATUS**: ✅ Working test data generator

**Purpose**: Generate sample orders for testing

**Usage**:
```bash
cd /home/alireza/Documents/mini-up
./bin/python populate_orders.py
```

**Important Notes**:
- Creates exactly 10 orders with varied statuses
- Uses `timezone.now()` for timezone-aware dates (NOT `datetime.now()`)
- Django settings: `miniup.settings` (NOT `miniup.settings.development`)
- OrderItem uses: `unit_price`, `original_price`, `total_price` (check model for exact field names)

## Design System & Constraints

### Color Palette
```css
/* Primary Neon Colors */
--purple: #bf00ff;    /* Main accent */
--pink: #ff0055;      /* Secondary accent */
--cyan: #00f5ff;      /* Labels and highlights */
--green: #4caf50;     /* Success states (shipped icon) */
--red: #f44336;       /* Destructive actions (delete/clear) */

/* Neutrals */
--white: #fff;        /* All data text */
--dark: #0a0a0a;      /* Background base */
--gray: rgba(255, 255, 255, 0.7);  /* Secondary text */
```

### Design Principles (CRITICAL - Owner's Preferences)

✅ **DO**:
- Use transparent backgrounds with colored borders
- Keep text white (#fff) for readability
- Use subtle neon glows on hover (0.4 opacity)
- Maintain RTL layout for Farsi text
- Scale effects on hover (1.05x max)
- Functional, clean interfaces

❌ **DON'T**:
- Use gradient fills on buttons
- Make colorful badges for status
- Over-use neon effects
- Create "flashy" or "busy" designs
- Use English text where Farsi is appropriate
- Add unnecessary animations

### Button Pattern
```css
.button-standard {
    background: transparent;
    border: 2px solid #bf00ff;
    color: #fff;
    padding: 0.5rem 1rem;
    transition: all 0.3s ease;
}

.button-standard:hover {
    box-shadow: 0 0 15px rgba(191, 0, 255, 0.4);
}
```

## Recent Major Changes (Dec 24, 2025)

### Orders Page Complete Rewrite
**Status**: ✅ COMPLETED

**What Changed**:
1. **Layout**: Card-based → Table-based
2. **Columns**: Reorganized to Counter, Image, Date, Status, Price, Profit
3. **Filters**: 
   - Status: 10 options → 5 grouped categories
   - Date: HTML5 date input → Persian text input with calendar
   - Added conditional clear button
4. **Styling**: Colorful gradients → Clean white text with minimal borders
5. **Icons**: Added green checkmark for shipped status
6. **Backend**: Enhanced to handle comma-separated status filtering

**Files Modified**:
- `templates/orders/order_list.html` - Complete rewrite (579 lines)
- `apps/accounts/views.py` - OrdersView enhanced with comma splitting
- `populate_orders.py` - Fixed multiple bugs, now working

**Testing Status**: ✅ All features verified working with 18 orders displayed

## Known Issues & Pending Work

### ⚠️ Date Filtering Backend NOT Implemented
**Problem**: Template accepts Persian dates but backend doesn't convert them to Gregorian for filtering

**Solution Needed**:
```python
# In OrdersView.get_queryset()
from jdatetime import datetime as jdatetime

date_from = self.request.GET.get('date_from')  # Format: YYYY/MM/DD (Persian)
if date_from:
    # Convert Persian to Gregorian
    parts = date_from.split('/')
    j_date = jdatetime(int(parts[0]), int(parts[1]), int(parts[2]))
    g_date = j_date.togregorian()
    orders = orders.filter(created_at__date__gte=g_date)
```

### ⚠️ Product Detail Links
**Current State**: Image links use `#` placeholder

**Location**: `templates/orders/order_list.html` line ~327
```django
<a href="#" class="product-link">  <!-- ⚠️ PLACEHOLDER -->
```

**Fix Needed**: Replace with actual product detail URL
```django
<a href="{% url 'products:detail' order.items.first.product.slug %}" class="product-link">
```

### 💡 Failed Orders
**Context**: Owner mentioned failed orders should be handled via notifications, not shown in order list

**Current State**: 'failed' status exists but removed from filter options

**Pending**: Notification system implementation (not started)

## URLs & Routes

**Main URLs** (`miniup/urls.py`):
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('orders/', include('apps.orders.urls')),
    path('products/', include('apps.products.urls')),
    # ... other apps
]
```

**Orders URLs** (`apps/orders/urls.py`):
```python
app_name = 'orders'
urlpatterns = [
    path('', OrdersView.as_view(), name='order_list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
]
```

**Current Working URL**: http://127.0.0.1:8000/orders/

## Running the Project

### Development Server
```bash
cd /home/alireza/Documents/mini-up
source bin/activate  # Or: . bin/activate
python manage.py runserver
```

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Create Test Data
```bash
python populate_orders.py  # Creates 10 sample orders
```

### Admin Access
```bash
python manage.py createsuperuser
# Then: http://127.0.0.1:8000/admin/
```

## Database State

**Current Orders**: 18 total (10 from script + 8 existing)

**Status Distribution**:
- Processing: 3
- Delivered: 3
- Cancelled: 2
- Confirmed: 1
- Shipped: 7+

**User Model**: Includes Google OAuth and phone number authentication

## Django Apps Structure

### apps/accounts
- User authentication (Google OAuth, phone)
- User profile management
- **OrdersView** (order history page)

### apps/orders
- Order model and management
- OrderItem model
- Order status workflow

### apps/products
- Product catalog
- Categories
- Images

### apps/payments
- Payment gateway integration
- Transaction handling

### apps/wallet
- User wallet system
- Wallet transactions

### apps/coupons
- Discount coupon system

## Important Commands for Reference

### Running Django Shell
```bash
cd /home/alireza/Documents/mini-up
./bin/python manage.py shell
```

### Quick Order Query
```python
from apps.orders.models import Order
orders = Order.objects.all()
print(f"Total orders: {orders.count()}")
```

### Template Tag Testing
```bash
./bin/python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miniup.settings')
django.setup()
from apps.core.templatetags.jalali_tags import jalali
from django.utils import timezone
print(jalali(timezone.now(), '%Y/%m/%d'))
"
```

## Communication Guidelines with Alireza

1. **Design Decisions**: Always confirm major UI changes before implementing
2. **Persian/Farsi**: Use Farsi text in user-facing features, English in code/comments
3. **Simplicity**: When in doubt, choose simpler, cleaner design over complex
4. **Testing**: Verify all changes with actual data (use populate script if needed)
5. **Documentation**: Update markdown files when making significant changes

## Next Steps (Recommended Priority)

1. **HIGH**: Implement Persian to Gregorian date conversion in OrdersView
2. **MEDIUM**: Fix product detail links (replace `#` placeholder)
3. **MEDIUM**: Create product detail page if it doesn't exist
4. **LOW**: Implement notification system for failed orders
5. **LOW**: Add pagination to orders table if count > 50

## File Reading Checklist

Before making ANY changes, you MUST read these files in full:

- [ ] `/home/alireza/Documents/mini-up/templates/orders/order_list.html`
- [ ] `/home/alireza/Documents/mini-up/apps/accounts/views.py` (OrdersView)
- [ ] `/home/alireza/Documents/mini-up/apps/orders/models.py`
- [ ] `/home/alireza/Documents/mini-up/apps/core/templatetags/jalali_tags.py`
- [ ] `/home/alireza/Documents/mini-up/miniup/settings.py`
- [ ] `/home/alireza/Documents/mini-up/miniup/urls.py`

## Critical Warnings

⚠️ **DO NOT**:
- Delete or truncate `db.sqlite3` (contains production data)
- Change field names in models without migrations
- Remove timezone awareness from datetime operations
- Use `datetime.now()` instead of `timezone.now()`
- Modify the status consolidation logic without discussing with owner
- Change the neon color scheme (#bf00ff, #ff0055, #00f5ff)
- Add colorful gradients or fills to buttons

⚠️ **ALWAYS**:
- Test with real orders (use populate script)
- Verify Persian calendar widget works after changes
- Check RTL layout rendering
- Run `python manage.py check` before committing
- Keep design minimal and functional
- Use exact field names from models

## Summary

This is a well-structured Django e-commerce platform with a recent complete overhaul of the orders page. The owner values clean, functional design with subtle neon accents over flashy aesthetics. All user-facing content is in Farsi with RTL support and Jalali calendar integration. The orders page is production-ready with working filters, Persian dates, and grouped status options. Main pending items are date conversion backend logic and product detail page integration.

**Project Health**: ✅ Stable, production-ready
**Last Major Work**: Orders page complete rewrite (Dec 24, 2025)
**Current Focus**: Backend enhancements and remaining integrations

---

**Agent Handoff Complete** - You have full context to continue development. Read all critical files before making changes. When in doubt about design, choose simplicity.
