/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * BUY PRODUCTS PAGE — MINI-UP.IR
 * Horizontal Scroll Carousel | Drag & Touch Support | No External Libraries
 * ═══════════════════════════════════════════════════════════════════════════════
 */

(function() {
    'use strict';

    // ═══════════════════════════════════════════════════════════════════════════
    // CONFIGURATION
    // ═══════════════════════════════════════════════════════════════════════════
    
    const CONFIG = {
        scrollAmount: 320,           // Pixels to scroll per arrow click
        dragThreshold: 5,            // Minimum drag distance to activate
        wheelMultiplier: 2,          // Mouse wheel scroll speed
        toastDuration: 4000,         // Cart toast display duration (ms)
        debounceDelay: 100,          // Debounce delay for scroll events
        apiEndpoints: {
            addToCart: '/api/cart/add/',
            quickView: '/api/products/{id}/quick-view/'
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // STATE MANAGEMENT
    // ═══════════════════════════════════════════════════════════════════════════
    
    const state = {
        activeModal: null,
        isDragging: false,
        startX: 0,
        scrollLeft: 0,
        currentWrapper: null,
        hasMoved: false
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // DOM ELEMENTS
    // ═══════════════════════════════════════════════════════════════════════════
    
    const elements = {
        scrollContainers: document.querySelectorAll('.bp-scroll-container'),
        quickViewModal: document.getElementById('bp-quick-view-modal'),
        modalBody: document.getElementById('bp-modal-body'),
        cartToast: document.getElementById('bp-cart-toast'),
        toastProductName: document.getElementById('bp-toast-product-name')
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // UTILITY FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Debounce function to limit execution rate
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Get CSRF token from cookies
     */
    function getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
                if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Smoothly scroll an element horizontally
     */
    function smoothScroll(element, amount) {
        element.scrollTo({
            left: element.scrollLeft + amount,
            behavior: 'smooth'
        });
    }

    /**
     * Create scroll progress dots
     */
    function createProgressDots(wrapper, progressContainer) {
        const cardWidth = wrapper.querySelector('.bp-product-card')?.offsetWidth || 300;
        const totalWidth = wrapper.scrollWidth;
        const visibleWidth = wrapper.clientWidth;

        const totalSteps = Math.ceil(totalWidth / cardWidth);

        progressContainer.innerHTML = '';

        for (let i = 0; i < totalSteps; i++) {
            const dot = document.createElement('div');
            dot.className = 'bp-progress-dot';
            progressContainer.appendChild(dot);
        }

        updateProgressDots(wrapper, progressContainer);
    }

    /**
     * Update active progress dot
     */
    function updateProgressDots(wrapper, progressContainer) {
        const dots = progressContainer.querySelectorAll('.bp-progress-dot');

        if (dots.length === 0) return;

        const cardWidth = wrapper.querySelector('.bp-product-card')?.offsetWidth || 300;
        const currentStep = Math.round(wrapper.scrollLeft / cardWidth);

        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentStep);
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // SCROLL & DRAG HANDLING
    // ═══════════════════════════════════════════════════════════════════════════

    function initScroll(container) {
        const wrapper = container.querySelector('.bp-scroll-wrapper');
        const prevBtn = container.querySelector('.bp-scroll-prev');
        const nextBtn = container.querySelector('.bp-scroll-next');
        const progress = container.querySelector('.bp-scroll-progress');

        if (!wrapper) return;

        // Create initial dots
        createProgressDots(wrapper, progress);

        // Arrow Buttons
        prevBtn?.addEventListener('click', () => smoothScroll(wrapper, CONFIG.scrollAmount));
        nextBtn?.addEventListener('click', () => smoothScroll(wrapper, -CONFIG.scrollAmount));

        // Drag Support
        // Track hover state for conditional wheel scroll prevention
        let isHovering = false;

        wrapper.addEventListener('mouseenter', () => {
            isHovering = true;
        });

        wrapper.addEventListener('mousedown', (e) => {
            // Don't interfere with links and buttons
            if (e.target.closest('a') || e.target.closest('button')) {
                return;
            }
            
            state.isDragging = true;
            state.hasMoved = false;
            wrapper.classList.add('is-dragging');
            state.startX = e.pageX - wrapper.offsetLeft;
            state.scrollLeft = wrapper.scrollLeft;
            state.currentWrapper = wrapper;
        });

        wrapper.addEventListener('mouseleave', () => {
            isHovering = false;
            state.isDragging = false;
            state.hasMoved = false;
            wrapper.classList.remove('is-dragging');
        });

        wrapper.addEventListener('mouseup', () => {
            state.isDragging = false;
            state.hasMoved = false;
            wrapper.classList.remove('is-dragging');
        });

        wrapper.addEventListener('mousemove', (e) => {
            if (!state.isDragging) return;
            
            const x = e.pageX - wrapper.offsetLeft;
            const walk = Math.abs(x - state.startX);
            
            // Only start dragging if moved more than threshold
            if (walk > CONFIG.dragThreshold) {
                state.hasMoved = true;
                e.preventDefault();
                const scrollAmount = (x - state.startX) * 1.5;
                wrapper.scrollLeft = state.scrollLeft - scrollAmount;
            }
        });

        // Touch Swipe
        wrapper.addEventListener('touchstart', (e) => {
            state.isDragging = true;
            state.startX = e.touches[0].pageX - wrapper.offsetLeft;
            state.scrollLeft = wrapper.scrollLeft;
        }, { passive: true });

        wrapper.addEventListener('touchend', () => {
            state.isDragging = false;
        });

        wrapper.addEventListener('touchmove', (e) => {
            if (!state.isDragging) return;
            const x = e.touches[0].pageX - wrapper.offsetLeft;
            const walk = (x - state.startX) * 1.5;
            wrapper.scrollLeft = state.scrollLeft - walk;
        }, { passive: true });

        // Mouse Wheel Support - only hijack scroll when hovering over carousel
        wrapper.addEventListener('wheel', (e) => {
            // Only prevent default page scroll when mouse is over the carousel
            if (isHovering) {
                e.preventDefault();
                wrapper.scrollLeft += e.deltaY * CONFIG.wheelMultiplier;
            }
            // Otherwise, allow normal page scrolling
        }, { passive: false });

        // Update dots on scroll
        wrapper.addEventListener('scroll', debounce(() => {
            updateProgressDots(wrapper, progress);
        }, CONFIG.debounceDelay));

        // Resize observer to recalc dots
        const resizeObserver = new ResizeObserver(() => {
            createProgressDots(wrapper, progress);
        });
        resizeObserver.observe(wrapper);
    }

    // Initialize each scroll container
    elements.scrollContainers.forEach(initScroll);

    // ═══════════════════════════════════════════════════════════════════════════
    // ADD TO CART HANDLER
    // ═══════════════════════════════════════════════════════════════════════════

    async function addToCart(productId, button, productName) {
        if (!button) return;

        button.classList.add('loading');

        try {
            const response = await fetch(CONFIG.apiEndpoints.addToCart, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ product_id: productId, quantity: 1 })
            });

            const data = await response.json();

            if (data.success) {
                showCartToast(productName);
            } else {
                window.showToast(data.message || 'خطا در افزودن به سبد خرید', 'error');
            }

        } catch (err) {
            console.error(err);
            window.showToast('خطا در اتصال به سرور', 'error');

        } finally {
            button.classList.remove('loading');
        }
    }

    /**
     * Cart Toast Notification
     */
    function showCartToast(name) {
        elements.toastProductName.textContent = name;

        elements.cartToast.classList.add('show');

        setTimeout(() => {
            elements.cartToast.classList.remove('show');
        }, CONFIG.toastDuration);
    }

    // Delegated Add-to-Cart listener
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-action="add-to-cart"]');
        if (!btn) return;

        const id = btn.dataset.productId;
        const name = btn.dataset.productName;

        addToCart(id, btn, name);
    });

    // ═══════════════════════════════════════════════════════════════════════════
    // QUICK VIEW MODAL
    // ═══════════════════════════════════════════════════════════════════════════

    async function openQuickView(productId) {
        elements.quickViewModal.classList.add('active');

        elements.modalBody.innerHTML = `
            <div class="bp-modal-loading flex items-center justify-center w-full py-20">
                <div class="bp-spinner w-12 h-12 border-4 border-gray-700 border-t-neon-pink rounded-full animate-spin"></div>
            </div>
        `;

        const endpoint = CONFIG.apiEndpoints.quickView.replace('{id}', productId);

        try {
            const response = await fetch(endpoint);
            const data = await response.json();

            if (data.success) {
                elements.modalBody.innerHTML = data.html;
            } else {
                elements.modalBody.innerHTML = `<p class="text-center text-red-500 py-10">${data.message}</p>`;
            }

        } catch (err) {
            console.error(err);
            elements.modalBody.innerHTML = `<p class="text-center text-red-500 py-10">خطا در دریافت اطلاعات</p>`;
        }
    }

    function closeModal() {
        elements.quickViewModal.classList.remove('active');
    }

    // Delegated listener
    document.addEventListener('click', (e) => {
        // Quick View button
        const quickViewBtn = e.target.closest('[data-action="quick-view"]');
        if (quickViewBtn) {
            const id = quickViewBtn.dataset.product;
            openQuickView(id);
            return;
        }

        // Close modal
        if (e.target.dataset.action === 'close-modal') {
            closeModal();
            return;
        }
    });

    // Close modal on ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });

})();
