/**
 * Persian Number Utilities
 * تبدیل اعداد انگلیسی به فارسی
 */

// نقشه تبدیل اعداد
const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
const englishDigits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];

/**
 * تبدیل اعداد انگلیسی به فارسی
 * @param {string|number} input - عدد یا رشته ورودی
 * @returns {string} - رشته با اعداد فارسی
 */
function toPersianNumber(input) {
    if (input == null || input === '') return '';
    
    const str = input.toString();
    return str.replace(/[0-9]/g, (digit) => persianDigits[parseInt(digit)]);
}

/**
 * تبدیل اعداد فارسی به انگلیسی
 * @param {string} input - رشته با اعداد فارسی
 * @returns {string} - رشته با اعداد انگلیسی
 */
function toEnglishNumber(input) {
    if (input == null || input === '') return '';
    
    let str = input.toString();
    persianDigits.forEach((persian, index) => {
        str = str.replace(new RegExp(persian, 'g'), englishDigits[index]);
    });
    return str;
}

/**
 * فرمت کردن قیمت با جداکننده و تبدیل به فارسی
 * @param {number} price - قیمت
 * @returns {string} - قیمت فرمت شده به فارسی
 */
function formatPersianPrice(price) {
    if (price == null || isNaN(price)) return '۰';
    
    const formatted = new Intl.NumberFormat('en-US').format(price);
    return toPersianNumber(formatted);
}

/**
 * فرمت کردن قیمت با واحد پول
 * @param {number} price - قیمت
 * @param {string} currency - واحد پول (پیش‌فرض: تومان)
 * @returns {string} - قیمت فرمت شده با واحد
 */
function formatPersianCurrency(price, currency = 'تومان') {
    const formattedPrice = formatPersianPrice(price);
    return `${formattedPrice} ${currency}`;
}

/**
 * تبدیل تمام اعداد در یک المنت HTML به فارسی
 * @param {HTMLElement} element - المنت هدف
 */
function convertElementNumbers(element) {
    if (!element) return;
    
    // Skip script and style elements
    if (element.tagName === 'SCRIPT' || element.tagName === 'STYLE') return;
    
    // تبدیل محتوای متنی
    const walker = document.createTreeWalker(
        element,
        NodeFilter.SHOW_TEXT,
        {
            acceptNode: function(node) {
                // Skip if parent is script or style
                if (node.parentElement && 
                    (node.parentElement.tagName === 'SCRIPT' || 
                     node.parentElement.tagName === 'STYLE')) {
                    return NodeFilter.FILTER_REJECT;
                }
                return NodeFilter.FILTER_ACCEPT;
            }
        },
        false
    );
    
    let node;
    while (node = walker.nextNode()) {
        if (node.nodeValue && /\d/.test(node.nodeValue)) {
            node.nodeValue = toPersianNumber(node.nodeValue);
        }
    }
    
    // تبدیل ویژگی‌های خاص
    const attributes = ['value', 'placeholder', 'title', 'alt', 'data-value'];
    const elements = element.querySelectorAll ? element.querySelectorAll('*') : [];
    Array.from(elements).forEach(el => {
        attributes.forEach(attr => {
            if (el.hasAttribute(attr)) {
                const value = el.getAttribute(attr);
                if (value && /\d/.test(value)) {
                    el.setAttribute(attr, toPersianNumber(value));
                }
            }
        });
    });
}

/**
 * تبدیل خودکار اعداد در کل صفحه
 */
function autoConvertPageNumbers() {
    // تبدیل body
    convertElementNumbers(document.body);
}

/**
 * افزودن event listener برای تبدیل خودکار
 */
if (typeof window !== 'undefined') {
    // تبدیل اعداد بعد از لود شدن DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoConvertPageNumbers);
    } else {
        autoConvertPageNumbers();
    }
    
    // MutationObserver برای تبدیل محتوای دینامیک
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    // Skip script and style elements
                    if (node.tagName !== 'SCRIPT' && node.tagName !== 'STYLE') {
                        convertElementNumbers(node);
                    }
                } else if (node.nodeType === Node.TEXT_NODE && node.nodeValue && /\d/.test(node.nodeValue)) {
                    // Skip if parent is script or style
                    if (node.parentElement && 
                        node.parentElement.tagName !== 'SCRIPT' && 
                        node.parentElement.tagName !== 'STYLE') {
                        node.nodeValue = toPersianNumber(node.nodeValue);
                    }
                }
            });
        });
    });
    
    // شروع مشاهده تغییرات
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        });
    } else {
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        toPersianNumber,
        toEnglishNumber,
        formatPersianPrice,
        formatPersianCurrency,
        convertElementNumbers,
        autoConvertPageNumbers
    };
}
