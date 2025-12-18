/**
 * Virtual Services Page - Featured Products Carousel
 * Auto-scrolling with manual navigation controls
 */

document.addEventListener('DOMContentLoaded', function() {
    const carousel = document.querySelector('.vs-carousel__track');
    const slides = document.querySelectorAll('.vs-carousel__slide');
    const prevBtn = document.querySelector('.vs-carousel__nav--prev');
    const nextBtn = document.querySelector('.vs-carousel__nav--next');
    const dots = document.querySelectorAll('.vs-carousel__dot');
    
    if (!carousel || slides.length === 0) return;
    
    let currentIndex = 0;
    let autoScrollInterval;
    const autoScrollDelay = 5000; // 5 seconds
    
    // Calculate slide width dynamically
    function getSlideWidth() {
        const slide = slides[0];
        const gap = parseInt(getComputedStyle(carousel).gap) || 30;
        return slide.offsetWidth + gap;
    }
    
    // Update carousel position
    function updateCarousel(animate = true) {
        const slideWidth = getSlideWidth();
        const offset = currentIndex * slideWidth;
        
        if (animate) {
            carousel.style.transition = 'transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
        } else {
            carousel.style.transition = 'none';
        }
        
        carousel.style.transform = `translateX(${offset}px)`;
        
        // Update dots
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentIndex);
        });
    }
    
    // Go to next slide
    function nextSlide() {
        currentIndex++;
        
        // Loop back to start
        if (currentIndex >= slides.length) {
            currentIndex = 0;
        }
        
        updateCarousel();
    }
    
    // Go to previous slide
    function prevSlide() {
        currentIndex--;
        
        // Loop to end
        if (currentIndex < 0) {
            currentIndex = slides.length - 1;
        }
        
        updateCarousel();
    }
    
    // Go to specific slide
    function goToSlide(index) {
        if (index >= 0 && index < slides.length) {
            currentIndex = index;
            updateCarousel();
        }
    }
    
    // Start auto-scroll
    function startAutoScroll() {
        stopAutoScroll(); // Clear any existing interval
        autoScrollInterval = setInterval(nextSlide, autoScrollDelay);
    }
    
    // Stop auto-scroll
    function stopAutoScroll() {
        if (autoScrollInterval) {
            clearInterval(autoScrollInterval);
            autoScrollInterval = null;
        }
    }
    
    // Event Listeners
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            prevSlide();
            stopAutoScroll();
            startAutoScroll(); // Restart timer
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            nextSlide();
            stopAutoScroll();
            startAutoScroll(); // Restart timer
        });
    }
    
    // Dot navigation
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
            goToSlide(index);
            stopAutoScroll();
            startAutoScroll(); // Restart timer
        });
    });
    
    // Pause on hover
    carousel.addEventListener('mouseenter', stopAutoScroll);
    carousel.addEventListener('mouseleave', startAutoScroll);
    
    // Touch swipe support
    let touchStartX = 0;
    let touchEndX = 0;
    
    carousel.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
        stopAutoScroll();
    }, { passive: true });
    
    carousel.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
        startAutoScroll();
    }, { passive: true });
    
    function handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchStartX - touchEndX;
        
        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                // Swipe left (RTL: next)
                prevSlide();
            } else {
                // Swipe right (RTL: previous)
                nextSlide();
            }
        }
    }
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') {
            prevSlide();
            stopAutoScroll();
            startAutoScroll();
        } else if (e.key === 'ArrowRight') {
            nextSlide();
            stopAutoScroll();
            startAutoScroll();
        }
    });
    
    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            updateCarousel(false);
        }, 250);
    });
    
    // Initialize
    updateCarousel(false);
    startAutoScroll();
    
    // Pause when page is hidden
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            stopAutoScroll();
        } else {
            startAutoScroll();
        }
    });
});
