1/**
 * Cart Management
 * Handles cart sidebar, add to cart, update quantities, etc.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Cart.js loaded successfully');
    
    // Cart elements
    const cartSidebar = document.getElementById('cartSidebar');
    const cartOverlay = document.getElementById('cartSidebarOverlay');
    
    // Check if elements exist
    if (!cartSidebar) {
        console.error('Cart sidebar not found');
        return;
    }
    
    if (!cartOverlay) {
        console.error('Cart overlay not found');
        return;
    }
    
    console.log('Cart elements found:', { cartSidebar, cartOverlay });
    
    // Open cart function
    window.openCart = function() {
        console.log('Opening cart...');
        cartSidebar.classList.add('active');
        cartOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    };
    
    // Close cart function
    window.closeCart = function() {
        console.log('Closing cart...');
        cartSidebar.classList.remove('active');
        cartOverlay.classList.remove('active');
        document.body.style.overflow = '';
    };
    
    // Event delegation for cart open buttons
    document.addEventListener('click', function(e) {
        const cartOpenBtn = e.target.closest('[data-cart-open]');
        if (cartOpenBtn) {
            e.preventDefault();
            console.log('Cart open button clicked');
            window.openCart();
        }
    });
    
    // Event delegation for cart close buttons
    document.addEventListener('click', function(e) {
        const cartCloseBtn = e.target.closest('[data-cart-close]');
        if (cartCloseBtn) {
            e.preventDefault();
            console.log('Cart close button clicked');
            window.closeCart();
        }
    });
    
    // Close on ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && cartSidebar.classList.contains('active')) {
            window.closeCart();
        }
    });
    
    console.log('Cart event listeners attached');
});
