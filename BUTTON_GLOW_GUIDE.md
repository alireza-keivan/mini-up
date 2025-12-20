# راهنمای استفاده از دکمه‌های Glow در پروژه

## 📌 معرفی
استایل دکمه‌های Glow با افکت Blur و Gradient Border که برای تمام دکمه‌های پروژه قابل استفاده است.

---

## 🎨 ویژگی‌ها
- ✨ افکت Glow/Blur در hover
- 🌈 Gradient Border با رنگ‌های Neon Gaming Theme
- 🎯 سه نوع رنگ: پیش‌فرض، Pink، Cyan، Purple
- 📏 سه سایز: Small، Medium (پیش‌فرض)، Large
- 📱 Responsive و سازگار با موبایل

---

## 🚀 نحوه استفاده

### ساختار HTML اصلی:
```html
<div class="btn-glow-container">
    <button class="btn-glow">
        <i class="fas fa-icon"></i>
        متن دکمه
    </button>
</div>
```

### به عنوان لینک:
```html
<div class="btn-glow-container">
    <a href="#" class="btn-glow">
        <i class="fas fa-icon"></i>
        متن دکمه
    </a>
</div>
```

---

## 🎨 انواع رنگ

### 1. پیش‌فرض (Cyan + Purple + Pink):
```html
<div class="btn-glow-container">
    <button class="btn-glow">دکمه پیش‌فرض</button>
</div>
```

### 2. صورتی (Pink):
```html
<div class="btn-glow-container pink">
    <button class="btn-glow">دکمه صورتی</button>
</div>
```

### 3. آبی (Cyan):
```html
<div class="btn-glow-container cyan">
    <button class="btn-glow">دکمه آبی</button>
</div>
```

### 4. بنفش (Purple):
```html
<div class="btn-glow-container purple">
    <button class="btn-glow">دکمه بنفش</button>
</div>
```

---

## 📏 سایزها

### کوچک (Small):
```html
<div class="btn-glow-container small">
    <button class="btn-glow">دکمه کوچک</button>
</div>
```

### متوسط (پیش‌فرض):
```html
<div class="btn-glow-container">
    <button class="btn-glow">دکمه متوسط</button>
</div>
```

### بزرگ (Large):
```html
<div class="btn-glow-container large">
    <button class="btn-glow">دکمه بزرگ</button>
</div>
```

---

## 🔀 ترکیب رنگ و سایز

```html
<!-- دکمه کوچک آبی -->
<div class="btn-glow-container small cyan">
    <button class="btn-glow">ذخیره</button>
</div>

<!-- دکمه بزرگ صورتی -->
<div class="btn-glow-container large pink">
    <button class="btn-glow">خرید محصول</button>
</div>

<!-- دکمه متوسط بنفش -->
<div class="btn-glow-container purple">
    <button class="btn-glow">ادامه</button>
</div>
```

---

## 💡 نمونه‌های کاربردی

### دکمه افزودن به سبد خرید:
```html
<div class="btn-glow-container cyan">
    <button class="btn-glow">
        <i class="fas fa-shopping-cart"></i>
        افزودن به سبد خرید
    </button>
</div>
```

### دکمه پرداخت:
```html
<div class="btn-glow-container large pink">
    <button class="btn-glow">
        <i class="fas fa-credit-card"></i>
        پرداخت و ثبت سفارش
    </button>
</div>
```

### دکمه ورود:
```html
<div class="btn-glow-container purple">
    <a href="{% url 'accounts:login' %}" class="btn-glow">
        <i class="fas fa-sign-in-alt"></i>
        ورود / ثبت‌نام
    </a>
</div>
```

### دکمه حذف:
```html
<div class="btn-glow-container small pink">
    <button class="btn-glow" onclick="deleteItem()">
        <i class="fas fa-trash"></i>
        حذف
    </button>
</div>
```

---

## 🎯 مثال‌های واقعی در پروژه

### 1. در صفحه محصولات (Product Card):
```html
<div class="btn-glow-container cyan">
    <button class="btn-glow" onclick="addToCart({{ product.id }})">
        <i class="fas fa-cart-plus"></i>
        افزودن به سبد
    </button>
</div>
```

### 2. در صفحه checkout:
```html
<div class="btn-glow-container large pink">
    <button type="submit" class="btn-glow">
        <i class="fas fa-check-circle"></i>
        تایید و پرداخت
    </button>
</div>
```

### 3. در صفحه dashboard:
```html
<div class="btn-glow-container small purple">
    <button class="btn-glow" onclick="saveProfile()">
        <i class="fas fa-save"></i>
        ذخیره تغییرات
    </button>
</div>
```

### 4. در modal ها:
```html
<div class="btn-glow-container cyan">
    <button class="btn-glow" @click="closeModal()">
        <i class="fas fa-times"></i>
        بستن
    </button>
</div>
```

---

## ⚙️ کلاس‌های CSS

### Container Classes:
- `btn-glow-container` - کلاس اصلی (الزامی)
- `pink` - رنگ صورتی
- `cyan` - رنگ آبی
- `purple` - رنگ بنفش
- `small` - سایز کوچک
- `large` - سایز بزرگ

### Button Class:
- `btn-glow` - کلاس دکمه (الزامی)

---

## 🎨 رنگ‌های Gradient

| نوع | رنگ‌ها |
|-----|--------|
| **پیش‌فرض** | `#00f5ff` → `#bf00ff` → `#ff0055` |
| **Pink** | `#ff0055` → `#bf00ff` |
| **Cyan** | `#00f5ff` → `#00ff88` |
| **Purple** | `#bf00ff` → `#ff0055` |

---

## 📱 Responsive

دکمه‌ها به طور خودکار در موبایل responsive هستند و عرض 100% می‌گیرند.

---

## 🔧 نکات مهم

1. ✅ همیشه دکمه را داخل `btn-glow-container` قرار دهید
2. ✅ برای استفاده از آیکون، Font Awesome را اضافه کنید
3. ✅ می‌توانید با `button` یا `a` tag استفاده کنید
4. ✅ برای ترکیب رنگ و سایز، هر دو کلاس را اضافه کنید
5. ⚠️ از `inline styles` برای override کردن استفاده نکنید

---

## 📊 پیش‌نمایش زنده

فایل نمونه: `templates/examples/button-examples.html`

برای مشاهده تمام حالت‌های دکمه، این فایل را در مرورگر باز کنید.

---

## 🎯 به‌روزرسانی دکمه‌های فعلی

برای تبدیل دکمه‌های فعلی به استایل جدید:

### قبل:
```html
<button class="btn-neon">ثبت</button>
```

### بعد:
```html
<div class="btn-glow-container cyan">
    <button class="btn-glow">ثبت</button>
</div>
```

---

این استایل برای **تمام دکمه‌های پروژه** قابل استفاده است و با **تم Neon Gaming** کاملاً سازگار شده است.
