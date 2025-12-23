# Neon Product Card Component Implementation

## Overview
This implementation provides a **neon-themed product card design** with precise proportions matching the Figma mockup. The card follows a modern, cyberpunk aesthetic with glowing borders and smooth animations.

## Card Specifications

### Proportions
- **Total Card Ratio**: `2:1` (height to width)
- **Image Section**: `1:1` (square aspect ratio - top half)
- **Content Section**: `1:1` (same height as image - bottom half)

### Visual Design
- Dark background with backdrop blur effect
- Neon-colored borders with glow effects
- Smooth hover animations (lift effect + enhanced glow)
- Gradient overlay on images
- Responsive design (mobile to desktop)

## Neon Color Options

The card supports **4 neon color themes**:

| Color  | Border Color | Shadow Color | Use Case |
|--------|-------------|--------------|----------|
| `cyan` | #22d3ee (Cyan-400) | rgba(34,211,238,0.5) | Gaming peripherals, tech gadgets |
| `pink` | #f472b6 (Pink-400) | rgba(244,114,182,0.5) | Premium products, highlighted items |
| `purple` | #c084fc (Purple-400) | rgba(192,132,252,0.5) | Smart devices, wearables |
| `green` | #4ade80 (Green-400) | rgba(74,222,128,0.5) | Audio products, eco-friendly items |

## File Structure

```
mini-up/
├── templates/
│   ├── components/
│   │   └── neon_product_card.html      # Reusable card component
│   └── core/
│       └── neon_products_demo.html     # Demo page showcasing cards
└── apps/
    └── core/
        ├── views.py                     # View logic (neon_products_demo)
        └── urls.py                      # URL routing
```

## Usage

### Basic Usage
Include the component in any template:

```django
{% include 'components/neon_product_card.html' with product=product neon_color='cyan' %}
```

### In a Grid Layout
```django
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    {% for product in products %}
        {% cycle 'cyan' 'pink' 'purple' 'green' as neon_colors silent %}
        {% include 'components/neon_product_card.html' with product=product neon_color=neon_colors %}
    {% endfor %}
</div>
```

### Required Product Model Fields
The component expects the following fields on the `product` object:

- `id` - Product ID
- `slug` - URL slug for product detail page
- `name` - Product title
- `description` - Product description (optional, has default)
- `price` - Original price (uses `intcomma` filter)
- `final_price` - Price after discount (if applicable)
- `discount_percent` - Discount percentage (0 if no discount)
- `stock` - Available quantity (>0 shows "Add to Cart", <=0 shows "Out of Stock")
- `rating` - Star rating (1-5, defaults to 5)
- `primary_image` - Main product image (optional, shows placeholder if missing)
  - `primary_image.url` - Image URL

## Component Features

### 1. **Image Section** (1:1 aspect ratio)
- Square product image with zoom effect on hover
- Gradient overlay for better text contrast
- Wishlist/Like button in top-right corner
- Responsive image loading with `loading="lazy"`
- Fallback placeholder for missing images

### 2. **Content Section** (1:1 aspect ratio)
- **Star Rating** - 5-star display with neon-colored active stars
- **Product Title** - 2-line clamp with hover underline effect
- **Description** - 2-line clamp with gray text
- **Price Display**:
  - Shows strikethrough original price if discounted
  - Neon-colored final price
  - "تومان" currency suffix
- **Add to Cart Button**:
  - Neon-styled with matching color
  - Shopping cart icon
  - Disabled state for out-of-stock products

### 3. **Interactive Elements**
- **Hover Effects**:
  - Card lifts up 8px (`translateY(-8px)`)
  - Glow shadow intensifies
  - Image zooms in (scale 110%)
- **Wishlist Button**:
  - Click to toggle favorite
  - Smooth fill animation
- **Add to Cart**:
  - Data attribute for JavaScript integration: `data-add-cart="{{ product.id }}"`

## Demo Page

### Access
Visit: **http://localhost:8000/neon-demo/**

### Features
- Displays 4+ products in neon grid
- Animated gradient title
- Instructions panel explaining proportions
- Responsive grid (1 column mobile → 4 columns desktop)
- JavaScript functionality for cart and wishlist

### View Code
```python
# apps/core/views.py
def neon_products_demo(request):
    """Demo page for neon-themed product cards"""
    from apps.products.models import Product
    
    products = Product.objects.filter(
        is_active=True
    ).select_related('category', 'brand')[:8]
    
    return render(request, 'core/neon_products_demo.html', {
        'title': 'نمایش کارت‌های نئون',
        'products': products,
    })
```

## Integration with Existing Pages

### Gaming Products Page
Replace existing cards in `templates/core/gaming_products.html`:

```django
<!-- OLD: Lines 556-800 -->
<article class="gp-product-card ...">
    ...
</article>

<!-- NEW: Single line replacement -->
{% include 'components/neon_product_card.html' with product=product neon_color='cyan' %}
```

### Category Pages
```django
{% for product in products %}
    {% include 'components/neon_product_card.html' with product=product neon_color='purple' %}
{% endfor %}
```

### Search Results
```django
{% for product in search_results %}
    {% include 'components/neon_product_card.html' with product=product neon_color='pink' %}
{% endfor %}
```

## Customization

### Change Card Width
The component uses `aspect-square` utility, so width determines height automatically:

```django
<div class="w-72">  <!-- 288px width = 576px height (2:1) -->
    {% include 'components/neon_product_card.html' with product=product neon_color='cyan' %}
</div>
```

### Add Custom Classes
Wrap the include in a div:

```django
<div class="custom-wrapper">
    {% include 'components/neon_product_card.html' with product=product neon_color='green' %}
</div>
```

### Modify Neon Colors
Edit `templates/components/neon_product_card.html` to add new colors:

```django
{% elif neon_color == 'orange' %}border-orange-400 shadow-[0_0_15px_rgba(251,146,60,0.5)]
```

## Responsive Behavior

| Breakpoint | Grid Columns | Card Width |
|------------|-------------|------------|
| Mobile (< 768px) | 1 column | 100% width |
| Tablet (768px - 1023px) | 2 columns | ~50% width |
| Desktop (≥ 1024px) | 4 columns | ~25% width |

The card automatically maintains 2:1 proportions at all sizes thanks to `aspect-square` classes.

## Browser Compatibility
- ✅ Chrome 90+ (full support)
- ✅ Firefox 88+ (full support)
- ✅ Safari 14+ (full support)
- ✅ Edge 90+ (full support)
- ⚠️ IE11 (limited support - no backdrop-blur, reduced shadows)

## Performance Tips
1. **Lazy Loading**: Images use `loading="lazy"` by default
2. **Optimized Images**: Ensure product images are properly compressed
3. **CSS**: All styles use Tailwind utilities (no custom CSS needed)
4. **JavaScript**: Minimal JS, only for interactivity

## Next Steps

### To Apply to Production:
1. ✅ Component created: `templates/components/neon_product_card.html`
2. ✅ Demo page created: `templates/core/neon_products_demo.html`
3. ⏳ **Replace existing cards** in gaming_products.html
4. ⏳ **Add to other product listings** (category pages, search, favorites)
5. ⏳ **Test on mobile devices**
6. ⏳ **Integrate JavaScript** for real cart/wishlist functionality
7. ⏳ **Commit to repository** (when ready)

### To Test:
```bash
# Run development server
python manage.py runserver

# Visit demo page
# http://localhost:8000/neon-demo/

# Test responsiveness
# - Resize browser window
# - Check mobile view (Chrome DevTools)
# - Test all 4 color variants
```

## JavaScript Integration

The demo includes basic JavaScript for cart and wishlist. For production, integrate with your existing cart system:

```javascript
// Add to cart
document.querySelectorAll('[data-add-cart]').forEach(button => {
    button.addEventListener('click', function(e) {
        e.preventDefault();
        const productId = this.dataset.addCart;
        
        // Your cart logic here
        fetch(`/cart/add/${productId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            }
        }).then(response => {
            // Handle success
        });
    });
});
```

## Support
For questions or modifications, refer to:
- Figma design: Neon Tech Store mockup
- Tailwind docs: https://tailwindcss.com/docs
- Django templates: https://docs.djangoproject.com/en/4.2/topics/templates/

---

**Created**: December 21, 2025  
**Status**: ✅ Ready for testing (NOT pushed to git)  
**Demo URL**: http://localhost:8000/neon-demo/
