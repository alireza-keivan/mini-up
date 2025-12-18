/**
 * Profile Page JavaScript
 * Mini-up.ir - Neon Dark Theme
 * 
 * Features:
 * - Tab switching with smooth animations
 * - Modal management (cards, addresses)
 * - Form validations
 * - Bank card detection
 * - OTP handling for security
 * - Toast notifications
 */

(function() {
    'use strict';

    // ═══════════════════════════════════════════════════════════════════════════
    // CONFIGURATION
    // ═══════════════════════════════════════════════════════════════════════════

    const CONFIG = {
        animationDuration: 300,
        toastDuration: 3000,
        otpLength: 6,
        pinLength: 4,
        cardNumberLength: 16,
        phoneRegex: /^09[0-9]{9}$/,
        emailRegex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        postalCodeRegex: /^[0-9]{10}$/,
        nationalCodeRegex: /^[0-9]{10}$/
    };

    // Bank BIN codes for detection
    const BANK_BINS = {
        '603799': { name: 'بانک ملی ایران', color: '#004d99' },
        '589210': { name: 'بانک سپه', color: '#fdb913' },
        '627648': { name: 'بانک توسعه صادرات', color: '#00a651' },
        '603770': { name: 'بانک کشاورزی', color: '#00a650' },
        '628023': { name: 'بانک مسکن', color: '#f7941d' },
        '627412': { name: 'بانک اقتصاد نوین', color: '#662d91' },
        '622106': { name: 'بانک پارسیان', color: '#c4161c' },
        '502229': { name: 'بانک پاسارگاد', color: '#f9a825' },
        '621986': { name: 'بانک سامان', color: '#009fe3' },
        '639346': { name: 'بانک سینا', color: '#1a3c6e' },
        '502806': { name: 'بانک شهر', color: '#e91c24' },
        '603769': { name: 'بانک صادرات', color: '#0066b3' },
        '610433': { name: 'بانک ملت', color: '#d42177' },
        '627353': { name: 'بانک تجارت', color: '#009bdb' },
        '589463': { name: 'بانک رفاه', color: '#004b87' },
        '627381': { name: 'بانک انصار', color: '#00a651' },
        '639607': { name: 'بانک سرمایه', color: '#0072bc' },
        '636214': { name: 'بانک آینده', color: '#6d2077' },
        '636949': { name: 'بانک حکمت ایرانیان', color: '#00aeef' },
        '505416': { name: 'بانک گردشگری', color: '#e31e24' },
        '639599': { name: 'بانک قوامین', color: '#0066b3' },
        '504172': { name: 'بانک رسالت', color: '#009245' },
        '505801': { name: 'موسسه کوثر', color: '#00a14b' },
        '606373': { name: 'موسسه مهر ایران', color: '#006838' },
        '639370': { name: 'بانک مهر اقتصاد', color: '#00a651' },
        '585983': { name: 'بانک تجارت', color: '#009bdb' },
        '639347': { name: 'بانک پاسارگاد', color: '#f9a825' },
        '627488': { name: 'بانک کارآفرین', color: '#00aeef' },
        '502910': { name: 'بانک کارآفرین', color: '#00aeef' },
        '603770': { name: 'بانک کشاورزی', color: '#00a650' },
        '627760': { name: 'پست بانک', color: '#006600' },
        '585949': { name: 'بانک تجارت', color: '#009bdb' },
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // DOM ELEMENTS
    // ═══════════════════════════════════════════════════════════════════════════

    const elements = {
        // Tab elements
        tabButtons: document.querySelectorAll('[data-tab-btn]'),
        tabContents: document.querySelectorAll('[data-tab-content]'),
        
        // Modals
        addCardModal: document.getElementById('addCardModal'),
        addAddressModal: document.getElementById('addAddressModal'),
        changePinModal: document.getElementById('changePinModal'),
        enable2faModal: document.getElementById('enable2faModal'),
        
        // Card form elements
        cardNumberInput: document.getElementById('cardNumberInput'),
        bankNameDisplay: document.getElementById('bankNameDisplay'),
        bankLogoDisplay: document.getElementById('bankLogoDisplay'),
        
        // PIN inputs
        pinInputs: document.querySelectorAll('.pin-input'),
        otpInputs: document.querySelectorAll('.otp-input'),
        
        // Forms
        profileInfoForm: document.getElementById('profileInfoForm'),
        addCardForm: document.getElementById('addCardForm'),
        addAddressForm: document.getElementById('addAddressForm'),
        changePinForm: document.getElementById('changePinForm'),
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // TAB MANAGEMENT
    // ═══════════════════════════════════════════════════════════════════════════

    const TabManager = {
        init() {
            if (elements.tabButtons.length === 0) return;

            elements.tabButtons.forEach(btn => {
                btn.addEventListener('click', (e) => this.switchTab(e));
            });

            // Check URL hash for initial tab
            this.checkUrlHash();

            // Listen for hash changes
            window.addEventListener('hashchange', () => this.checkUrlHash());
        },

        switchTab(e) {
            const targetTab = e.currentTarget.dataset.tabBtn;
            if (!targetTab) return;

            // Update buttons
            elements.tabButtons.forEach(btn => {
                btn.classList.remove('active', 'bg-cyan-500/20', 'text-cyan-400', 'border-cyan-500/50');
                btn.classList.add('text-gray-400', 'hover:text-white', 'hover:bg-white/5');
            });

            e.currentTarget.classList.add('active', 'bg-cyan-500/20', 'text-cyan-400', 'border-cyan-500/50');
            e.currentTarget.classList.remove('text-gray-400', 'hover:text-white', 'hover:bg-white/5');

            // Update content panels
            elements.tabContents.forEach(content => {
                if (content.dataset.tabContent === targetTab) {
                    content.classList.remove('hidden');
                    content.classList.add('animate-fade-in');
                } else {
                    content.classList.add('hidden');
                    content.classList.remove('animate-fade-in');
                }
            });

            // Update URL hash without scrolling
            history.replaceState(null, null, '#' + targetTab);
        },

        checkUrlHash() {
            const hash = window.location.hash.replace('#', '');
            if (hash) {
                const targetBtn = document.querySelector(`[data-tab-btn="${hash}"]`);
                if (targetBtn) {
                    targetBtn.click();
                }
            }
        },

        goToTab(tabName) {
            const targetBtn = document.querySelector(`[data-tab-btn="${tabName}"]`);
            if (targetBtn) {
                targetBtn.click();
            }
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // MODAL MANAGEMENT
    // ═══════════════════════════════════════════════════════════════════════════

    const ModalManager = {
        activeModal: null,

        open(modalId) {
            const modal = document.getElementById(modalId);
            if (!modal) return;

            modal.classList.remove('hidden');
            modal.classList.add('flex');
            document.body.style.overflow = 'hidden';
            this.activeModal = modal;

            // Focus first input
            setTimeout(() => {
                const firstInput = modal.querySelector('input:not([type="hidden"]), select, textarea');
                if (firstInput) firstInput.focus();
            }, 100);

            // Add escape key listener
            document.addEventListener('keydown', this.handleEscape);
        },

        close(modalId) {
            const modal = modalId ? document.getElementById(modalId) : this.activeModal;
            if (!modal) return;

            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.style.overflow = '';
            this.activeModal = null;

            // Remove escape key listener
            document.removeEventListener('keydown', this.handleEscape);

            // Reset forms inside modal
            const form = modal.querySelector('form');
            if (form) form.reset();
        },

        handleEscape(e) {
            if (e.key === 'Escape') {
                ModalManager.close();
            }
        },

        init() {
            // Close modal when clicking overlay
            document.querySelectorAll('[data-modal-overlay]').forEach(overlay => {
                overlay.addEventListener('click', (e) => {
                    if (e.target === overlay) {
                        this.close();
                    }
                });
            });

            // Close buttons
            document.querySelectorAll('[data-modal-close]').forEach(btn => {
                btn.addEventListener('click', () => this.close());
            });
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // BANK CARD UTILITIES
    // ═══════════════════════════════════════════════════════════════════════════

    const BankCardUtils = {
        init() {
            if (elements.cardNumberInput) {
                elements.cardNumberInput.addEventListener('input', (e) => this.handleCardInput(e));
                elements.cardNumberInput.addEventListener('paste', (e) => this.handleCardPaste(e));
            }
        },

        handleCardInput(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = value.substring(0, CONFIG.cardNumberLength);
            
            // Format with dashes
            const formatted = value.replace(/(\d{4})(?=\d)/g, '$1 - ');
            e.target.value = formatted;

            // Detect bank
            if (value.length >= 6) {
                this.detectAndDisplayBank(value.substring(0, 6));
            } else {
                this.clearBankDisplay();
            }

            // Validate
            this.validateCardNumber(value);
        },

        handleCardPaste(e) {
            e.preventDefault();
            const pasteData = e.clipboardData.getData('text').replace(/\D/g, '');
            e.target.value = pasteData.substring(0, CONFIG.cardNumberLength);
            e.target.dispatchEvent(new Event('input'));
        },

        detectBank(bin) {
            return BANK_BINS[bin] || null;
        },

        detectAndDisplayBank(bin) {
            const bank = this.detectBank(bin);
            
            if (elements.bankNameDisplay) {
                elements.bankNameDisplay.textContent = bank ? bank.name : 'بانک نامشخص';
                elements.bankNameDisplay.style.color = bank ? bank.color : '#888';
            }

            if (elements.bankLogoDisplay && bank) {
                elements.bankLogoDisplay.style.borderColor = bank.color;
            }
        },

        clearBankDisplay() {
            if (elements.bankNameDisplay) {
                elements.bankNameDisplay.textContent = '';
            }
        },

        validateCardNumber(number) {
            const digits = number.replace(/\D/g, '');
            
            if (digits.length !== 16) {
                return { valid: false, message: 'شماره کارت باید ۱۶ رقم باشد' };
            }

            // Luhn algorithm validation
            if (!this.luhnCheck(digits)) {
                return { valid: false, message: 'شماره کارت نامعتبر است' };
            }

            return { valid: true, message: '' };
        },

        luhnCheck(cardNumber) {
            let sum = 0;
            let isEven = false;

            for (let i = cardNumber.length - 1; i >= 0; i--) {
                let digit = parseInt(cardNumber[i], 10);

                if (isEven) {
                    digit *= 2;
                    if (digit > 9) {
                        digit -= 9;
                    }
                }

                sum += digit;
                isEven = !isEven;
            }

            return sum % 10 === 0;
        },

        formatCardNumber(number) {
            const digits = number.replace(/\D/g, '');
            return digits.replace(/(\d{4})(?=\d)/g, '$1 - ');
        },

        maskCardNumber(number) {
            const digits = number.replace(/\D/g, '');
            if (digits.length < 16) return number;
            return digits.substring(0, 4) + ' **** **** ' + digits.substring(12);
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // PIN/OTP INPUT HANDLER
    // ═══════════════════════════════════════════════════════════════════════════

    const PinOtpHandler = {
        init() {
            this.setupPinInputs();
            this.setupOtpInputs();
        },

        setupPinInputs() {
            const pinContainers = document.querySelectorAll('.pin-container');
            
            pinContainers.forEach(container => {
                const inputs = container.querySelectorAll('.pin-input');
                this.setupInputGroup(inputs, CONFIG.pinLength);
            });
        },

        setupOtpInputs() {
            const otpContainers = document.querySelectorAll('.otp-container');
            
            otpContainers.forEach(container => {
                const inputs = container.querySelectorAll('.otp-input');
                this.setupInputGroup(inputs, CONFIG.otpLength);
            });
        },

        setupInputGroup(inputs, maxLength) {
            inputs.forEach((input, index) => {
                // Only allow numbers
                input.addEventListener('input', (e) => {
                    e.target.value = e.target.value.replace(/\D/g, '').substring(0, 1);
                    
                    if (e.target.value.length === 1) {
                        e.target.classList.add('filled');
                        // Move to next input
                        if (index < inputs.length - 1) {
                            inputs[index + 1].focus();
                        }
                    } else {
                        e.target.classList.remove('filled');
                    }
                });

                // Handle navigation
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Backspace' && e.target.value === '' && index > 0) {
                        inputs[index - 1].focus();
                        inputs[index - 1].value = '';
                        inputs[index - 1].classList.remove('filled');
                    }
                    if (e.key === 'ArrowLeft' && index > 0) {
                        inputs[index - 1].focus();
                    }
                    if (e.key === 'ArrowRight' && index < inputs.length - 1) {
                        inputs[index + 1].focus();
                    }
                });

                input.addEventListener('paste', (e) => {
                    e.preventDefault();
                    const data = (e.clipboardData.getData('text') || '').replace(/\D/g, '');
                    for (let i = 0; i < Math.min(data.length, inputs.length); i++) {
                        inputs[i].value = data[i];
                        inputs[i].classList.add('filled');
                    }
                });
            });
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // FORM VALIDATION HELPERS
    // ═══════════════════════════════════════════════════════════════════════════

    const FormUtils = {
        isValidPhone(value) {
            return CONFIG.phoneRegex.test(value);
        },
        isValidEmail(value) {
            return CONFIG.emailRegex.test(value);
        },
        isValidPostalCode(value) {
            return CONFIG.postalCodeRegex.test(value);
        },
        showError(input, msg) {
            showToast(msg, 'error');
            input.classList.add('border-red-500');
            setTimeout(() => input.classList.remove('border-red-500'), 2000);
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // TOAST GLOBAL FUNCTION (Fallback if main.js not loaded)
    // ═══════════════════════════════════════════════════════════════════════════

    function showToast(message, type = 'info', duration = CONFIG.toastDuration) {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'fixed bottom-4 left-4 z-50 flex flex-col gap-2';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        const typeClass = {
            success: 'bg-green-500/90 text-white',
            error: 'bg-red-500/90 text-white',
            info: 'bg-cyan-500/90 text-white',
            warning: 'bg-yellow-500/90 text-black'
        }[type];

        toast.className = `toast-item px-4 py-3 rounded-lg shadow-lg transform translate-x-full transition-transform duration-300 ${typeClass}`;
        toast.textContent = message;
        container.appendChild(toast);

        requestAnimationFrame(() => (toast.style.transform = 'translateX(0)'));
        setTimeout(() => {
            toast.style.transform = 'translateX(-100%)';
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // INITIALIZATION
    // ═══════════════════════════════════════════════════════════════════════════

    document.addEventListener('DOMContentLoaded', () => {
        TabManager.init();
        ModalManager.init();
        BankCardUtils.init();
        PinOtpHandler.init();

        console.log('⚙️ profile.js initialized');
    });

})();
