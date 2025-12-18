/**
 * Mini-up.ir - Virtual Services Page JavaScript
 * Neon Dark Theme - RTL Support
 * 
 * Features:
 * - Horizontal Carousel with drag/touch support
 * - Smooth scrolling with momentum
 * - Keyboard navigation
 * - Responsive behavior
 * - Neon glow effects on interaction
 */

(function() {
    'use strict';

    // ═══════════════════════════════════════════════════════════════════════════
    // CONFIGURATION
    // ═══════════════════════════════════════════════════════════════════════════

    const CONFIG = {
        scrollAmount: 320,           // Pixels to scroll per button click
        scrollDuration: 400,         // Animation duration in ms
        dragThreshold: 5,            // Minimum drag distance to activate
        momentumMultiplier: 0.92,    // Momentum decay rate
        autoScrollInterval: 5000,    // Auto-scroll interval (0 to disable)
        touchSensitivity: 1.2        // Touch drag sensitivity
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // DOM ELEMENTS
    // ═══════════════════════════════════════════════════════════════════════════

    const serviceContainers = document.querySelectorAll('.vs-service');
    const carousels = document.querySelectorAll('.vs-carousel');
    const filterButtons = document.querySelectorAll('.vs-filter-btn');
    const searchInput = document.getElementById('vs-search');

    // ═══════════════════════════════════════════════════════════════════════════
    // CAROUSEL CLASS
    // ═══════════════════════════════════════════════════════════════════════════

    class ServiceCarousel {
        constructor(container) {
            this.container = container;
            this.carousel = container.querySelector('.vs-carousel');
            this.track = container.querySelector('.vs-carousel-track');
            this.prevBtn = container.querySelector('.vs-nav-prev');
            this.nextBtn = container.querySelector('.vs-nav-next');
            this.cards = container.querySelectorAll('.vs-card');
            
            if (!this.carousel || !this.track) return;

            // State
            this.isDragging = false;
            this.startX = 0;
            this.scrollLeft = 0;
            this.velocity = 0;
            this.momentumId = null;
            this.autoScrollId = null;

            this.init();
        }

        init() {
            this.bindEvents();
            this.updateNavButtons();
            this.setupAutoScroll();
            this.addCardEffects();
        }

        // ─────────────────────────────────────────────────────────────────────
        // EVENT BINDING
        // ─────────────────────────────────────────────────────────────────────

        bindEvents() {
            // Navigation buttons
            if (this.prevBtn) {
                this.prevBtn.addEventListener('click', () => this.scrollPrev());
            }
            if (this.nextBtn) {
                this.nextBtn.addEventListener('click', () => this.scrollNext());
            }

            // Mouse drag
            this.carousel.addEventListener('mousedown', (e) => this.onDragStart(e));
            document.addEventListener('mousemove', (e) => this.onDragMove(e));
            document.addEventListener('mouseup', () => this.onDragEnd());

            // Touch drag
            this.carousel.addEventListener('touchstart', (e) => this.onTouchStart(e), { passive: true });
            this.carousel.addEventListener('touchmove', (e) => this.onTouchMove(e), { passive: false });
            this.carousel.addEventListener('touchend', () => this.onDragEnd());

            // Scroll event for button visibility
            this.carousel.addEventListener('scroll', () => {
                this.updateNavButtons();
                this.cancelAutoScroll();
            });

            // Keyboard navigation
            this.carousel.addEventListener('keydown', (e) => this.onKeyDown(e));

            // Mouse enter/leave for auto-scroll pause
            this.container.addEventListener('mouseenter', () => this.pauseAutoScroll());
            this.container.addEventListener('mouseleave', () => this.resumeAutoScroll());

            // Wheel horizontal scroll
            this.carousel.addEventListener('wheel', (e) => this.onWheel(e), { passive: false });
        }

        // ─────────────────────────────────────────────────────────────────────
        // NAVIGATION
        // ─────────────────────────────────────────────────────────────────────

        scrollPrev() {
            // RTL: scroll right means going to previous
            this.smoothScroll(this.carousel.scrollLeft + CONFIG.scrollAmount);
        }

        scrollNext() {
            // RTL: scroll left means going to next
            this.smoothScroll(this.carousel.scrollLeft - CONFIG.scrollAmount);
        }

        smoothScroll(targetScroll) {
            const startScroll = this.carousel.scrollLeft;
            const distance = targetScroll - startScroll;
            const startTime = performance.now();

            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / CONFIG.scrollDuration, 1);
                
                // Easing function (ease-out-cubic)
                const easeOut = 1 - Math.pow(1 - progress, 3);
                
                this.carousel.scrollLeft = startScroll + (distance * easeOut);

                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    this.updateNavButtons();
                }
            };

            requestAnimationFrame(animate);
        }

        updateNavButtons() {
            if (!this.prevBtn || !this.nextBtn) return;

            const { scrollLeft, scrollWidth, clientWidth } = this.carousel;
            const maxScroll = scrollWidth - clientWidth;

            // RTL logic is inverted
            // scrollLeft is 0 at the start (right side in RTL)
            // scrollLeft is negative when scrolled left
            
            const atStart = scrollLeft >= -10;
            const atEnd = scrollLeft <= -(maxScroll - 10);

            this.prevBtn.classList.toggle('vs-nav-disabled', atStart);
            this.nextBtn.classList.toggle('vs-nav-disabled', atEnd);

            this.prevBtn.disabled = atStart;
            this.nextBtn.disabled = atEnd;
        }

        // ─────────────────────────────────────────────────────────────────────
        // DRAG HANDLING (Mouse)
        // ─────────────────────────────────────────────────────────────────────

        onDragStart(e) {
            if (e.button !== 0) return; // Only left mouse button
            
            this.isDragging = true;
            this.startX = e.pageX;
            this.scrollLeft = this.carousel.scrollLeft;
            this.velocity = 0;
            this.lastX = e.pageX;
            this.lastTime = Date.now();

            this.carousel.classList.add('vs-grabbing');
            this.cancelMomentum();
            this.cancelAutoScroll();

            e.preventDefault();
        }

        onDragMove(e) {
            if (!this.isDragging) return;

            const x = e.pageX;
            const walk = (x - this.startX);
            
            // Calculate velocity for momentum
            const now = Date.now();
            const dt = now - this.lastTime;
            if (dt > 0) {
                this.velocity = (x - this.lastX) / dt;
            }
            this.lastX = x;
            this.lastTime = now;

            this.carousel.scrollLeft = this.scrollLeft - walk;
        }

        onDragEnd() {
            if (!this.isDragging) return;
            
            this.isDragging = false;
            this.carousel.classList.remove('vs-grabbing');

            // Apply momentum
            if (Math.abs(this.velocity) > 0.1) {
                this.applyMomentum();
            }

            this.updateNavButtons();
        }

        // ─────────────────────────────────────────────────────────────────────
        // TOUCH HANDLING
        // ─────────────────────────────────────────────────────────────────────

        onTouchStart(e) {
            this.isDragging = true;
            this.startX = e.touches[0].pageX;
            this.scrollLeft = this.carousel.scrollLeft;
            this.velocity = 0;
            this.lastX = e.touches[0].pageX;
            this.lastTime = Date.now();

            this.cancelMomentum();
            this.cancelAutoScroll();
        }

        onTouchMove(e) {
            if (!this.isDragging) return;

            const x = e.touches[0].pageX;
            const walk = (x - this.startX) * CONFIG.touchSensitivity;

            // Calculate velocity
            const now = Date.now();
            const dt = now - this.lastTime;
            if (dt > 0) {
                this.velocity = (x - this.lastX) / dt;
            }
            this.lastX = x;
            this.lastTime = now;

            this.carousel.scrollLeft = this.scrollLeft - walk;

            // Prevent vertical scroll when dragging horizontally
            if (Math.abs(walk) > CONFIG.dragThreshold) {
                e.preventDefault();
            }
        }

        // ─────────────────────────────────────────────────────────────────────
        // MOMENTUM SCROLLING
        // ─────────────────────────────────────────────────────────────────────

        applyMomentum() {
            const momentum = () => {
                if (Math.abs(this.velocity) < 0.01) {
                    this.cancelMomentum();
                    return;
                }

                this.carousel.scrollLeft -= this.velocity * 16;
                this.velocity *= CONFIG.momentumMultiplier;

                this.momentumId = requestAnimationFrame(momentum);
            };

            this.momentumId = requestAnimationFrame(momentum);
        }

        cancelMomentum() {
            if (this.momentumId) {
                cancelAnimationFrame(this.momentumId);
                this.momentumId = null;
            }
        }

        // ─────────────────────────────────────────────────────────────────────
        // KEYBOARD NAVIGATION
        // ─────────────────────────────────────────────────────────────────────

        onKeyDown(e) {
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.scrollNext(); // RTL: left arrow = next
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.scrollPrev(); // RTL: right arrow = prev
                    break;
                case 'Home':
                    e.preventDefault();
                    this.scrollToStart();
                    break;
                case 'End':
                    e.preventDefault();
                    this.scrollToEnd();
                    break;
            }
        }

        scrollToStart() {
            this.smoothScroll(0);
        }

        scrollToEnd() {
            const maxScroll = this.carousel.scrollWidth - this.carousel.clientWidth;
            this.smoothScroll(-maxScroll);
        }

        // ─────────────────────────────────────────────────────────────────────
        // WHEEL HANDLING
        // ─────────────────────────────────────────────────────────────────────

        onWheel(e) {
            // Convert vertical scroll to horizontal
            if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
                e.preventDefault();
                this.carousel.scrollLeft -= e.deltaY;
                this.updateNavButtons();
            }
        }

        // ─────────────────────────────────────────────────────────────────────
        // AUTO SCROLL
        // ─────────────────────────────────────────────────────────────────────

        setupAutoScroll() {
            if (CONFIG.autoScrollInterval <= 0) return;
            this.resumeAutoScroll();
        }

        pauseAutoScroll() {
            if (this.autoScrollId) {
                clearInterval(this.autoScrollId);
                this.autoScrollId = null;
            }
        }

        resumeAutoScroll() {
            if (CONFIG.autoScrollInterval <= 0) return;
            
            this.autoScrollId = setInterval(() => {
                const { scrollLeft, scrollWidth, clientWidth } = this.carousel;
                const maxScroll = scrollWidth - clientWidth;

                // If at end, scroll back to start
                if (scrollLeft <= -(maxScroll - 50)) {
                    this.scrollToStart();
                } else {
                    this.scrollNext();
                }
            }, CONFIG.autoScrollInterval);
        }

        cancelAutoScroll() {
            this.pauseAutoScroll();
        }

        // ─────────────────────────────────────────────────────────────────────
        // CARD EFFECTS
        // ─────────────────────────────────────────────────────────────────────

        addCardEffects() {
            this.cards.forEach(card => {
                // Tilt effect on hover
                card.addEventListener('mousemove', (e) => this.onCardMouseMove(e, card));
                card.addEventListener('mouseleave', (e) => this.onCardMouseLeave(e, card));
                
                // Click ripple
                card.addEventListener('click', (e) => this.createRipple(e, card));
            });
        }

        onCardMouseMove(e, card) {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;

            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;

            // Move glow effect
            const glowX = (x / rect.width) * 100;
            const glowY = (y / rect.height) * 100;
            card.style.setProperty('--glow-x', `${glowX}%`);
            card.style.setProperty('--glow-y', `${glowY}%`);
        }

        onCardMouseLeave(e, card) {
            card.style.transform = '';
            card.style.setProperty('--glow-x', '50%');
            card.style.setProperty('--glow-y', '50%');
        }

        createRipple(e, card) {
            const ripple = document.createElement('span');
            ripple.className = 'vs-ripple';
            
            const rect = card.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            
            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${e.clientX - rect.left - size/2}px`;
            ripple.style.top = `${e.clientY - rect.top - size/2}px`;
            
            card.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // INITIALIZE ALL CAROUSELS
    // ═══════════════════════════════════════════════════════════════════════════

    const carouselInstances = [];
    
    serviceContainers.forEach(container => {
        const instance = new ServiceCarousel(container);
        carouselInstances.push(instance);
    });

    // ═══════════════════════════════════════════════════════════════════════════
    // SEARCH FILTER
    // ═══════════════════════════════════════════════════════════════════════════

    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            
            searchTimeout = setTimeout(() => {
                const keyword = this.value.trim().toLowerCase();
                
                if (keyword === '') {
                    // Show all cards and services
                    document.querySelectorAll('.vs-card').forEach(card => {
                        card.style.display = '';
                        card.style.opacity = '1';
                    });
                    serviceContainers.forEach(container => {
                        container.style.display = '';
                    });
                    return;
                }

                // Filter cards
                document.querySelectorAll('.vs-card').forEach(card => {
                    const cardName = (card.dataset.name || '').toLowerCase();
                    const cardDesc = (card.dataset.description || '').toLowerCase();
                    const cardTags = (card.dataset.tags || '').toLowerCase();
                    
                    const isMatch = cardName.includes(keyword) || 
                                   cardDesc.includes(keyword) || 
                                   cardTags.includes(keyword);
                    
                    card.style.display = isMatch ? '' : 'none';
                    card.style.opacity = isMatch ? '1' : '0';
                });

                // Hide empty service sections
                serviceContainers.forEach(container => {
                    const visibleCards = container.querySelectorAll('.vs-card[style=""], .vs-card:not([style*="display: none"])');
                    const hasVisibleCards = Array.from(container.querySelectorAll('.vs-card')).some(card => {
                        return card.style.display !== 'none';
                    });
                    container.style.display = hasVisibleCards ? '' : 'none';
                });

            }, 300); // Debounce 300ms
        });

        // Clear search on Escape
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                this.dispatchEvent(new Event('input'));
                this.blur();
            }
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // CATEGORY FILTER BUTTONS
    // ═══════════════════════════════════════════════════════════════════════════

    if (filterButtons.length > 0) {
        filterButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const filter = this.dataset.filter;

                // Update active state
                filterButtons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                // Clear search input
                if (searchInput) {
                    searchInput.value = '';
                }

                // Apply filter
                if (filter === 'all') {
                    serviceContainers.forEach(container => {
                        container.style.display = '';
                        container.classList.remove('vs-hidden');
                        
                        // Animate in
                        container.style.opacity = '0';
                        container.style.transform = 'translateY(20px)';
                        
                        requestAnimationFrame(() => {
                            container.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
                            container.style.opacity = '1';
                            container.style.transform = 'translateY(0)';
                        });
                    });
                } else {
                    serviceContainers.forEach(container => {
                        const category = container.dataset.category;
                        const shouldShow = category === filter;

                        if (shouldShow) {
                            container.style.display = '';
                            container.classList.remove('vs-hidden');
                            
                            // Animate in
                            container.style.opacity = '0';
                            container.style.transform = 'translateY(20px)';
                            
                            requestAnimationFrame(() => {
                                container.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
                                container.style.opacity = '1';
                                container.style.transform = 'translateY(0)';
                            });
                        } else {
                            container.style.opacity = '0';
                            container.style.transform = 'translateY(-20px)';
                            
                            setTimeout(() => {
                                container.style.display = 'none';
                                container.classList.add('vs-hidden');
                            }, 400);
                        }
                    });
                }

                // Update URL hash
                history.replaceState(null, null, filter === 'all' ? '#' : `#${filter}`);
            });
        });

        // Check URL hash on load
        const initialHash = window.location.hash.slice(1);
        if (initialHash) {
            const targetBtn = document.querySelector(`.vs-filter-btn[data-filter="${initialHash}"]`);
            if (targetBtn) {
                targetBtn.click();
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // SCROLL TO SERVICE ON ANCHOR CLICK
    // ═══════════════════════════════════════════════════════════════════════════

    document.querySelectorAll('a[href^="#service-"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            const target = document.querySelector(targetId);
            
            if (target) {
                e.preventDefault();
                
                // Calculate offset for fixed header
                const headerHeight = document.querySelector('.site-header')?.offsetHeight || 80;
                const targetPosition = target.getBoundingClientRect().top + window.scrollY - headerHeight - 20;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });

                // Add highlight effect
                target.classList.add('vs-highlight');
                setTimeout(() => {
                    target.classList.remove('vs-highlight');
                }, 2000);
            }
        });
    });

    // ═══════════════════════════════════════════════════════════════════════════
    // INTERSECTION OBSERVER FOR SECTION ANIMATIONS
    // ═══════════════════════════════════════════════════════════════════════════

    if ('IntersectionObserver' in window) {
        const sectionObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const section = entry.target;
                    section.classList.add('vs-visible');
                    
                    // Stagger card animations
                    const cards = section.querySelectorAll('.vs-card');
                    cards.forEach((card, index) => {
                        card.style.animationDelay = `${index * 100}ms`;
                        card.classList.add('vs-card-animate');
                    });
                    
                    sectionObserver.unobserve(section);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        serviceContainers.forEach(container => {
            sectionObserver.observe(container);
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PRICE CARD HOVER GLOW EFFECT
    // ═══════════════════════════════════════════════════════════════════════════

    document.querySelectorAll('.vs-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            // Add glow class
            this.classList.add('vs-card-glow');
            
            // Create glow element if not exists
            if (!this.querySelector('.vs-glow-effect')) {
                const glow = document.createElement('div');
                glow.className = 'vs-glow-effect';
                this.appendChild(glow);
            }
        });

        card.addEventListener('mouseleave', function() {
            this.classList.remove('vs-card-glow');
        });

        // Dynamic glow position
        card.addEventListener('mousemove', function(e) {
            const glow = this.querySelector('.vs-glow-effect');
            if (glow) {
                const rect = this.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / rect.width) * 100;
                const y = ((e.clientY - rect.top) / rect.height) * 100;
                
                glow.style.background = `radial-gradient(circle at ${x}% ${y}%, rgba(0, 255, 255, 0.3) 0%, transparent 50%)`;
            }
        });
    });

    // ═══════════════════════════════════════════════════════════════════════════
    // POPULAR/FEATURED BADGE PULSE
    // ═══════════════════════════════════════════════════════════════════════════

    document.querySelectorAll('.vs-badge-popular, .vs-badge-featured').forEach(badge => {
        // Add pulse animation
        setInterval(() => {
            badge.classList.add('vs-pulse');
            setTimeout(() => badge.classList.remove('vs-pulse'), 1000);
        }, 3000);
    });

    // ═══════════════════════════════════════════════════════════════════════════
    // PRICE ANIMATION ON SCROLL
    // ═══════════════════════════════════════════════════════════════════════════

    function animatePrice(element) {
        const finalPrice = parseInt(element.dataset.price || element.textContent.replace(/[^\d]/g, ''));
        const duration = 1000;
        const startTime = performance.now();
        const startPrice = 0;

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Ease out
            const easeProgress = 1 - Math.pow(1 - progress, 3);
            const currentPrice = Math.floor(startPrice + (finalPrice - startPrice) * easeProgress);
            
            element.textContent = currentPrice.toLocaleString('fa-IR');
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.textContent = finalPrice.toLocaleString('fa-IR');
            }
        };

        requestAnimationFrame(animate);
    }

    // Observe price elements
    if ('IntersectionObserver' in window) {
        const priceObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animatePrice(entry.target);
                    priceObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        document.querySelectorAll('.vs-price[data-animate-price]').forEach(price => {
            priceObserver.observe(price);
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // KEYBOARD SHORTCUTS
    // ═══════════════════════════════════════════════════════════════════════════

    document.addEventListener('keydown', function(e) {
        // Focus search with Ctrl+K or /
        if ((e.ctrlKey && e.key === 'k') || (e.key === '/' && document.activeElement.tagName !== 'INPUT')) {
            e.preventDefault();
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
    });

    // ═══════════════════════════════════════════════════════════════════════════
    // LAZY LOAD IMAGES IN CARDS
    // ═══════════════════════════════════════════════════════════════════════════

    if ('IntersectionObserver' in window) {
        const imgObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.classList.add('vs-img-loaded');
                    }
                    imgObserver.unobserve(img);
                }
            });
        }, {
            rootMargin: '100px'
        });

        document.querySelectorAll('.vs-card img[data-src]').forEach(img => {
            imgObserver.observe(img);
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // EXPOSE API FOR EXTERNAL USE
    // ═══════════════════════════════════════════════════════════════════════════

    window.VirtualServices = {
        carousels: carouselInstances,
        
        // Filter by category programmatically
        filterByCategory: function(category) {
            const btn = document.querySelector(`.vs-filter-btn[data-filter="${category}"]`);
            if (btn) btn.click();
        },
        
        // Search programmatically
        search: function(keyword) {
            if (searchInput) {
                searchInput.value = keyword;
                searchInput.dispatchEvent(new Event('input'));
            }
        },
        
        // Scroll to service
        scrollToService: function(serviceId) {
            const target = document.getElementById(serviceId);
            if (target) {
                const headerHeight = document.querySelector('.site-header')?.offsetHeight || 80;
                const targetPosition = target.getBoundingClientRect().top + window.scrollY - headerHeight - 20;
                window.scrollTo({ top: targetPosition, behavior: 'smooth' });
            }
        },
        
        // Refresh carousels (useful after dynamic content load)
        refresh: function() {
            carouselInstances.forEach(instance => {
                instance.updateNavButtons();
            });
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // PAGE LOAD COMPLETE
    // ═══════════════════════════════════════════════════════════════════════════

    document.addEventListener('DOMContentLoaded', function() {
        document.body.classList.add('vs-loaded');
        console.log('⚡ Virtual Services Page Initialized');
    });

})();
