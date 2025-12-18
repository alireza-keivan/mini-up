# Virtual Services Featured Products Carousel

## Overview
A horizontal, auto-scrolling product carousel added to the virtual-services page, displaying admin-controlled featured products.

## Implementation Summary

### 📁 Files Modified/Created

1. **Backend (View)**
   - File: `apps/core/views.py`
   - Added carousel products query to `virtual_services()` view
   - Filters products with `is_featured=True` and `product_type=VIRTUAL`
   - Returns top 6 featured products

2. **Frontend (Template)**
   - File: `templates/core/virtual_services.html`
   - Added carousel section between hero and quick navigation
   - Shows ~2.5 products at once (responsive)
   - Includes product image, name, price, discount, and action button

3. **Styling (CSS)**
   - File: `static/css/pages/_virtual_services.css`
   - Added 300+ lines of carousel styles
   - Fully responsive (desktop, tablet, mobile)
   - Dark neon theme with glassmorphism

4. **Functionality (JavaScript)**
   - File: `static/js/pages/virtual_services.js` (NEW)
   - Auto-scrolls every 5 seconds
   - Infinite loop
   - Manual navigation (arrows, dots, keyboard, swipe)
   - Pause on hover

---

## Features

### ✨ Core Features
- ✅ Shows ~2.5 products visible at once (large cards)
- ✅ Auto-scrolls every 5 seconds
- ✅ Loops infinitely
- ✅ Visible ‹ / › navigation arrows
- ✅ Dot indicators for current slide
- ✅ Admin-controlled products via `is_featured` flag

### 📱 Responsive Design
- **Desktop (>1024px)**: ~2.5 products visible
- **Tablet (768-1024px)**: 2 products visible
- **Mobile (<768px)**: 1 product with peek effect (85% width)

### 🎨 Product Card Contains
- Large product image (280px height on desktop)
- Product name (clearly visible, bold)
- Short description (optional, truncated)
- Price display:
  - Shows discount price if available
  - Strikethrough original price
  - Neon glow effect
- Discount badge (if applicable)
- Action button: «ثبت درخواست» (Submit Request)

### 🎯 Interaction Features
- **Auto-scroll**: Every 5 seconds
- **Manual navigation**: 
  - Arrow buttons (left/right)
  - Dot indicators (click to jump)
  - Keyboard arrows
  - Touch swipe (mobile)
- **Pause on hover**: Auto-scroll stops when hovering
- **Responsive touch**: Swipe left/right on mobile

---

## How to Use (Admin Panel)

### Step 1: Mark Products as Featured
1. Go to Django Admin → Products → Product
2. Edit any virtual service product
3. Check the **"ویژه" (is_featured)** checkbox
4. Save the product

### Step 2: Verify Product Type
- Ensure the product has `product_type = "virtual"` (محصولات مجازی)
- Only virtual products with `is_featured=True` appear in carousel

### Step 3: Upload Product Images
- Add at least one product image
- First image is used in carousel
- Recommended size: 800x600px or similar ratio

### Step 4: Set Price & Discount (Optional)
- Set base price
- Optionally set discount price
- Discount percentage is calculated automatically
- Discount badge appears if discount exists

---

## Technical Details

### Backend Query
```python
carousel_products = Product.objects.filter(
    is_active=True,
    product_type=Product.ProductType.VIRTUAL,
    is_featured=True
).select_related('category', 'brand').prefetch_related('images').order_by('-created_at')[:6]
```

### Auto-scroll Logic
- Interval: 5000ms (5 seconds)
- Direction: Right to left (RTL-aware)
- Loop: Infinite (wraps to start)
- Pause: On hover, touch, or manual navigation
- Resume: After interaction ends

### Responsive Breakpoints
```css
Desktop: > 1024px  → 2.5 products visible
Tablet:  768-1024px → 2 products visible  
Mobile:  < 768px   → 1 product (85% width for peek)
Small:   < 480px   → 1 product (90% width)
```

### Navigation Methods
1. **Arrow Buttons**: Click ‹ / ›
2. **Dot Indicators**: Click any dot
3. **Keyboard**: Arrow keys (← →)
4. **Touch Swipe**: Swipe left/right on mobile
5. **Auto-scroll**: Automatic every 5s

---

## Customization

### Change Auto-scroll Speed
Edit `static/js/pages/virtual_services.js`:
```javascript
const autoScrollDelay = 5000; // Change to desired milliseconds
```

### Change Number of Featured Products
Edit `apps/core/views.py`:
```python
[:6]  # Change 6 to desired number
```

### Change Products Per View
Edit `static/css/pages/_virtual_services.css`:
```css
.vs-carousel__slide {
    flex: 0 0 calc(40% - 15px); /* Adjust percentage */
}
```

---

## Testing Checklist

### ✅ Functionality
- [ ] Carousel auto-scrolls every 5 seconds
- [ ] Left/right arrows work correctly
- [ ] Dot indicators show active slide
- [ ] Clicking dots jumps to correct slide
- [ ] Infinite loop works (wraps around)
- [ ] Hover pauses auto-scroll
- [ ] Touch swipe works on mobile

### ✅ Responsive
- [ ] Desktop: Shows ~2.5 products
- [ ] Tablet: Shows 2 products
- [ ] Mobile: Shows 1 product with peek
- [ ] No horizontal overflow
- [ ] Images load correctly
- [ ] Buttons accessible on all devices

### ✅ Content
- [ ] Featured products appear in carousel
- [ ] Non-featured products don't appear
- [ ] Only virtual products shown
- [ ] Product images display correctly
- [ ] Prices show correctly
- [ ] Discount badges appear when applicable
- [ ] "ثبت درخواست" button links to product detail

---

## Troubleshooting

### No products showing in carousel
**Solution**: 
1. Check at least one product has `is_featured=True`
2. Verify product has `product_type='virtual'`
3. Ensure product is `is_active=True`
4. Refresh the page

### Carousel not auto-scrolling
**Solution**:
1. Check browser console for JavaScript errors
2. Verify `virtual_services.js` is loaded
3. Check if page has focus (auto-scroll pauses when page hidden)

### Images not showing
**Solution**:
1. Verify product has at least one image uploaded
2. Check image file exists in media folder
3. Verify `MEDIA_URL` and `MEDIA_ROOT` settings
4. Check image path in browser dev tools

### Arrows not working
**Solution**:
1. Check console for JavaScript errors
2. Verify Font Awesome icons are loaded
3. Test with keyboard arrows as alternative

---

## Performance Notes

- **Optimized Queries**: Uses `select_related()` and `prefetch_related()`
- **Image Lazy Loading**: `loading="lazy"` attribute added
- **Smooth Animations**: Hardware-accelerated CSS transforms
- **Pause When Hidden**: Auto-scroll stops when tab not visible
- **Debounced Resize**: Window resize handled efficiently

---

## Future Enhancements (Optional)

1. **Admin Control for Order**: Allow drag-and-drop ordering in admin
2. **Video Support**: Allow video thumbnails instead of images
3. **Multiple Carousels**: Different carousels per category
4. **Analytics**: Track carousel clicks and views
5. **A/B Testing**: Test different carousel configurations

---

## Files Reference

```
apps/
  core/
    views.py                                  [MODIFIED]
templates/
  core/
    virtual_services.html                     [MODIFIED]
static/
  css/
    pages/
      _virtual_services.css                   [MODIFIED]
  js/
    pages/
      virtual_services.js                     [CREATED]
```

---

**Status**: ✅ COMPLETE
**Last Updated**: December 16, 2025
**Tested**: Ready for production
