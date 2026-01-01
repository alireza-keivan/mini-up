/**
 * Wishlist Management System
 * Handles wishlist for both authenticated and anonymous users
 * - Authenticated: Uses Django backend
 * - Anonymous: Uses localStorage
 */

const WishlistManager = {
    STORAGE_KEY: 'mini_up_wishlist',
    
    /**
     * Initialize wishlist system
     */
    init() {
        this.updateWishlistCount();
        this.bindEvents();
        this.syncWithBackend();
        this.markWishlistItems();
    },
    
    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        // Check multiple indicators of authentication
        // 1. CSRF token input field
        if (document.querySelector('[name=csrfmiddlewaretoken]') !== null) {
            return true;
        }
        // 2. data-user-authenticated attribute
        if (document.body.dataset.userAuthenticated === 'true') {
            return true;
        }
        // 3. CSRF cookie (Django sets this for authenticated requests)
        const csrfCookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
        if (csrfCookie) {
            return true;
        }
        return false;
    },
    
    /**
     * Get wishlist from localStorage (for anonymous users)
     */
    getLocalWishlist() {
        try {
            const wishlist = localStorage.getItem(this.STORAGE_KEY);
            return wishlist ? JSON.parse(wishlist) : [];
        } catch (e) {
            console.error('Error reading wishlist from localStorage:', e);
            return [];
        }
    },
    
    /**
     * Save wishlist to localStorage
     */
    saveLocalWishlist(wishlist) {
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(wishlist));
            this.updateWishlistCount();
        } catch (e) {
            console.error('Error saving wishlist to localStorage:', e);
        }
    },
    
    /**
     * Add product to wishlist
     */
    async addToWishlist(productId) {
        if (this.isAuthenticated()) {
            return await this.addToWishlistBackend(productId);
        } else {
            return this.addToWishlistLocal(productId);
        }
    },
    
    /**
     * Remove product from wishlist
     */
    async removeFromWishlist(productId) {
        if (this.isAuthenticated()) {
            return await this.removeFromWishlistBackend(productId);
        } else {
            return this.removeFromWishlistLocal(productId);
        }
    },
    
    /**
     * Toggle product in wishlist
     */
    async toggleWishlist(productId) {
        const isInWishlist = await this.isInWishlist(productId);
        
        if (isInWishlist) {
            return await this.removeFromWishlist(productId);
        } else {
            return await this.addToWishlist(productId);
        }
    },
    
    /**
     * Check if product is in wishlist
     */
    async isInWishlist(productId) {
        if (this.isAuthenticated()) {
            // For authenticated users, check via backend or cached data
            const wishlist = await this.getBackendWishlist();
            return wishlist.some(item => item.product_id == productId || item.id == productId);
        } else {
            const wishlist = this.getLocalWishlist();
            return wishlist.includes(parseInt(productId));
        }
    },
    
    /**
     * Add to wishlist (localStorage - anonymous users)
     */
    addToWishlistLocal(productId) {
        const wishlist = this.getLocalWishlist();
        
        if (!wishlist.includes(parseInt(productId))) {
            wishlist.push(parseInt(productId));
            this.saveLocalWishlist(wishlist);
            this.showNotification('محصول به علاقه‌مندی‌ها اضافه شد', 'success');
            return { success: true, in_wishlist: true };
        }
        
        return { success: true, in_wishlist: true };
    },
    
    /**
     * Remove from wishlist (localStorage - anonymous users)
     */
    removeFromWishlistLocal(productId) {
        let wishlist = this.getLocalWishlist();
        wishlist = wishlist.filter(id => id !== parseInt(productId));
        this.saveLocalWishlist(wishlist);
        this.showNotification('محصول از علاقه‌مندی‌ها حذف شد', 'info');
        return { success: true, in_wishlist: false };
    },
    
    /**
     * Add to wishlist (backend - authenticated users)
     */
    async addToWishlistBackend(productId) {
        try {
            const response = await fetch('/products/api/v1/wishlist/add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ product_id: productId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updateWishlistCount();
                this.showNotification('محصول به علاقه‌مندی‌ها اضافه شد', 'success');
                return { success: true, in_wishlist: true };
            } else {
                this.showNotification(data.message || 'خطا در افزودن به علاقه‌مندی‌ها', 'error');
                return { success: false, in_wishlist: false };
            }
        } catch (error) {
            console.error('Error adding to wishlist:', error);
            this.showNotification('خطا در ارتباط با سرور', 'error');
            return { success: false, in_wishlist: false };
        }
    },
    
    /**
     * Remove from wishlist (backend - authenticated users)
     */
    async removeFromWishlistBackend(productId) {
        try {
            const response = await fetch('/products/api/v1/wishlist/remove/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ product_id: productId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updateWishlistCount();
                this.showNotification('محصول از علاقه‌مندی‌ها حذف شد', 'info');
                return { success: true, in_wishlist: false };
            } else {
                this.showNotification(data.message || 'خطا در حذف از علاقه‌مندی‌ها', 'error');
                return { success: false, in_wishlist: true };
            }
        } catch (error) {
            console.error('Error removing from wishlist:', error);
            this.showNotification('خطا در ارتباط با سرور', 'error');
            return { success: false, in_wishlist: true };
        }
    },
    
    /**
     * Get wishlist from backend
     */
    async getBackendWishlist() {
        try {
            const response = await fetch('/products/api/v1/wishlist/', {
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            const data = await response.json();
            return data.success ? data.data : [];
        } catch (error) {
            console.error('Error fetching wishlist:', error);
            return [];
        }
    },
    
    /**
     * Update wishlist count badge
     */
    async updateWishlistCount() {
        let count = 0;
        
        if (this.isAuthenticated()) {
            const wishlist = await this.getBackendWishlist();
            count = wishlist.length;
        } else {
            const wishlist = this.getLocalWishlist();
            count = wishlist.length;
        }
        
        const badge = document.getElementById('wishlistCount');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
        }
    },
    
    /**
     * Sync localStorage wishlist with backend after login
     */
    async syncWithBackend() {
        // Only sync if user just logged in and has items in localStorage
        if (this.isAuthenticated()) {
            const localWishlist = this.getLocalWishlist();
            
            if (localWishlist.length > 0) {
                // Sync each item
                for (const productId of localWishlist) {
                    await this.addToWishlistBackend(productId);
                }
                
                // Clear localStorage after sync
                localStorage.removeItem(this.STORAGE_KEY);
            }
        }
    },
    
    /**
     * Mark wishlist items on page load
     */
    async markWishlistItems() {
        let wishlistProductIds = [];
        
        // Get wishlist based on authentication status
        if (this.isAuthenticated()) {
            const wishlist = await this.getBackendWishlist();
            wishlistProductIds = wishlist.map(item => 
                parseInt(item.product_id || item.product?.id || item.id)
            );
        } else {
            wishlistProductIds = this.getLocalWishlist();
        }
        
        // Mark all wishlist buttons on the page
        const allWishlistBtns = document.querySelectorAll('[data-wishlist-toggle]');
        allWishlistBtns.forEach(btn => {
            const productId = parseInt(btn.dataset.productId);
            const heart = btn.querySelector('.wishlist-heart');
            
            if (heart && wishlistProductIds.includes(productId)) {
                // Mark as in wishlist
                heart.style.fill = 'currentColor';
                heart.style.stroke = 'currentColor';
                heart.classList.add('text-red-500');
                btn.classList.add('bg-red-500/40', 'border-red-400');
                btn.classList.remove('bg-cyan-500/20', 'border-cyan-400');
            }
        });
    },
    
    /**
     * Bind event listeners
     */
    bindEvents() {
        // Handle wishlist toggle buttons
        document.addEventListener('click', async (e) => {
            const wishlistBtn = e.target.closest('[data-wishlist-toggle]');
            
            if (wishlistBtn) {
                e.preventDefault();
                e.stopPropagation();
                
                const productId = wishlistBtn.dataset.productId;
                if (!productId) return;
                
                // Disable button during processing
                wishlistBtn.disabled = true;
                
                const result = await this.toggleWishlist(productId);
                
                // Update button state
                if (result.success) {
                    const heart = wishlistBtn.querySelector('.wishlist-heart');
                    if (heart) {
                        if (result.in_wishlist) {
                            // Mark as in wishlist - red filled heart
                            heart.style.fill = 'currentColor';
                            heart.style.stroke = 'currentColor';
                            heart.classList.add('text-red-500');
                            heart.classList.remove('text-white');
                            wishlistBtn.classList.add('bg-red-500/40', 'border-red-400');
                            wishlistBtn.classList.remove('bg-cyan-500/20', 'border-cyan-400');
                        } else {
                            // Mark as not in wishlist - white outline heart
                            heart.style.fill = 'none';
                            heart.style.stroke = 'currentColor';
                            heart.classList.remove('text-red-500');
                            heart.classList.add('text-white');
                            wishlistBtn.classList.remove('bg-red-500/40', 'border-red-400');
                            wishlistBtn.classList.add('bg-cyan-500/20', 'border-cyan-400');
                        }
                    }
                }
                
                // Re-enable button
                wishlistBtn.disabled = false;
            }
        });
        
        // Handle wishlist link click for anonymous users
        const wishlistToggle = document.getElementById('wishlistToggle');
        if (wishlistToggle) {
            wishlistToggle.addEventListener('click', (e) => {
                if (!this.isAuthenticated()) {
                    e.preventDefault();
                    this.showAnonymousWishlistModal();
                }
            });
        }
    },
    
    /**
     * Show modal for anonymous users to view their wishlist
     */
    showAnonymousWishlistModal() {
        const wishlist = this.getLocalWishlist();
        
        if (wishlist.length === 0) {
            this.showNotification('لیست علاقه‌مندی‌های شما خالی است', 'info');
            return;
        }
        
        // For now, just show a message. You can implement a modal here.
        this.showNotification(`شما ${wishlist.length} محصول در علاقه‌مندی‌ها دارید. برای مشاهده وارد شوید.`, 'info');
        
        // Redirect to login after 2 seconds
        setTimeout(() => {
            window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
        }, 2000);
    },
    
    /**
     * Get CSRF token
     */
    getCsrfToken() {
        // First try to get from input field
        const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenInput) {
            return tokenInput.value;
        }
        
        // If not found, try to get from cookie
        return this.getCookie('csrftoken') || '';
    },
    
    /**
     * Get cookie value by name
     */
    getCookie(name) {
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
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existing = document.querySelector('.wishlist-notification');
        if (existing) {
            existing.remove();
        }
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = `wishlist-notification fixed top-24 left-1/2 transform -translate-x-1/2 px-6 py-3 rounded-lg shadow-lg z-50 transition-all duration-300 ${
            type === 'success' ? 'bg-green-500' :
            type === 'error' ? 'bg-red-500' :
            'bg-blue-500'
        } text-white font-bold`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => WishlistManager.init());
} else {
    WishlistManager.init();
}

// Export for use in other scripts
window.WishlistManager = WishlistManager;
