/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * MINI-UP.IR - Gaming Products Page JavaScript
 * Version: 1.0.0
 * Theme: Neon Dark RTL
 * ═══════════════════════════════════════════════════════════════════════════════
 */

(function() {
    'use strict';

    // ═══════════════════════════════════════════════════════════════════════════
    // CONFIGURATION
    // ═══════════════════════════════════════════════════════════════════════════

    const CONFIG = {
        // API Endpoints
        api: {
            addToCart: '/api/cart/add/',
            toggleWishlist: '/api/wishlist/toggle/',
            notifyStock: '/api/notify-stock/',
        },
        // Animation Durations
        animation: {
            toast: 3000,
            modalTransition: 300,
            scrollSmooth: 500,
        },
        // Carousel Settings
        carousel: {
            dragThreshold: 50,
            wheelMultiplier: 2,
            arrowScrollAmount: 300,
        },
        // Selectors
        selectors: {
            carousel: '.gp-carousel',
            carouselWrapper: '.gp-carousel-wrapper',
            card: '.gp-card',
            categoryNav: '.gp-category-nav',
            categoryLink: '.gp-category-link',
            section: '.gp-category-section',
            modal: '#gp-quick-view-modal',
            modalOverlay: '#gp-modal-overlay',
            toastContainer: '.gp-toast-container',
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // UTILITY FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════

    const Utils = {
        /**
         * Get CSRF Token from cookies
         */
        getCSRFToken() {
            const name = 'csrftoken';
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },

        /**
         * Format price with Persian numerals and separators
         */
        formatPrice(price) {
            if (!price && price !== 0) return '—';
            const formatted = price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
            // Convert to Persian numerals (optional)
            const persianNumerals = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
            // return formatted.replace(/[0-9]/g, d => persianNumerals[d]);
            return formatted;
        },

        /**
         * Debounce function
         */
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        /**
         * Throttle function
         */
        throttle(func, limit) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        /**
         * Check if element is in viewport
         */
        isInViewport(element) {
            const rect = element.getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.right <= (window.innerWidth || document.documentElement.clientWidth)
            );
        },

        /**
         * Smooth scroll to element
         */
        scrollToElement(element, offset = 100) {
            const elementPosition = element.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - offset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // TOAST NOTIFICATION SYSTEM
    // ═══════════════════════════════════════════════════════════════════════════

    const Toast = {
        container: null,

        init() {
            // Create container if not exists
            this.container = document.querySelector(CONFIG.selectors.toastContainer);
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.className = 'gp-toast-container';
                document.body.appendChild(this.container);
            }
        },

        show(message, type = 'info') {
            if (!this.container) this.init();

            const toast = document.createElement('div');
            toast.className = `gp-toast gp-toast-${type}`;
            
            // Icon based on type
            const icons = {
                success: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
                error: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
                warning: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
                info: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
            };

            toast.innerHTML = `
                <span class="gp-toast-icon">${icons[type] || icons.info}</span>
                <span class="gp-toast-message">${message}</span>
            `;

            this.container.appendChild(toast);

            // Auto remove
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => toast.remove(), 300);
            }, CONFIG.animation.toast);
        },

        success(message) {
            this.show(message, 'success');
        },

        error(message) {
            this.show(message, 'error');
        },

        warning(message) {
            this.show(message, 'warning');
        },

        info(message) {
            this.show(message, 'info');
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // CAROUSEL HANDLER
    // ═══════════════════════════════════════════════════════════════════════════

    const Carousel = {
        instances: [],

        init() {
            const carousels = document.querySelectorAll(CONFIG.selectors.carousel);
            carousels.forEach((carousel, index) => {
                this.setupCarousel(carousel, index);
            });
        },

        setupCarousel(carousel, index) {
            const wrapper = carousel.closest(CONFIG.selectors.carouselWrapper);
            if (!wrapper) return;

            const prevBtn = wrapper.querySelector('.gp-carousel-arrow--prev');
            const nextBtn = wrapper.querySelector('.gp-carousel-arrow--next');

            const state = {
                isDragging: false,
                startX: 0,
                scrollLeft: 0,
                velocity: 0,
                lastX: 0,
                lastTime: 0
            };

            // ─────────────────────────────────────────────────────────────────
            // Mouse Drag Scroll
            // ─────────────────────────────────────────────────────────────────

            carousel.addEventListener('mousedown', (e) => {
                state.isDragging = true;
                carousel.classList.add('is-dragging');
                state.startX = e.pageX - carousel.offsetLeft;
                state.scrollLeft = carousel.scrollLeft;
                state.lastX = e.pageX;
                state.lastTime = Date.now();
            });

            carousel.addEventListener('mouseleave', () => {
                if (state.isDragging) {
                    state.isDragging = false;
                    carousel.classList.remove('is-dragging');
                }
            });

            carousel.addEventListener('mouseup', (e) => {
                state.isDragging = false;
                carousel.classList.remove('is-dragging');
                
                // Momentum scrolling
                const timeDiff = Date.now() - state.lastTime;
                if (timeDiff < 100) {
                    const distance = e.pageX - state.lastX;
                    const velocity = distance / timeDiff;
                    carousel.scrollBy({
                        left: -velocity * 150,
                        behavior: 'smooth'
                    });
                }
            });

            carousel.addEventListener('mousemove', (e) => {
                if (!state.isDragging) return;
                e.preventDefault();
                const x = e.pageX - carousel.offsetLeft;
                const walk = (x - state.startX) * 1.5;
                carousel.scrollLeft = state.scrollLeft - walk;
            });

            // ─────────────────────────────────────────────────────────────────
            // Touch Scroll (Mobile)
            // ─────────────────────────────────────────────────────────────────

            carousel.addEventListener('touchstart', (e) => {
                state.isDragging = true;
                state.startX = e.touches[0].pageX - carousel.offsetLeft;
                state.scrollLeft = carousel.scrollLeft;
            }, { passive: true });

            carousel.addEventListener('touchend', () => {
                state.isDragging = false;
            });

            carousel.addEventListener('touchmove', (e) => {
                if (!state.isDragging) return;
                const x = e.touches[0].pageX - carousel.offsetLeft;
                const walk = (x - state.startX) * 1.5;
                carousel.scrollLeft = state.scrollLeft - walk;
            }, { passive: true });

            // ─────────────────────────────────────────────────────────────────
            // Mouse Wheel Horizontal Scroll
            // ─────────────────────────────────────────────────────────────────

            carousel.addEventListener('wheel', (e) => {
                if (Math.abs(e.deltaY) < Math.abs(e.deltaX)) return;
                
                e.preventDefault();
                carousel.scrollBy({
                    left: e.deltaY * CONFIG.carousel.wheelMultiplier,
                    behavior: 'auto'
                });
            }, { passive: false });

            // ─────────────────────────────────────────────────────────────────
            // Arrow Buttons
            // ─────────────────────────────────────────────────────────────────

            if (prevBtn) {
                prevBtn.addEventListener('click', () => {
                    carousel.scrollBy({
                        left: CONFIG.carousel.arrowScrollAmount,
                        behavior: 'smooth'
                    });
                });
            }

            if (nextBtn) {
                nextBtn.addEventListener('click', () => {
                    carousel.scrollBy({
                        left: -CONFIG.carousel.arrowScrollAmount,
                        behavior: 'smooth'
                    });
                });
            }

            // ─────────────────────────────────────────────────────────────────
            // Update Arrow States
            // ─────────────────────────────────────────────────────────────────

            const updateArrows = () => {
                if (!prevBtn || !nextBtn) return;
                
                const isAtStart = carousel.scrollLeft <= 10;
                const isAtEnd = carousel.scrollLeft >= carousel.scrollWidth - carousel.clientWidth - 10;

                // RTL direction - arrows are reversed
                prevBtn.disabled = isAtEnd;
                nextBtn.disabled = isAtStart;
            };

            carousel.addEventListener('scroll', Utils.throttle(updateArrows, 100));
            updateArrows();

            // Store instance
            this.instances.push({ carousel, state, prevBtn, nextBtn });
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // CATEGORY NAVIGATION
    // ═══════════════════════════════════════════════════════════════════════════

    const CategoryNav = {
        nav: null,
        links: [],
        sections: [],
        activeLink: null,

        init() {
            this.nav = document.querySelector(CONFIG.selectors.categoryNav);
            if (!this.nav) return;

            this.links = Array.from(document.querySelectorAll(CONFIG.selectors.categoryLink));
            this.sections = Array.from(document.querySelectorAll(CONFIG.selectors.section));

            this.setupClickHandlers();
            this.setupScrollSpy();
        },

        setupClickHandlers() {
            this.links.forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const targetId = link.getAttribute('href');
                    const targetSection = document.querySelector(targetId);
                    
                    if (targetSection) {
                        Utils.scrollToElement(targetSection, 120);
                        this.setActiveLink(link);
                    }
                });
            });
        },

        setupScrollSpy() {
            const observerOptions = {
                root: null,
                rootMargin: '-20% 0px -70% 0px',
                threshold: 0
            };

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const sectionId = entry.target.getAttribute('id');
                        const correspondingLink = this.links.find(link => 
                            link.getAttribute('href') === `#${sectionId}`
                        );
                        if (correspondingLink) {
                            this.setActiveLink(correspondingLink);
                        }
                    }
                });
            }, observerOptions);

            this.sections.forEach(section => {
                observer.observe(section);
            });
        },

        setActiveLink(link) {
            if (this.activeLink === link) return;

            this.links.forEach(l => {
                l.classList.remove('active');
            });

            link.classList.add('active');
            this.activeLink = link;

            // Scroll nav to show active link (horizontal scroll)
            if (this.nav) {
                const navRect = this.nav.getBoundingClientRect();
                const linkRect = link.getBoundingClientRect();
                
                if (linkRect.right > navRect.right || linkRect.left < navRect.left) {
                    link.scrollIntoView({
                        behavior: 'smooth',
                        block: 'nearest',
                        inline: 'center'
                    });
                }
            }
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // QUICK VIEW MODAL
    // ═══════════════════════════════════════════════════════════════════════════

    const QuickViewModal = {
        modal: null,
        overlay: null,
        isOpen: false,
        currentProduct: null,

        init() {
            this.modal = document.querySelector(CONFIG.selectors.modal);
            this.overlay = document.querySelector(CONFIG.selectors.modalOverlay);

            if (!this.modal || !this.overlay) {
                this.createModal();
            }

            this.setupEventListeners();
        },

        createModal() {
            // Create overlay
            this.overlay = document.createElement('div');
            this.overlay.id = 'gp-modal-overlay';
            this.overlay.className = 'gp-modal-overlay';
            document.body.appendChild(this.overlay);

            // Create modal
            this.modal = document.createElement('div');
            this.modal.id = 'gp-quick-view-modal';
            this.modal.className = 'gp-quick-view-modal';
            this.modal.innerHTML = `
                <div class="gp-modal-content">
                    <button class="gp-modal-close" aria-label="بستن">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                    <div class="gp-modal-body">
                        <div class="gp-modal-loading">
                            <div class="gp-spinner"></div>
                            <span>در حال بارگذاری...</span>
                        </div>
                        <div class="gp-modal-product" style="display: none;"></div>
                    </div>
                </div>
            `;
            document.body.appendChild(this.modal);
        },

        setupEventListeners() {
            // Close button
            const closeBtn = this.modal.querySelector('.gp-modal-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => this.close());
            }

            // Overlay click
            this.overlay.addEventListener('click', () => this.close());

            // Escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isOpen) {
                    this.close();
                }
            });

            // Quick view buttons
            document.addEventListener('click', (e) => {
                const quickViewBtn = e.target.closest('[data-quick-view]');
                if (quickViewBtn) {
                    e.preventDefault();
                    const productId = quickViewBtn.dataset.quickView;
                    const variantId = quickViewBtn.dataset.variantId || null;
                    this.open(productId, variantId);
                }
            });
        },

        open(productId, variantId) {
            this.isOpen = true;
            this.modal.classList.add('active');
            this.overlay.classList.add('active');
            document.body.style.overflow = 'hidden';

            // Show loading
            const loadingEl = this.modal.querySelector('.gp-modal-loading');
            const productEl = this.modal.querySelector('.gp-modal-product');
            
            if (loadingEl) loadingEl.style.display = 'flex';
            if (productEl) productEl.style.display = 'none';

            // Fetch product data
            this.fetchProductData(productId, variantId);
        },

        close() {
            this.isOpen = false;
            this.modal.classList.remove('active');
            this.overlay.classList.remove('active');
            document.body.style.overflow = '';
            this.currentProduct = null;
        },

        async fetchProductData(productId, variantId) {
            try {
                const url = variantId 
                    ? `/api/gaming-products/${productId}/variants/${variantId}/`
                    : `/api/gaming-products/${productId}/`;
                
                const response = await fetch(url);
                
                if (!response.ok) {
                    throw new Error('خطا در دریافت اطلاعات محصول');
                }

                const data = await response.json();
                this.currentProduct = data;
                this.renderProduct(data);

            } catch (error) {
                console.error('Error fetching product:', error);
                Toast.error('خطا در دریافت اطلاعات محصول');
                this.close();
            }
        },

        renderProduct(data) {
            const loadingEl = this.modal.querySelector('.gp-modal-loading');
            const productEl = this.modal.querySelector('.gp-modal-product');

            if (loadingEl) loadingEl.style.display = 'none';
            if (!productEl) return;

            const hasDiscount = data.discount_percent > 0;
            const isAvailable = data.is_available && data.stock > 0;

            productEl.innerHTML = `
                <div class="gp-modal-grid">
                    <div class="gp-modal-image">
                        <img src="${data.image || '/static/images/placeholder.png'}" alt="${data.name}">
                        ${hasDiscount ? `<span class="gp-modal-badge">${data.discount_percent}% تخفیف</span>` : ''}
                    </div>
                    <div class="gp-modal-info">
                        <h2 class="gp-modal-title">${data.name}</h2>
                        ${data.product_name ? `<p class="gp-modal-subtitle">${data.product_name}</p>` : ''}
                        
                        <div class="gp-modal-price">
                            ${hasDiscount ? `
                                <span class="gp-modal-price-original">${Utils.formatPrice(data.original_price)} تومان</span>
                                <span class="gp-modal-price-current">${Utils.formatPrice(data.price)} تومان</span>
                            ` : `
                                <span class="gp-modal-price-current">${Utils.formatPrice(data.price)} تومان</span>
                            `}
                        </div>

                        ${data.description ? `
                            <div class="gp-modal-description">
                                <p>${data.description}</p>
                            </div>
                        ` : ''}

                        ${data.features && data.features.length > 0 ? `
                            <ul class="gp-modal-features">
                                ${data.features.map(f => `<li>${f}</li>`).join('')}
                            </ul>
                        ` : ''}

                        <div class="gp-modal-stock ${isAvailable ? 'in-stock' : 'out-of-stock'}">
                            ${isAvailable ? `
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
                                <span>موجود در انبار (${data.stock} عدد)</span>
                            ` : `
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
                                <span>ناموجود</span>
                            `}
                        </div>

                        <div class="gp-modal-actions">
                            ${isAvailable ? `
                                <button class="gp-btn gp-btn-primary gp-btn-add-cart" 
                                        data-product-id="${data.product_id || data.id}"
                                        data-variant-id="${data.variant_id || ''}">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>
                                    افزودن به سبد خرید
                                </button>
                            ` : `
                                <button class="gp-btn gp-btn-secondary gp-btn-notify"
                                        data-product-id="${data.product_id || data.id}"
                                        data-variant-id="${data.variant_id || ''}">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
                                    اطلاع‌رسانی موجودی
                                </button>
                            `}
                            <button class="gp-btn gp-btn-icon gp-btn-wishlist ${data.is_in_wishlist ? 'active' : ''}"
                                    data-product-id="${data.product_id || data.id}"
                                    data-variant-id="${data.variant_id || ''}"
                                    aria-label="افزودن به علاقه‌مندی‌ها">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="${data.is_in_wishlist ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                            </button>
                        </div>
                    </div>
                </div>
            `;

            productEl.style.display = 'block';

            // Setup action buttons
            this.setupModalActions(productEl);
        },

        setupModalActions(container) {
            // Add to cart
            const addCartBtn = container.querySelector('.gp-btn-add-cart');
            if (addCartBtn) {
                addCartBtn.addEventListener('click', () => {
                    const productId = addCartBtn.dataset.productId;
                    const variantId = addCartBtn.dataset.variantId;
                    Cart.addItem(productId, variantId, 1);
                });
            }

            // Wishlist
            const wishlistBtn = container.querySelector('.gp-btn-wishlist');
            if (wishlistBtn) {
                wishlistBtn.addEventListener('click', () => {
                    const productId = wishlistBtn.dataset.productId;
                    const variantId = wishlistBtn.dataset.variantId;
                    Wishlist.toggle(productId, variantId, wishlistBtn);
                });
            }

            // Notify stock
            const notifyBtn = container.querySelector('.gp-btn-notify');
            if (notifyBtn) {
                notifyBtn.addEventListener('click', () => {
                    const productId = notifyBtn.dataset.productId;
                    const variantId = notifyBtn.dataset.variantId;
                    Stock.notifyWhenAvailable(productId, variantId);
                });
            }
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // CART HANDLER
    // ═══════════════════════════════════════════════════════════════════════════

    const Cart = {
        async addItem(productId, variantId, quantity = 1) {
            try {
                const payload = {
                    product_id: productId,
                    quantity: quantity
                };
                
                if (variantId) {
                    payload.variant_id = variantId;
                }

                const response = await fetch(CONFIG.api.addToCart, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': Utils.getCSRFToken()
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    Toast.success('محصول به سبد خرید اضافه شد');
                    this.updateCartBadge(data.cart_count);
                    
                    // Dispatch custom event
                    document.dispatchEvent(new CustomEvent('cart:updated', {
                        detail: { count: data.cart_count }
                    }));
                } else {
                    throw new Error(data.message || 'خطا در افزودن به سبد خرید');
                }

            } catch (error) {
                console.error('Cart error:', error);
                Toast.error(error.message || 'خطا در افزودن به سبد خرید');
            }
        },

        updateCartBadge(count) {
            const badges = document.querySelectorAll('.cart-badge, .gp-cart-count');
            badges.forEach(badge => {
                badge.textContent = count;
                badge.style.display = count > 0 ? 'flex' : 'none';
                
                // Add animation
                badge.classList.add('pulse');
                setTimeout(() => badge.classList.remove('pulse'), 300);
            });
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // WISHLIST HANDLER
    // ═══════════════════════════════════════════════════════════════════════════

    const Wishlist = {
        async toggle(productId, variantId, buttonElement) {
            try {
                const payload = {
                    product_id: productId
                };
                
                if (variantId) {
                    payload.variant_id = variantId;
                }

                const response = await fetch(CONFIG.api.toggleWishlist, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': Utils.getCSRFToken()
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    const isAdded = data.action === 'added';
                    
                    // Update button state
                    if (buttonElement) {
                        buttonElement.classList.toggle('active', isAdded);
                        const svg = buttonElement.querySelector('svg');
                        if (svg) {
                            svg.setAttribute('fill', isAdded ? 'currentColor' : 'none');
                        }
                    }

                    // Update all matching wishlist buttons on page
                    this.updateAllButtons(productId, variantId, isAdded);

                    Toast.success(isAdded ? 'به علاقه‌مندی‌ها اضافه شد' : 'از علاقه‌مندی‌ها حذف شد');
                    
                    // Dispatch custom event
                    document.dispatchEvent(new CustomEvent('wishlist:updated', {
                        detail: { productId, variantId, isAdded }
                    }));

                } else {
                    throw new Error(data.message || 'خطا در بروزرسانی علاقه‌مندی‌ها');
                }

            } catch (error) {
                console.error('Wishlist error:', error);
                Toast.error(error.message || 'خطا در بروزرسانی علاقه‌مندی‌ها');
            }
        },

        updateAllButtons(productId, variantId, isAdded) {
            const selector = variantId 
                ? `[data-product-id="${productId}"][data-variant-id="${variantId}"]`
                : `[data-product-id="${productId}"]`;
            
            document.querySelectorAll(`.gp-btn-wishlist${selector}`).forEach(btn => {
                btn.classList.toggle('active', isAdded);
                const svg = btn.querySelector('svg');
                if (svg) {
                    svg.setAttribute('fill', isAdded ? 'currentColor' : 'none');
                }
            });
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // STOCK NOTIFICATION HANDLER
    // ═══════════════════════════════════════════════════════════════════════════

    const Stock = {
        async notifyWhenAvailable(productId, variantId) {
            try {
                const payload = {
                    product_id: productId
                };
                
                if (variantId) {
                    payload.variant_id = variantId;
                }

                const response = await fetch(CONFIG.api.notifyStock, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': Utils.getCSRFToken()
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    Toast.success('هنگام موجود شدن به شما اطلاع می‌دهیم');
                } else if (data.already_subscribed) {
                    Toast.info('شما قبلاً برای این محصول ثبت‌نام کرده‌اید');
                } else {
                    throw new Error(data.message || 'خطا در ثبت درخواست');
                }

            } catch (error) {
                console.error('Stock notification error:', error);
                Toast.error(error.message || 'خطا در ثبت درخواست اطلاع‌رسانی');
            }
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // CARD INTERACTIONS
    // ═══════════════════════════════════════════════════════════════════════════

    const CardInteractions = {
        init() {
            this.setupCardButtons();
            this.setupHoverEffects();
            this.setupLazyLoading();
        },

        setupCardButtons() {
            // Delegate event listeners for card buttons
            document.addEventListener('click', (e) => {
                // Add to cart button
                const addCartBtn = e.target.closest('.gp-card-btn-cart');
                if (addCartBtn) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const card = addCartBtn.closest('.gp-card');
                    const productId = card?.dataset.productId;
                    const variantId = card?.dataset.variantId;
                    
                    if (productId) {
                        // Add loading state
                        addCartBtn.classList.add('loading');
                        addCartBtn.disabled = true;
                        
                        Cart.addItem(productId, variantId, 1).finally(() => {
                            addCartBtn.classList.remove('loading');
                            addCartBtn.disabled = false;
                        });
                    }
                }

                // Wishlist button
                const wishlistBtn = e.target.closest('.gp-card-btn-wishlist');
                if (wishlistBtn) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const card = wishlistBtn.closest('.gp-card');
                    const productId = card?.dataset.productId;
                    const variantId = card?.dataset.variantId;
                    
                    if (productId) {
                        Wishlist.toggle(productId, variantId, wishlistBtn);
                    }
                }

                // Quick view button
                const quickViewBtn = e.target.closest('.gp-card-btn-quick-view');
                if (quickViewBtn) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const card = quickViewBtn.closest('.gp-card');
                    const productId = card?.dataset.productId;
                    const variantId = card?.dataset.variantId;
                    
                    if (productId) {
                        QuickViewModal.open(productId, variantId);
                    }
                }
            });
        },

        setupHoverEffects() {
            const cards = document.querySelectorAll('.gp-card');
            
            cards.forEach(card => {
                // Mouse move parallax effect for card image
                card.addEventListener('mousemove', (e) => {
                    const rect = card.getBoundingClientRect();
                    const x = (e.clientX - rect.left) / rect.width;
                    const y = (e.clientY - rect.top) / rect.height;
                    
                    const image = card.querySelector('.gp-card-image img');
                    if (image) {
                        const moveX = (x - 0.5) * 10;
                        const moveY = (y - 0.5) * 10;
                        image.style.transform = `scale(1.1) translate(${moveX}px, ${moveY}px)`;
                    }
                });

                card.addEventListener('mouseleave', () => {
                    const image = card.querySelector('.gp-card-image img');
                    if (image) {
                        image.style.transform = 'scale(1) translate(0, 0)';
                    }
                });
            });
        },

        setupLazyLoading() {
            // Lazy load images using Intersection Observer
            if ('IntersectionObserver' in window) {
                const imageObserver = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            const src = img.dataset.src;
                            
                            if (src) {
                                img.src = src;
                                img.classList.add('loaded');
                                img.removeAttribute('data-src');
                            }
                            
                            imageObserver.unobserve(img);
                        }
                    });
                }, {
                    rootMargin: '50px 0px',
                    threshold: 0.01
                });

                document.querySelectorAll('.gp-card-image img[data-src]').forEach(img => {
                    imageObserver.observe(img);
                });
            }
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // HERO SECTION ANIMATIONS
    // ═══════════════════════════════════════════════════════════════════════════

    const HeroAnimations = {
        init() {
            this.animateParticles();
            this.setupScrollIndicator();
        },

        animateParticles() {
            const particlesContainer = document.querySelector('.gp-hero-particles');
            if (!particlesContainer) return;

            // Create floating particles
            for (let i = 0; i < 20; i++) {
                const particle = document.createElement('div');
                particle.className = 'gp-particle';
                particle.style.cssText = `
                    --delay: ${Math.random() * 5}s;
                    --duration: ${5 + Math.random() * 10}s;
                    --x-start: ${Math.random() * 100}%;
                    --x-end: ${Math.random() * 100}%;
                    --size: ${2 + Math.random() * 4}px;
                `;
                particlesContainer.appendChild(particle);
            }
        },

        setupScrollIndicator() {
            const scrollIndicator = document.querySelector('.gp-hero-scroll-indicator');
            if (!scrollIndicator) return;

            scrollIndicator.addEventListener('click', () => {
                const firstSection = document.querySelector('.gp-category-section');
                if (firstSection) {
                    Utils.scrollToElement(firstSection, 100);
                }
            });

            // Hide on scroll
            window.addEventListener('scroll', Utils.throttle(() => {
                if (window.scrollY > 100) {
                    scrollIndicator.style.opacity = '0';
                    scrollIndicator.style.pointerEvents = 'none';
                } else {
                    scrollIndicator.style.opacity = '1';
                    scrollIndicator.style.pointerEvents = 'auto';
                }
            }, 100));
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // SEARCH & FILTER (Optional Enhancement)
    // ═══════════════════════════════════════════════════════════════════════════

    const SearchFilter = {
        searchInput: null,
        filterTimeout: null,

        init() {
            this.searchInput = document.querySelector('.gp-search-input');
            if (!this.searchInput) return;

            this.searchInput.addEventListener('input', Utils.debounce((e) => {
                this.filterProducts(e.target.value);
            }, 300));
        },

        filterProducts(query) {
            const normalizedQuery = query.trim().toLowerCase();
            const cards = document.querySelectorAll('.gp-card');

            cards.forEach(card => {
                const title = card.querySelector('.gp-card-title')?.textContent.toLowerCase() || '';
                const category = card.dataset.category?.toLowerCase() || '';
                
                const matches = !normalizedQuery || 
                    title.includes(normalizedQuery) || 
                    category.includes(normalizedQuery);

                card.style.display = matches ? '' : 'none';
                
                if (matches) {
                    card.classList.add('filter-visible');
                } else {
                    card.classList.remove('filter-visible');
                }
            });

            // Update section visibility
            document.querySelectorAll('.gp-category-section').forEach(section => {
                const visibleCards = section.querySelectorAll('.gp-card[style=""], .gp-card:not([style])');
                section.style.display = visibleCards.length > 0 ? '' : 'none';
            });
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // KEYBOARD NAVIGATION
    // ═══════════════════════════════════════════════════════════════════════════

    const KeyboardNav = {
        init() {
            document.addEventListener('keydown', (e) => {
                // Navigate carousels with arrow keys when focused
                if (e.target.closest('.gp-carousel')) {
                    const carousel = e.target.closest('.gp-carousel');
                    
                    if (e.key === 'ArrowLeft') {
                        e.preventDefault();
                        carousel.scrollBy({ left: 200, behavior: 'smooth' });
                    } else if (e.key === 'ArrowRight') {
                        e.preventDefault();
                        carousel.scrollBy({ left: -200, behavior: 'smooth' });
                    }
                }
            });

            // Make cards focusable
            document.querySelectorAll('.gp-card').forEach(card => {
                card.setAttribute('tabindex', '0');
                
                card.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        const quickViewBtn = card.querySelector('.gp-card-btn-quick-view');
                        if (quickViewBtn) {
                            quickViewBtn.click();
                        }
                    }
                });
            });
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // PERFORMANCE OPTIMIZATIONS
    // ═══════════════════════════════════════════════════════════════════════════

    const Performance = {
        init() {
            this.setupIntersectionAnimations();
            this.prefetchOnHover();
        },

        setupIntersectionAnimations() {
            if (!('IntersectionObserver' in window)) return;

            const animateObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('gp-animate-in');
                        animateObserver.unobserve(entry.target);
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            });

            document.querySelectorAll('.gp-card, .gp-category-header').forEach(el => {
                animateObserver.observe(el);
            });
        },

        prefetchOnHover() {
            document.querySelectorAll('.gp-card').forEach(card => {
                card.addEventListener('mouseenter', () => {
                    const productUrl = card.querySelector('a')?.href;
                    if (productUrl && !document.querySelector(`link[href="${productUrl}"]`)) {
                        const prefetch = document.createElement('link');
                        prefetch.rel = 'prefetch';
                        prefetch.href = productUrl;
                        document.head.appendChild(prefetch);
                    }
                }, { once: true });
            });
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // INITIALIZATION
    // ═══════════════════════════════════════════════════════════════════════════

    function init() {
        // Initialize all modules
        CategoryNav.init();
        Carousel.init();
        QuickViewModal.init();
        CardInteractions.init();
        HeroAnimations.init();
        SearchFilter.init();
        KeyboardNav.init();
        Performance.init();

        // Expose public API
        window.GamingProducts = {
            Cart,
            Wishlist,
            QuickViewModal,
            Toast,
            refresh: init
        };

        console.log('🎮 Gaming Products page initialized');
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
