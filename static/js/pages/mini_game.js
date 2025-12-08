/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * MINI-UP.IR - MINI GAME PAGE
 * Premium Gaming Currency & Items Store
 * ═══════════════════════════════════════════════════════════════════════════════
 * 
 * @description  Complete JavaScript for Mini Game page functionality
 * @version      1.0.0
 * @author       Mini-up Development Team
 * @license      Proprietary
 * 
 * Features:
 * - Dynamic category filtering
 * - Game selection and filtering
 * - Sort functionality (price, popularity, newest)
 * - Search within plans
 * - Purchase modal with form validation
 * - Add to cart functionality
 * - Smooth animations and transitions
 * - RTL support
 * - Mobile responsive interactions
 * - Loading states and skeletons
 * - Toast notifications integration
 * 
 * ═══════════════════════════════════════════════════════════════════════════════
 */

(function() {
    'use strict';

    // ═══════════════════════════════════════════════════════════════════════════
    // CONFIGURATION & CONSTANTS
    // ═══════════════════════════════════════════════════════════════════════════

    const CONFIG = {
        // Animation durations (ms)
        ANIMATION_DURATION: 300,
        RIPPLE_DURATION: 600,
        TOAST_DURATION: 3000,
        DEBOUNCE_DELAY: 300,

        // API endpoints (to be configured with Django URLs)
        API: {
            GET_PLANS: '/api/mini-game/plans/',
            GET_CATEGORIES: '/api/mini-game/categories/',
            GET_GAMES: '/api/mini-game/games/',
            ADD_TO_CART: '/api/cart/add/',
            PURCHASE: '/api/mini-game/purchase/',
        },

        // Validation patterns
        VALIDATION: {
            PLAYER_ID: /^[a-zA-Z0-9_-]{3,50}$/,
            EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            PHONE: /^09[0-9]{9}$/,
        },

        // Sort options
        SORT_OPTIONS: {
            'popular': 'محبوب‌ترین',
            'price-low': 'ارزان‌ترین',
            'price-high': 'گران‌ترین',
            'newest': 'جدیدترین',
        },

        // Local storage keys
        STORAGE_KEYS: {
            SELECTED_GAME: 'mg_selected_game',
            SELECTED_CATEGORY: 'mg_selected_category',
            SORT_PREFERENCE: 'mg_sort_preference',
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // STATE MANAGEMENT
    // ═══════════════════════════════════════════════════════════════════════════

    const State = {
        // Current selections
        selectedGame: null,
        selectedCategory: null,
        selectedPlan: null,
        
        // Filter & sort
        currentSort: 'popular',
        searchQuery: '',
        
        // UI states
        isLoading: false,
        isModalOpen: false,
        isSubmitting: false,
        
        // Data cache
        games: [],
        categories: [],
        plans: [],
        
        // Cart
        cartItems: [],
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // DOM ELEMENT REFERENCES
    // ═══════════════════════════════════════════════════════════════════════════

    const DOM = {
        // Main containers
        pageContainer: null,
        heroSection: null,
        categoriesContainer: null,
        plansContainer: null,
        
        // Game selector
        gameSelector: null,
        gameSelectorBtn: null,
        gameSelectorDropdown: null,
        gameOptions: null,
        selectedGameDisplay: null,
        
        // Category tabs
        categoryTabs: null,
        categoryTabButtons: null,
        
        // Filters & sorting
        sortSelect: null,
        searchInput: null,
        filterTags: null,
        
        // Plan cards grid
        plansGrid: null,
        planCards: null,
        
        // Modal elements
        modalOverlay: null,
        modal: null,
        modalClose: null,
        modalForm: null,
        modalGameIcon: null,
        modalTitle: null,
        modalSubtitle: null,
        modalPlanName: null,
        modalPlanPrice: null,
        playerIdInput: null,
        submitBtn: null,
        
        // Empty state
        emptyState: null,
        
        // Loading skeleton
        loadingSkeleton: null,
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // INITIALIZATION
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Initialize the Mini Game page
     */
    function init() {
        // Cache DOM elements
        cacheDOMElements();
        
        // Load saved preferences
        loadSavedPreferences();
        
        // Bind all event listeners
        bindEventListeners();
        
        // Initialize components
        initGameSelector();
        initCategoryTabs();
        initSortSelect();
        initSearchInput();
        initPlanCards();
        initModal();
        
        // Initialize animations
        initScrollAnimations();
        
        // Log initialization
        console.log('🎮 Mini Game page initialized');
    }

    /**
     * Cache all DOM element references
     */
    function cacheDOMElements() {
        // Main containers
        DOM.pageContainer = document.querySelector('.mg-page');
        DOM.heroSection = document.querySelector('.mg-hero');
        DOM.categoriesContainer = document.querySelector('.mg-categories-wrapper');
        DOM.plansContainer = document.querySelector('.mg-plans-container');
        
        // Game selector
        DOM.gameSelector = document.querySelector('.mg-game-selector');
        DOM.gameSelectorBtn = document.querySelector('.mg-game-selector-btn');
        DOM.gameSelectorDropdown = document.querySelector('.mg-game-dropdown');
        DOM.gameOptions = document.querySelectorAll('.mg-game-option');
        DOM.selectedGameDisplay = document.querySelector('.mg-selected-game');
        
        // Category tabs
        DOM.categoryTabs = document.querySelector('.mg-category-tabs');
        DOM.categoryTabButtons = document.querySelectorAll('.mg-category-tab');
        
        // Filters & sorting
        DOM.sortSelect = document.querySelector('.mg-sort-select');
        DOM.searchInput = document.querySelector('.mg-search-input');
        DOM.filterTags = document.querySelectorAll('.mg-filter-tag');
        
        // Plan cards
        DOM.plansGrid = document.querySelector('.mg-plans-grid');
        DOM.planCards = document.querySelectorAll('.mg-plan-card');
        
        // Modal
        DOM.modalOverlay = document.querySelector('.mg-modal-overlay');
        DOM.modal = document.querySelector('.mg-modal');
        DOM.modalClose = document.querySelector('.mg-modal-close');
        DOM.modalForm = document.querySelector('.mg-modal-form');
        DOM.modalGameIcon = document.querySelector('.mg-modal-icon img');
        DOM.modalTitle = document.querySelector('.mg-modal-title');
        DOM.modalSubtitle = document.querySelector('.mg-modal-subtitle');
        DOM.playerIdInput = document.querySelector('#mg-player-id');
        DOM.submitBtn = document.querySelector('.mg-modal-btn-primary');
        
        // Summary elements
        DOM.summaryPlanName = document.querySelector('[data-summary="plan-name"]');
        DOM.summaryPlanPrice = document.querySelector('[data-summary="plan-price"]');
        DOM.summaryTotal = document.querySelector('[data-summary="total"]');
        
        // States
        DOM.emptyState = document.querySelector('.mg-empty-state');
        DOM.loadingSkeleton = document.querySelector('.mg-loading-skeleton');
    }

    /**
     * Load saved preferences from localStorage
     */
    function loadSavedPreferences() {
        try {
            // Load selected game
            const savedGame = localStorage.getItem(CONFIG.STORAGE_KEYS.SELECTED_GAME);
            if (savedGame) {
                State.selectedGame = JSON.parse(savedGame);
            }
            
            // Load selected category
            const savedCategory = localStorage.getItem(CONFIG.STORAGE_KEYS.SELECTED_CATEGORY);
            if (savedCategory) {
                State.selectedCategory = savedCategory;
            }
            
            // Load sort preference
            const savedSort = localStorage.getItem(CONFIG.STORAGE_KEYS.SORT_PREFERENCE);
            if (savedSort && CONFIG.SORT_OPTIONS[savedSort]) {
                State.currentSort = savedSort;
            }
        } catch (e) {
            console.warn('Could not load saved preferences:', e);
        }
    }

    /**
     * Save preference to localStorage
     */
    function savePreference(key, value) {
        try {
            localStorage.setItem(key, typeof value === 'object' ? JSON.stringify(value) : value);
        } catch (e) {
            console.warn('Could not save preference:', e);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // EVENT LISTENERS
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Bind all event listeners
     */
    function bindEventListeners() {
        // Game selector events
        if (DOM.gameSelectorBtn) {
            DOM.gameSelectorBtn.addEventListener('click', toggleGameDropdown);
        }
        
        // Game option selection
        DOM.gameOptions.forEach(option => {
            option.addEventListener('click', handleGameSelect);
        });
        
        // Category tab clicks
        DOM.categoryTabButtons.forEach(tab => {
            tab.addEventListener('click', handleCategorySelect);
        });
        
        // Sort select change
        if (DOM.sortSelect) {
            DOM.sortSelect.addEventListener('change', handleSortChange);
        }
        
        // Search input
        if (DOM.searchInput) {
            DOM.searchInput.addEventListener('input', debounce(handleSearch, CONFIG.DEBOUNCE_DELAY));
            DOM.searchInput.addEventListener('keydown', handleSearchKeydown);
        }
        
        // Filter tags
        DOM.filterTags.forEach(tag => {
            tag.addEventListener('click', handleFilterTagClick);
        });
        
        // Plan card clicks (buy buttons)
        document.addEventListener('click', handlePlanCardClick);
        
        // Modal events
        if (DOM.modalClose) {
            DOM.modalClose.addEventListener('click', closeModal);
        }
        
        if (DOM.modalOverlay) {
            DOM.modalOverlay.addEventListener('click', handleModalOverlayClick);
        }
        
        if (DOM.modalForm) {
            DOM.modalForm.addEventListener('submit', handleModalSubmit);
        }
        
        // Player ID input validation
        if (DOM.playerIdInput) {
            DOM.playerIdInput.addEventListener('input', handlePlayerIdInput);
            DOM.playerIdInput.addEventListener('blur', validatePlayerIdField);
        }
        
        // Keyboard events
        document.addEventListener('keydown', handleGlobalKeydown);
        
        // Click outside to close dropdown
        document.addEventListener('click', handleClickOutside);
        
        // Window resize
        window.addEventListener('resize', debounce(handleResize, 200));
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // GAME SELECTOR
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Initialize game selector component
     */
    function initGameSelector() {
        if (!DOM.gameSelector) return;
        
        // If we have a saved game, apply it
        if (State.selectedGame) {
            updateSelectedGameDisplay(State.selectedGame);
        }
        
        // Add ripple effect to game options
        DOM.gameOptions.forEach(option => {
            option.classList.add('mg-ripple-hover');
        });
    }

    /**
     * Toggle game dropdown visibility
     */
    function toggleGameDropdown(e) {
        e.stopPropagation();
        
        const isOpen = DOM.gameSelectorDropdown?.classList.contains('active');
        
        if (isOpen) {
            closeGameDropdown();
        } else {
            openGameDropdown();
        }
    }

    /**
     * Open game dropdown
     */
    function openGameDropdown() {
        if (!DOM.gameSelectorDropdown || !DOM.gameSelectorBtn) return;
        
        DOM.gameSelectorDropdown.classList.add('active');
        DOM.gameSelectorBtn.classList.add('active');
        DOM.gameSelectorBtn.setAttribute('aria-expanded', 'true');
        
        // Focus first option for accessibility
        const firstOption = DOM.gameSelectorDropdown.querySelector('.mg-game-option');
        if (firstOption) {
            firstOption.focus();
        }
    }

    /**
     * Close game dropdown
     */
    function closeGameDropdown() {
        if (!DOM.gameSelectorDropdown || !DOM.gameSelectorBtn) return;
        
        DOM.gameSelectorDropdown.classList.remove('active');
        DOM.gameSelectorBtn.classList.remove('active');
        DOM.gameSelectorBtn.setAttribute('aria-expanded', 'false');
    }

    /**
     * Handle game selection
     */
    function handleGameSelect(e) {
        const option = e.currentTarget;
        const gameId = option.dataset.gameId;
        const gameName = option.dataset.gameName;
        const gameIcon = option.dataset.gameIcon;
        const gameSlug = option.dataset.gameSlug;
        
        // Update state
        State.selectedGame = {
            id: gameId,
            name: gameName,
            icon: gameIcon,
            slug: gameSlug,
        };
        
        // Save preference
        savePreference(CONFIG.STORAGE_KEYS.SELECTED_GAME, State.selectedGame);
        
        // Update UI
        updateSelectedGameDisplay(State.selectedGame);
        
        // Mark option as selected
        DOM.gameOptions.forEach(opt => opt.classList.remove('selected'));
        option.classList.add('selected');
        
        // Close dropdown
        closeGameDropdown();
        
        // Reload plans for selected game
        loadPlansForGame(State.selectedGame);
        
        // Create ripple effect
        createRipple(e, option);
        
        // Show toast
        showToast(`بازی "${gameName}" انتخاب شد`, 'success');
    }

    /**
     * Update the selected game display
     */
    function updateSelectedGameDisplay(game) {
        if (!DOM.selectedGameDisplay) return;
        
        const iconEl = DOM.selectedGameDisplay.querySelector('.mg-selector-icon img');
        const nameEl = DOM.selectedGameDisplay.querySelector('.mg-selector-name');
        
        if (iconEl && game.icon) {
            iconEl.src = game.icon;
            iconEl.alt = game.name;
        }
        
        if (nameEl) {
            nameEl.textContent = game.name;
        }
        
        // Add selected class for styling
        DOM.gameSelector?.classList.add('has-selection');
    }

    /**
     * Load plans for selected game (API call placeholder)
     */
    function loadPlansForGame(game) {
        if (!game) return;
        
        // Show loading state
        showLoadingState();
        
        // In production, this would be an API call:
        // fetch(`${CONFIG.API.GET_PLANS}?game=${game.slug}`)
        //     .then(response => response.json())
        //     .then(data => {
        //         State.plans = data.plans;
        //         renderPlans(data.plans);
        //         hideLoadingState();
        //     })
        //     .catch(error => {
        //         console.error('Error loading plans:', error);
        //         showErrorState();
        //         hideLoadingState();
        //     });
        
        // For now, simulate loading with existing DOM content
        setTimeout(() => {
            filterPlansByGame(game.slug);
            hideLoadingState();
        }, 500);
    }

    /**
     * Filter plans by game slug
     */
    function filterPlansByGame(gameSlug) {
        if (!DOM.planCards) return;
        
        DOM.planCards.forEach(card => {
            const cardGame = card.dataset.game;
            
            if (!gameSlug || cardGame === gameSlug) {
                card.classList.remove('hidden');
                card.style.display = '';
                animateCardIn(card);
            } else {
                card.classList.add('hidden');
                card.style.display = 'none';
            }
        });
        
        // Check if we have visible cards
        checkEmptyState();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // CATEGORY TABS
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Initialize category tabs
     */
    function initCategoryTabs() {
        if (!DOM.categoryTabs) return;
        
        // Apply saved category if exists
        if (State.selectedCategory) {
            const savedTab = document.querySelector(
                `.mg-category-tab[data-category="${State.selectedCategory}"]`
            );
            if (savedTab) {
                activateCategoryTab(savedTab);
            }
        }
        
        // Initialize horizontal scroll for tabs on mobile
        initTabsHorizontalScroll();
    }

    /**
     * Handle category tab selection
     */
    function handleCategorySelect(e) {
        const tab = e.currentTarget;
        const category = tab.dataset.category;
        
        // Update state
        State.selectedCategory = category;
        
        // Save preference
        savePreference(CONFIG.STORAGE_KEYS.SELECTED_CATEGORY, category);
        
        // Update UI
        activateCategoryTab(tab);
        
        // Filter plans
        filterPlansByCategory(category);
        
        // Create ripple effect
        createRipple(e, tab);
    }

    /**
     * Activate a category tab
     */
    function activateCategoryTab(tab) {
        // Remove active from all tabs
        DOM.categoryTabButtons.forEach(t => {
            t.classList.remove('active');
            t.setAttribute('aria-selected', 'false');
        });
        
        // Add active to selected tab
        tab.classList.add('active');
        tab.setAttribute('aria-selected', 'true');
        
        // Scroll tab into view on mobile
        if (window.innerWidth < 768) {
            tab.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'center'
            });
        }
    }

    /**
     * Filter plans by category
     */
    function filterPlansByCategory(category) {
        if (!DOM.planCards) return;
        
        let visibleCount = 0;
        
        DOM.planCards.forEach(card => {
            const cardCategory = card.dataset.category;
            const cardGame = card.dataset.game;
            
            // Check both game and category filters
            const matchesGame = !State.selectedGame || cardGame === State.selectedGame.slug;
            const matchesCategory = !category || category === 'all' || cardCategory === category;
            const matchesSearch = matchesSearchQuery(card);
            
            if (matchesGame && matchesCategory && matchesSearch) {
                card.classList.remove('hidden');
                card.style.display = '';
                animateCardIn(card, visibleCount * 50);
                visibleCount++;
            } else {
                card.classList.add('hidden');
                card.style.display = 'none';
            }
        });
        
        // Check empty state
        checkEmptyState();
    }

    /**
     * Initialize horizontal scroll for category tabs
     */
    function initTabsHorizontalScroll() {
        if (!DOM.categoryTabs) return;
        
        let isDown = false;
        let startX;
        let scrollLeft;
        
        DOM.categoryTabs.addEventListener('mousedown', (e) => {
            isDown = true;
            DOM.categoryTabs.classList.add('grabbing');
            startX = e.pageX - DOM.categoryTabs.offsetLeft;
            scrollLeft = DOM.categoryTabs.scrollLeft;
        });
        
        DOM.categoryTabs.addEventListener('mouseleave', () => {
            isDown = false;
            DOM.categoryTabs.classList.remove('grabbing');
        });
        
        DOM.categoryTabs.addEventListener('mouseup', () => {
            isDown = false;
            DOM.categoryTabs.classList.remove('grabbing');
        });
        
        DOM.categoryTabs.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - DOM.categoryTabs.offsetLeft;
            const walk = (x - startX) * 2;
            DOM.categoryTabs.scrollLeft = scrollLeft - walk;
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // SORTING & FILTERING
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Initialize sort select
     */
    function initSortSelect() {
        if (!DOM.sortSelect) return;
        
        // Set saved sort preference
        if (State.currentSort) {
            DOM.sortSelect.value = State.currentSort;
        }
    }

    /**
     * Handle sort change
     */
    function handleSortChange(e) {
        const sortValue = e.target.value;
        
        // Update state
        State.currentSort = sortValue;
        
        // Save preference
        savePreference(CONFIG.STORAGE_KEYS.SORT_PREFERENCE, sortValue);
        
        // Sort and re-render plans
        sortPlans(sortValue);
        
        // Show toast
        showToast(`مرتب‌سازی: ${CONFIG.SORT_OPTIONS[sortValue]}`, 'info');
    }

    /**
     * Sort plans by criteria
     */
    function sortPlans(sortBy) {
        if (!DOM.plansGrid) return;
        
        const cards = Array.from(DOM.planCards).filter(
            card => !card.classList.contains('hidden')
        );
        
        cards.sort((a, b) => {
            const priceA = parseFloat(a.dataset.price) || 0;
            const priceB = parseFloat(b.dataset.price) || 0;
            const popularityA = parseInt(a.dataset.popularity) || 0;
            const popularityB = parseInt(b.dataset.popularity) || 0;
            const dateA = new Date(a.dataset.created) || new Date(0);
            const dateB = new Date(b.dataset.created) || new Date(0);
            
            switch (sortBy) {
                case 'price-low':
                    return priceA - priceB;
                case 'price-high':
                    return priceB - priceA;
                case 'newest':
                    return dateB - dateA;
                case 'popular':
                default:
                    return popularityB - popularityA;
            }
        });
        
        // Re-append sorted cards with animation
        cards.forEach((card, index) => {
            card.style.order = index;
            animateCardIn(card, index * 30);
        });
    }

    /**
     * Initialize search input
     */
    function initSearchInput() {
        if (!DOM.searchInput) return;
        
        // Add clear button functionality
        const clearBtn = DOM.searchInput.parentElement?.querySelector('.mg-search-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', clearSearch);
        }
    }

    /**
     * Handle search input
     */
    function handleSearch(e) {
        const query = e.target.value.trim().toLowerCase();
        
        // Update state
        State.searchQuery = query;
        
        // Toggle clear button visibility
        const clearBtn = DOM.searchInput?.parentElement?.querySelector('.mg-search-clear');
        if (clearBtn) {
            clearBtn.classList.toggle('visible', query.length > 0);
        }
        
        // Filter plans
        applyAllFilters();
    }

    /**
     * Handle search keydown (Enter key)
     */
    function handleSearchKeydown(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            applyAllFilters();
        }
        
        if (e.key === 'Escape') {
            clearSearch();
            DOM.searchInput?.blur();
        }
    }

    /**
     * Clear search
     */
    function clearSearch() {
        if (DOM.searchInput) {
            DOM.searchInput.value = '';
        }
        State.searchQuery = '';
        
        const clearBtn = DOM.searchInput?.parentElement?.querySelector('.mg-search-clear');
        if (clearBtn) {
            clearBtn.classList.remove('visible');
        }
        
        applyAllFilters();
    }

    /**
     * Check if card matches search query
     */
    function matchesSearchQuery(card) {
        if (!State.searchQuery) return true;
        
        const title = card.dataset.title?.toLowerCase() || '';
        const description = card.dataset.description?.toLowerCase() || '';
        const tags = card.dataset.tags?.toLowerCase() || '';
        
        const searchTerms = State.searchQuery.split(' ');
        
        return searchTerms.every(term => 
            title.includes(term) || 
            description.includes(term) || 
            tags.includes(term)
        );
    }

    /**
     * Handle filter tag click
     */
    function handleFilterTagClick(e) {
        const tag = e.currentTarget;
        const filterValue = tag.dataset.filter;
        
        // Toggle active state
        tag.classList.toggle('active');
        
        // Apply filters
        applyAllFilters();
        
        // Create ripple
        createRipple(e, tag);
    }

    /**
     * Apply all active filters
     */
    function applyAllFilters() {
        if (!DOM.planCards) return;
        
        let visibleCount = 0;
        
        DOM.planCards.forEach(card => {
            const matchesGame = !State.selectedGame || 
                card.dataset.game === State.selectedGame.slug;
            const matchesCategory = !State.selectedCategory || 
                State.selectedCategory === 'all' || 
                card.dataset.category === State.selectedCategory;
            const matchesSearch = matchesSearchQuery(card);
            const matchesFilters = matchesActiveFilters(card);
            
            if (matchesGame && matchesCategory && matchesSearch && matchesFilters) {
                card.classList.remove('hidden');
                card.style.display = '';
                animateCardIn(card, visibleCount * 30);
                visibleCount++;
            } else {
                card.classList.add('hidden');
                card.style.display = 'none';
            }
        });
        
        // Re-sort visible cards
        sortPlans(State.currentSort);
        
        // Check empty state
        checkEmptyState();
    }

    /**
     * Check if card matches active filter tags
     */
    function matchesActiveFilters(card) {
        const activeFilters = document.querySelectorAll('.mg-filter-tag.active');
        
        if (activeFilters.length === 0) return true;
        
        const cardTags = (card.dataset.tags || '').split(',').map(t => t.trim());
        
        return Array.from(activeFilters).some(filter => 
            cardTags.includes(filter.dataset.filter)
        );
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PLAN CARDS
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Initialize plan cards
     */
    function initPlanCards() {
        if (!DOM.planCards) return;
        
        DOM.planCards.forEach((card, index) => {
            // Add hover effects
            card.addEventListener('mouseenter', handleCardMouseEnter);
            card.addEventListener('mouseleave', handleCardMouseLeave);
            
            // Add stagger animation on load
            card.style.animationDelay = `${index * 50}ms`;
        });
    }

    /**
     * Handle plan card click events (delegation)
     */
    function handlePlanCardClick(e) {
        // Buy button click
        const buyBtn = e.target.closest('.mg-card-btn-buy');
        if (buyBtn) {
            e.preventDefault();
            const card = buyBtn.closest('.mg-plan-card');
            if (card) {
                handleBuyClick(card);
            }
            return;
        }
        
        // Add to cart button click
        const cartBtn = e.target.closest('.mg-card-btn-cart');
        if (cartBtn) {
            e.preventDefault();
            const card = cartBtn.closest('.mg-plan-card');
            if (card) {
                handleAddToCart(card);
            }
            return;
        }
        
        // Quick view button click
        const quickViewBtn = e.target.closest('.mg-card-btn-quickview');
        if (quickViewBtn) {
            e.preventDefault();
            const card = quickViewBtn.closest('.mg-plan-card');
            if (card) {
                handleQuickView(card);
            }
            return;
        }
    }

    /**
     * Handle card mouse enter
     */
    function handleCardMouseEnter(e) {
        const card = e.currentTarget;
        card.classList.add('hovered');
        
        // Parallax effect on card content
        const cardInner = card.querySelector('.mg-card-inner');
        if (cardInner) {
            cardInner.style.transform = 'translateY(-4px)';
        }
    }

    /**
     * Handle card mouse leave
     */
    function handleCardMouseLeave(e) {
        const card = e.currentTarget;
        card.classList.remove('hovered');
        
        const cardInner = card.querySelector('.mg-card-inner');
        if (cardInner) {
            cardInner.style.transform = '';
        }
    }

    /**
     * Handle buy button click
     */
    function handleBuyClick(card) {
        const planData = extractPlanData(card);
        
        if (!planData) {
            showToast('خطا در دریافت اطلاعات پلن', 'error');
            return;
        }
        
        // Update state
        State.selectedPlan = planData;
        
        // Open purchase modal
        openModal(planData);
    }

    /**
     * Handle add to cart
     */
    function handleAddToCart(card) {
        const planData = extractPlanData(card);
        
        if (!planData) {
            showToast('خطا در دریافت اطلاعات پلن', 'error');
            return;
        }
        
        // Check if already in cart
        const existingItem = State.cartItems.find(item => item.id === planData.id);
        
        if (existingItem) {
            showToast('این آیتم قبلاً به سبد خرید اضافه شده', 'warning');
            return;
        }
        
        // Add to cart state
        State.cartItems.push({
            ...planData,
            addedAt: new Date().toISOString()
        });
        
        // Animate button
        const cartBtn = card.querySelector('.mg-card-btn-cart');
        if (cartBtn) {
            cartBtn.classList.add('added');
            cartBtn.innerHTML = `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <span>اضافه شد</span>
            `;
            
            // Reset after delay
            setTimeout(() => {
                cartBtn.classList.remove('added');
                cartBtn.innerHTML = `
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
                    </svg>
                    <span>سبد خرید</span>
                `;
            }, 2000);
        }
        
        // Update cart badge
        updateCartBadge();
        
        // Show success toast
        showToast(`"${planData.title}" به سبد خرید اضافه شد`, 'success');
        
        // Optional: Send to server
        // sendToCartAPI(planData);
    }

    /**
     * Handle quick view
     */
    function handleQuickView(card) {
        const planData = extractPlanData(card);
        
        if (!planData) {
            showToast('خطا در دریافت اطلاعات', 'error');
            return;
        }
        
        // For now, open the purchase modal in preview mode
        // In production, this could open a detailed quick view modal
        openModal(planData, true); // true = preview mode
    }

    /**
     * Extract plan data from card element
     */
    function extractPlanData(card) {
        if (!card) return null;
        
        try {
            return {
                id: card.dataset.planId || card.dataset.id,
                title: card.dataset.title || card.querySelector('.mg-card-title')?.textContent?.trim(),
                price: parseFloat(card.dataset.price) || 0,
                originalPrice: parseFloat(card.dataset.originalPrice) || null,
                discount: parseInt(card.dataset.discount) || 0,
                game: card.dataset.game,
                gameTitle: card.dataset.gameTitle,
                gameIcon: card.dataset.gameIcon,
                category: card.dataset.category,
                categoryTitle: card.dataset.categoryTitle,
                description: card.dataset.description || card.querySelector('.mg-card-description')?.textContent?.trim(),
                image: card.dataset.image || card.querySelector('.mg-card-image img')?.src,
                features: JSON.parse(card.dataset.features || '[]'),
                inStock: card.dataset.inStock !== 'false',
                popularity: parseInt(card.dataset.popularity) || 0,
                tags: (card.dataset.tags || '').split(',').filter(Boolean),
            };
        } catch (error) {
            console.error('Error extracting plan data:', error);
            return null;
        }
    }

    /**
     * Update cart badge count
     */
    function updateCartBadge() {
        const cartBadge = document.querySelector('.mg-cart-badge, .cart-badge');
        
        if (cartBadge) {
            const count = State.cartItems.length;
            cartBadge.textContent = count;
            cartBadge.classList.toggle('hidden', count === 0);
            
            // Animate badge
            cartBadge.classList.add('pulse');
            setTimeout(() => cartBadge.classList.remove('pulse'), 300);
        }
    }

    /**
     * Animate card entrance
     */
    function animateCardIn(card, delay = 0) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, delay);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PURCHASE MODAL
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Initialize modal
     */
    function initModal() {
        if (!DOM.modal) return;
        
        // Add form input event listeners
        const formInputs = DOM.modal.querySelectorAll('input, select, textarea');
        formInputs.forEach(input => {
            input.addEventListener('input', handleModalInputChange);
            input.addEventListener('blur', handleModalInputBlur);
        });
    }

    /**
     * Open purchase modal
     */
    function openModal(planData, previewMode = false) {
        if (!DOM.modalOverlay || !DOM.modal) return;
        
        // Update state
        State.selectedPlan = planData;
        State.isModalOpen = true;
        
        // Populate modal with plan data
        populateModal(planData, previewMode);
        
        // Show modal
        DOM.modalOverlay.classList.add('active');
        DOM.modal.classList.add('active');
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
        document.body.classList.add('modal-open');
        
        // Focus first input
        setTimeout(() => {
            const firstInput = DOM.modal.querySelector('input:not([type="hidden"])');
            if (firstInput) {
                firstInput.focus();
            }
        }, CONFIG.ANIMATION_DURATION);
        
        // Track modal open
        trackEvent('modal_open', { plan_id: planData.id, plan_title: planData.title });
    }

    /**
     * Close modal
     */
    function closeModal() {
        if (!DOM.modalOverlay || !DOM.modal) return;
        
        // Update state
        State.isModalOpen = false;
        State.isSubmitting = false;
        
        // Hide modal
        DOM.modalOverlay.classList.remove('active');
        DOM.modal.classList.remove('active');
        
        // Restore body scroll
        document.body.style.overflow = '';
        document.body.classList.remove('modal-open');
        
        // Reset form
        if (DOM.modalForm) {
            DOM.modalForm.reset();
            clearFormErrors();
        }
        
        // Clear selected plan after animation
        setTimeout(() => {
            State.selectedPlan = null;
        }, CONFIG.ANIMATION_DURATION);
    }

    /**
     * Populate modal with plan data
     */
    function populateModal(planData, previewMode = false) {
        if (!planData) return;
        
        // Game icon
        if (DOM.modalGameIcon && planData.gameIcon) {
            DOM.modalGameIcon.src = planData.gameIcon;
            DOM.modalGameIcon.alt = planData.gameTitle || '';
        }
        
        // Title
        if (DOM.modalTitle) {
            DOM.modalTitle.textContent = planData.title;
        }
        
        // Subtitle (game name + category)
        if (DOM.modalSubtitle) {
            DOM.modalSubtitle.textContent = `${planData.gameTitle || ''} - ${planData.categoryTitle || ''}`;
        }
        
        // Plan name in summary
        if (DOM.summaryPlanName) {
            DOM.summaryPlanName.textContent = planData.title;
        }
        
        // Price display
        const priceFormatted = formatPrice(planData.price);
        
        if (DOM.summaryPlanPrice) {
            DOM.summaryPlanPrice.textContent = priceFormatted;
        }
        
        // Original price (if discounted)
        const originalPriceEl = DOM.modal?.querySelector('[data-summary="original-price"]');
        if (originalPriceEl) {
            if (planData.originalPrice && planData.originalPrice > planData.price) {
                originalPriceEl.textContent = formatPrice(planData.originalPrice);
                originalPriceEl.classList.remove('hidden');
            } else {
                originalPriceEl.classList.add('hidden');
            }
        }
        
        // Discount badge
        const discountBadge = DOM.modal?.querySelector('.mg-modal-discount');
        if (discountBadge) {
            if (planData.discount > 0) {
                discountBadge.textContent = `${planData.discount}% تخفیف`;
                discountBadge.classList.remove('hidden');
            } else {
                discountBadge.classList.add('hidden');
            }
        }
        
        // Total price
        if (DOM.summaryTotal) {
            DOM.summaryTotal.textContent = priceFormatted;
        }
        
        // Features list
        const featuresContainer = DOM.modal?.querySelector('.mg-modal-features');
        if (featuresContainer && planData.features) {
            featuresContainer.innerHTML = planData.features.map(feature => `
                <li class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-emerald-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                    </svg>
                    <span class="text-slate-300 text-sm">${escapeHtml(feature)}</span>
                </li>
            `).join('');
        }
        
        // Set plan ID in hidden field
        const planIdInput = DOM.modal?.querySelector('input[name="plan_id"]');
        if (planIdInput) {
            planIdInput.value = planData.id;
        }
        
        // Update button text based on mode
        if (DOM.submitBtn) {
            if (previewMode) {
                DOM.submitBtn.textContent = 'خرید این پلن';
                DOM.submitBtn.dataset.mode = 'preview';
            } else {
                DOM.submitBtn.innerHTML = `
                    <span>تأیید و پرداخت</span>
                    <span class="mg-btn-price">${priceFormatted}</span>
                `;
                DOM.submitBtn.dataset.mode = 'purchase';
            }
        }
        
        // Show/hide player ID field based on game requirements
        const playerIdGroup = DOM.modal?.querySelector('.mg-player-id-group');
        if (playerIdGroup) {
            // Some games require player ID, some don't
            const requiresPlayerId = !['voucher', 'giftcard'].includes(planData.category);
            playerIdGroup.classList.toggle('hidden', !requiresPlayerId);
            
            if (DOM.playerIdInput) {
                DOM.playerIdInput.required = requiresPlayerId;
            }
        }
    }

    /**
     * Handle modal overlay click
     */
    function handleModalOverlayClick(e) {
        if (e.target === DOM.modalOverlay) {
            closeModal();
        }
    }

    /**
     * Handle modal form submission
     */
    function handleModalSubmit(e) {
        e.preventDefault();
        
        if (State.isSubmitting) return;
        
        // Validate form
        if (!validateModalForm()) {
            return;
        }
        
        // Get form data
        const formData = new FormData(DOM.modalForm);
        const data = Object.fromEntries(formData.entries());
        
        // Add plan data
        data.plan = State.selectedPlan;
        
        // Submit purchase
        submitPurchase(data);
    }

    /**
     * Validate modal form
     */
    function validateModalForm() {
        let isValid = true;
        clearFormErrors();
        
        // Validate player ID if required
        if (DOM.playerIdInput && DOM.playerIdInput.required) {
            const playerId = DOM.playerIdInput.value.trim();
            
            if (!playerId) {
                showFieldError(DOM.playerIdInput, 'لطفاً آیدی بازیکن را وارد کنید');
                isValid = false;
            } else if (!CONFIG.VALIDATION.PLAYER_ID.test(playerId)) {
                showFieldError(DOM.playerIdInput, 'فرمت آیدی بازیکن نامعتبر است');
                isValid = false;
            }
        }
        
        // Validate email if present
        const emailInput = DOM.modal?.querySelector('input[name="email"]');
        if (emailInput && emailInput.value) {
            if (!CONFIG.VALIDATION.EMAIL.test(emailInput.value)) {
                showFieldError(emailInput, 'فرمت ایمیل نامعتبر است');
                isValid = false;
            }
        }
        
        // Validate phone if present
        const phoneInput = DOM.modal?.querySelector('input[name="phone"]');
        if (phoneInput && phoneInput.value) {
            if (!CONFIG.VALIDATION.PHONE.test(phoneInput.value)) {
                showFieldError(phoneInput, 'شماره موبایل باید ۱۱ رقم و با ۰۹ شروع شود');
                isValid = false;
            }
        }
        
        return isValid;
    }

    /**
     * Handle player ID input
     */
    function handlePlayerIdInput(e) {
        const input = e.target;
        const value = input.value;
        
        // Remove invalid characters
        input.value = value.replace(/[^a-zA-Z0-9_-]/g, '');
        
        // Clear error on input
        clearFieldError(input);
    }

    /**
     * Validate player ID field on blur
     */
    function validatePlayerIdField(e) {
        const input = e.target;
        const value = input.value.trim();
        
        if (input.required && !value) {
            showFieldError(input, 'این فیلد الزامی است');
        } else if (value && !CONFIG.VALIDATION.PLAYER_ID.test(value)) {
            showFieldError(input, 'فقط حروف انگلیسی، اعداد، خط تیره و آندرلاین مجاز است');
        } else {
            clearFieldError(input);
        }
    }

    /**
     * Clear all form errors
     */
    function clearFormErrors() {
        if (!DOM.modal) return;
        
        DOM.modal.querySelectorAll('.mg-input-error').forEach(err => err.remove());
        DOM.modal.querySelectorAll('.input-error').forEach(el => el.classList.remove('input-error'));
    }

    /**
     * Show field error
     */
    function showFieldError(input, message) {
        clearFieldError(input);
        
        input.classList.add('input-error');
        
        const error = document.createElement('div');
        error.className = 'mg-input-error text-red-400 text-xs mt-1 flex items-center gap-1';
        error.innerHTML = `
            <svg class="w-3 h-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            <span>${message}</span>
        `;
        
        input.parentElement.appendChild(error);
        
        // Shake animation
        input.classList.add('shake');
        setTimeout(() => input.classList.remove('shake'), 500);
    }

    /**
     * Clear single field error
     */
    function clearFieldError(input) {
        input.classList.remove('input-error');
        const err = input.parentElement?.querySelector('.mg-input-error');
        if (err) err.remove();
    }

    /**
     * Handle modal input change
     */
    function handleModalInputChange(e) {
        const input = e.target;
        clearFieldError(input);
        
        // Handle discount code separately
        if (input.name === 'discount_code') {
            debouncedDiscountCheck(input.value);
        }
        
        // Live validation for specific fields
        if (input.name === 'email' && input.value) {
            if (!CONFIG.VALIDATION.EMAIL.test(input.value)) {
                // Don't show error immediately, wait for blur
            }
        }
    }

    /**
     * Handle modal input blur
     */
    function handleModalInputBlur(e) {
        const input = e.target;
        const value = input.value.trim();
        
        switch (input.name) {
            case 'player_id':
                if (input.required || value) {
                    validatePlayerIdField(e);
                }
                break;
                
            case 'email':
                if (value && !CONFIG.VALIDATION.EMAIL.test(value)) {
                    showFieldError(input, 'فرمت ایمیل نامعتبر است');
                }
                break;
                
            case 'phone':
                if (value && !CONFIG.VALIDATION.PHONE.test(value)) {
                    showFieldError(input, 'شماره موبایل باید ۱۱ رقم و با ۰۹ شروع شود');
                }
                break;
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // DISCOUNT CODE
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Debounced discount code check
     */
    const debouncedDiscountCheck = debounce(checkDiscountCode, 500);

    /**
     * Check discount code validity
     */
    async function checkDiscountCode(code) {
        if (!State.selectedPlan) return;
        
        const discountInput = DOM.modal?.querySelector('input[name="discount_code"]');
        const discountStatus = DOM.modal?.querySelector('.mg-discount-status');
        
        if (!code || code.length < 3) {
            // Reset to original price
            updatePriceSummary(State.selectedPlan.price, null);
            if (discountStatus) {
                discountStatus.classList.add('hidden');
            }
            State.appliedDiscount = null;
            return;
        }
        
        // Show loading state
        if (discountStatus) {
            discountStatus.classList.remove('hidden');
            discountStatus.innerHTML = `
                <span class="text-slate-400 text-sm flex items-center gap-2">
                    <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                    در حال بررسی...
                </span>
            `;
        }
        
        try {
            // API call to validate discount code
            const response = await fetch(CONFIG.API.VALIDATE_DISCOUNT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: JSON.stringify({
                    code: code,
                    plan_id: State.selectedPlan.id,
                }),
            });
            
            const result = await response.json();
            
            if (result.valid) {
                // Apply discount
                State.appliedDiscount = {
                    code: code,
                    type: result.type, // 'percent' or 'fixed'
                    value: result.value,
                };
                
                const discountedPrice = calculateDiscountedPrice(
                    State.selectedPlan.price,
                    result.type,
                    result.value
                );
                
                updatePriceSummary(discountedPrice, State.selectedPlan.price);
                
                if (discountStatus) {
                    discountStatus.innerHTML = `
                        <span class="text-emerald-400 text-sm flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                            ${result.message || 'کد تخفیف اعمال شد'}
                        </span>
                    `;
                }
                
                if (discountInput) {
                    discountInput.classList.add('border-emerald-500');
                }
                
            } else {
                // Invalid code
                State.appliedDiscount = null;
                updatePriceSummary(State.selectedPlan.price, null);
                
                if (discountStatus) {
                    discountStatus.innerHTML = `
                        <span class="text-red-400 text-sm flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                            ${result.message || 'کد تخفیف نامعتبر است'}
                        </span>
                    `;
                }
                
                if (discountInput) {
                    discountInput.classList.remove('border-emerald-500');
                }
            }
            
        } catch (error) {
            console.error('Discount validation error:', error);
            
            // Fallback: Simple local validation for demo
            handleLocalDiscountValidation(code, discountStatus, discountInput);
        }
    }

    /**
     * Fallback local discount validation (for demo/development)
     */
    function handleLocalDiscountValidation(code, statusEl, inputEl) {
        const demoDiscounts = {
            'WELCOME10': { type: 'percent', value: 10, message: '۱۰٪ تخفیف خوش‌آمدگویی' },
            'PUBG20': { type: 'percent', value: 20, message: '۲۰٪ تخفیف پابجی' },
            'FREEFIRE15': { type: 'percent', value: 15, message: '۱۵٪ تخفیف فری فایر' },
            'FLAT5000': { type: 'fixed', value: 5000, message: '۵,۰۰۰ تومان تخفیف' },
        };
        
        const discount = demoDiscounts[code.toUpperCase()];
        
        if (discount) {
            State.appliedDiscount = { code, ...discount };
            
            const discountedPrice = calculateDiscountedPrice(
                State.selectedPlan.price,
                discount.type,
                discount.value
            );
            
            updatePriceSummary(discountedPrice, State.selectedPlan.price);
            
            if (statusEl) {
                statusEl.innerHTML = `
                    <span class="text-emerald-400 text-sm flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                        </svg>
                        ${discount.message}
                    </span>
                `;
            }
            
            if (inputEl) inputEl.classList.add('border-emerald-500');
            
        } else {
            State.appliedDiscount = null;
            updatePriceSummary(State.selectedPlan.price, null);
            
            if (statusEl) {
                statusEl.innerHTML = `
                    <span class="text-red-400 text-sm flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                        کد تخفیف نامعتبر است
                    </span>
                `;
            }
            
            if (inputEl) inputEl.classList.remove('border-emerald-500');
        }
    }

    /**
     * Calculate discounted price
     */
    function calculateDiscountedPrice(originalPrice, discountType, discountValue) {
        if (discountType === 'percent') {
            return originalPrice * (1 - discountValue / 100);
        } else if (discountType === 'fixed') {
            return Math.max(0, originalPrice - discountValue);
        }
        return originalPrice;
    }

    /**
     * Update price summary in modal
     */
    function updatePriceSummary(finalPrice, originalPrice = null) {
        // Update total
        if (DOM.summaryTotal) {
            DOM.summaryTotal.textContent = formatPrice(finalPrice);
        }
        
        // Update original price display
        const originalPriceEl = DOM.modal?.querySelector('[data-summary="original-price"]');
        if (originalPriceEl) {
            if (originalPrice && originalPrice > finalPrice) {
                originalPriceEl.textContent = formatPrice(originalPrice);
                originalPriceEl.classList.remove('hidden');
            } else {
                originalPriceEl.classList.add('hidden');
            }
        }
        
        // Update discount amount display
        const discountAmountEl = DOM.modal?.querySelector('[data-summary="discount-amount"]');
        if (discountAmountEl) {
            if (originalPrice && originalPrice > finalPrice) {
                const savings = originalPrice - finalPrice;
                discountAmountEl.textContent = `-${formatPrice(savings)}`;
                discountAmountEl.parentElement?.classList.remove('hidden');
            } else {
                discountAmountEl.parentElement?.classList.add('hidden');
            }
        }
        
        // Update submit button price
        if (DOM.submitBtn) {
            const priceSpan = DOM.submitBtn.querySelector('.mg-btn-price');
            if (priceSpan) {
                priceSpan.textContent = formatPrice(finalPrice);
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // FORM SUBMISSION
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Submit purchase to server
     */
    async function submitPurchase(formData) {
        State.isSubmitting = true;
        
        // Update button state
        if (DOM.submitBtn) {
            DOM.submitBtn.disabled = true;
            DOM.submitBtn.classList.add('loading');
            DOM.submitBtn.innerHTML = `
                <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                <span>در حال پردازش...</span>
            `;
        }
        
        try {
            const payload = {
                plan_id: State.selectedPlan.id,
                player_id: formData.player_id || null,
                email: formData.email || null,
                phone: formData.phone || null,
                discount_code: State.appliedDiscount?.code || null,
            };
            
            const response = await fetch(CONFIG.API.SUBMIT_ORDER, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: JSON.stringify(payload),
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Success - redirect to payment
                showToast('در حال انتقال به درگاه پرداخت...', 'success');
                closeModal();
                
                if (result.redirect_url) {
                    setTimeout(() => {
                        window.location.href = result.redirect_url;
                    }, 1500);
                }
                
            } else {
                // Error from server
                showToast(result.message || 'خطا در ثبت سفارش', 'error');
                resetSubmitButton();
            }
            
        } catch (error) {
            console.error('Submit error:', error);
            showToast('خطا در ارتباط با سرور', 'error');
            resetSubmitButton();
        }
        
        State.isSubmitting = false;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // INITIALIZE ON DOM READY
    // ═══════════════════════════════════════════════════════════════════════════

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
