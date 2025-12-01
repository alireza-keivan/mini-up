// ═══════════════════════════════════════════════════════════════════════════════
// AUTHENTICATION SYSTEM
// ═══════════════════════════════════════════════════════════════════════════════

(function() {
    'use strict';

    // ─────────────────────────────────────────────────────────────────────────
    // AUTH DOM ELEMENTS
    // ─────────────────────────────────────────────────────────────────────────
    
    const authTabs = document.querySelectorAll('.auth-tab');
    const authPanels = document.querySelectorAll('.auth-panel');
    const backButtons = document.querySelectorAll('.back-btn');
    
    // Login elements
    const loginInput = document.getElementById('login-input');
    const loginSendCodeBtn = document.getElementById('login-send-code');
    const loginSubmitBtn = document.getElementById('login-submit');
    const loginResendBtn = document.getElementById('login-resend');
    const loginOtpTarget = document.getElementById('login-otp-target');
    const loginTimerMinute = document.getElementById('login-timer-minute');
    const loginTimerSecond = document.getElementById('login-timer-second');
    const loginExpired = document.getElementById('login-expired');
    
    // Register elements
    const registerInput = document.getElementById('register-input');
    const registerSendCodeBtn = document.getElementById('register-send-code');
    const registerSubmitBtn = document.getElementById('register-submit');
    const registerResendBtn = document.getElementById('register-resend');
    const registerOtpTarget = document.getElementById('register-otp-target');
    const registerTimerMinute = document.getElementById('register-timer-minute');
    const registerTimerSecond = document.getElementById('register-timer-second');
    const registerExpired = document.getElementById('register-expired');

    // Timer intervals storage
    let loginTimerInterval = null;
    let registerTimerInterval = null;

    // ─────────────────────────────────────────────────────────────────────────
    // VALIDATION PATTERNS
    // ─────────────────────────────────────────────────────────────────────────
    
    // Iranian mobile: starts with 09, total 11 digits
    const PHONE_REGEX = /^09[0-9]{9}$/;
    
    // Email validation
    const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    /**
     * Validate if input is a valid phone number or email
     * @param {string} value - Input value
     * @returns {object} - { valid: boolean, type: 'phone'|'email'|null }
     */
    function validateInput(value) {
        const trimmed = value.trim();
        
        if (PHONE_REGEX.test(trimmed)) {
            return { valid: true, type: 'phone', value: trimmed };
        }
        
        if (EMAIL_REGEX.test(trimmed)) {
            return { valid: true, type: 'email', value: trimmed };
        }
        
        return { valid: false, type: null, value: trimmed };
    }

    /**
     * Format phone number for display
     * @param {string} phone - Phone number
     * @returns {string} - Formatted phone like +98 912 xxx xxxx
     */
    function formatPhone(phone) {
        if (phone.startsWith('0')) {
            phone = '+98' + phone.substring(1);
        }
        return phone;
    }

    // ─────────────────────────────────────────────────────────────────────────
    // TAB SWITCHING
    // ─────────────────────────────────────────────────────────────────────────
    
    if (authTabs.length > 0) {
        authTabs.forEach(function(tab) {
            tab.addEventListener('click', function() {
                const targetTab = this.dataset.tab;
                
                // Update tab active states
                authTabs.forEach(function(t) {
                    t.classList.remove('active');
                });
                this.classList.add('active');
                
                // Update panel visibility
                authPanels.forEach(function(panel) {
                    panel.classList.remove('active');
                });
                
                const targetPanel = document.getElementById('panel-' + targetTab);
                if (targetPanel) {
                    targetPanel.classList.add('active');
                    
                    // Reset to step 1 when switching tabs
                    resetPanelToStep1(targetPanel);
                }
            });
        });
    }

    /**
     * Reset panel to step 1
     * @param {HTMLElement} panel - The auth panel element
     */
    function resetPanelToStep1(panel) {
        const steps = panel.querySelectorAll('.auth-step');
        steps.forEach(function(step, index) {
            if (index === 0) {
                step.classList.add('active');
            } else {
                step.classList.remove('active');
            }
        });
        
        // Clear OTP inputs
        const otpInputs = panel.querySelectorAll('.otp-input');
        otpInputs.forEach(function(input) {
            input.value = '';
            input.classList.remove('filled');
        });
    }

    // ─────────────────────────────────────────────────────────────────────────
    // STEP NAVIGATION
    // ─────────────────────────────────────────────────────────────────────────
    
    /**
     * Navigate to a specific step
     * @param {string} panelId - Panel ID (panel-login or panel-register)
     * @param {number} stepNumber - Step number (1, 2, or 3)
     */
    function goToStep(panelId, stepNumber) {
        const panel = document.getElementById(panelId);
        if (!panel) return;
        
        const steps = panel.querySelectorAll('.auth-step');
        const prefix = panelId === 'panel-login' ? 'login' : 'register';
        
        steps.forEach(function(step) {
            step.classList.remove('active');
        });
        
        const targetStep = document.getElementById(prefix + '-step-' + stepNumber);
        if (targetStep) {
            targetStep.classList.add('active');
        }
    }

    // Back button handlers
    if (backButtons.length > 0) {
        backButtons.forEach(function(btn) {
            btn.addEventListener('click', function() {
                const targetStepId = this.dataset.back;
                if (!targetStepId) return;
                
                // Find parent panel
                const panel = this.closest('.auth-panel');
                if (!panel) return;
                
                // Hide current step
                const currentStep = this.closest('.auth-step');
                if (currentStep) {
                    currentStep.classList.remove('active');
                }
                
                // Show target step
                const targetStep = document.getElementById(targetStepId);
                if (targetStep) {
                    targetStep.classList.add('active');
                }
                
                // Clear timers
                if (panel.id === 'panel-login' && loginTimerInterval) {
                    clearInterval(loginTimerInterval);
                    loginTimerInterval = null;
                }
                if (panel.id === 'panel-register' && registerTimerInterval) {
                    clearInterval(registerTimerInterval);
                    registerTimerInterval = null;
                }
            });
        });
    }

    // ─────────────────────────────────────────────────────────────────────────
    // OTP INPUT HANDLING
    // ─────────────────────────────────────────────────────────────────────────
    
    const otpContainers = document.querySelectorAll('.otp-container');
    
    otpContainers.forEach(function(container) {
        const inputs = container.querySelectorAll('.otp-input');
        
        inputs.forEach(function(input, index) {
            // Only allow numbers
            input.addEventListener('input', function(e) {
                // Remove non-numeric characters
                this.value = this.value.replace(/[^0-9]/g, '');
                
                if (this.value.length === 1) {
                    this.classList.add('filled');
                    
                    // Auto-focus next input
                    if (index < inputs.length - 1) {
                        inputs[index + 1].focus();
                    }
                } else {
                    this.classList.remove('filled');
                }
            });
            
            // Handle backspace
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Backspace' && this.value === '' && index > 0) {
                    inputs[index - 1].focus();
                    inputs[index - 1].value = '';
                    inputs[index - 1].classList.remove('filled');
                }
                
                // Handle arrow keys
                if (e.key === 'ArrowLeft' && index < inputs.length - 1) {
                    e.preventDefault();
                    inputs[index + 1].focus();
                }
                if (e.key === 'ArrowRight' && index > 0) {
                    e.preventDefault();
                    inputs[index - 1].focus();
                }
            });
            
            // Handle paste
            input.addEventListener('paste', function(e) {
                e.preventDefault();
                const pasteData = e.clipboardData.getData('text').replace(/[^0-9]/g, '');
                
                for (let i = 0; i < Math.min(pasteData.length, inputs.length); i++) {
                    inputs[i].value = pasteData[i];
                    inputs[i].classList.add('filled');
                }
                
                // Focus last filled or next empty
                const focusIndex = Math.min(pasteData.length, inputs.length - 1);
                inputs[focusIndex].focus();
            });
            
            // Select all on focus
            input.addEventListener('focus', function() {
                this.select();
            });
        });
    });

    /**
     * Get OTP value from a container
     * @param {HTMLElement} container - OTP container element
     * @returns {string} - Concatenated OTP value
     */
    function getOtpValue(container) {
        const inputs = container.querySelectorAll('.otp-input');
        let otp = '';
        inputs.forEach(function(input) {
            otp += input.value;
        });
        return otp;
    }

    /**
     * Clear OTP inputs in a container
     * @param {HTMLElement} container - OTP container element
     */
    function clearOtpInputs(container) {
        const inputs = container.querySelectorAll('.otp-input');
        inputs.forEach(function(input) {
            input.value = '';
            input.classList.remove('filled');
        });
        if (inputs.length > 0) {
            inputs[0].focus();
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // TIMER FUNCTIONALITY
    // ─────────────────────────────────────────────────────────────────────────
    
    /**
     * Start countdown timer
     * @param {object} options - Timer options
     * @param {HTMLElement} options.minuteEl - Minutes display element
     * @param {HTMLElement} options.secondEl - Seconds display element
     * @param {HTMLElement} options.expiredEl - Expired message element
     * @param {HTMLElement} options.resendBtn - Resend button element
     * @param {number} options.duration - Timer duration in seconds (default 120)
     * @param {function} options.onExpire - Callback when timer expires
     * @returns {number} - Interval ID
     */
    function startTimer(options) {
        const {
            minuteEl,
            secondEl,
            expiredEl,
            resendBtn,
            duration = 120,
            onExpire
        } = options;
        
        let timeLeft = duration;
        
        // Reset UI
        if (expiredEl) expiredEl.classList.add('hidden');
        if (resendBtn) resendBtn.disabled = true;
        
        // Update display immediately
        updateTimerDisplay(timeLeft, minuteEl, secondEl);
        
        const interval = setInterval(function() {
            timeLeft--;
            updateTimerDisplay(timeLeft, minuteEl, secondEl);
            
            if (timeLeft <= 0) {
                clearInterval(interval);
                
                // Show expired state
                if (expiredEl) expiredEl.classList.remove('hidden');
                if (resendBtn) resendBtn.disabled = false;
                
                if (onExpire) onExpire();
            }
        }, 1000);
        
        return interval;
    }

    /**
     * Update timer display
     * @param {number} timeLeft - Time left in seconds
     * @param {HTMLElement} minuteEl - Minutes element
     * @param {HTMLElement} secondEl - Seconds element
     */
    function updateTimerDisplay(timeLeft, minuteEl, secondEl) {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        
        if (minuteEl) minuteEl.textContent = String(minutes).padStart(2, '0');
        if (secondEl) secondEl.textContent = String(seconds).padStart(2, '0');
    }

    // ─────────────────────────────────────────────────────────────────────────
    // LOGIN FLOW
    // ─────────────────────────────────────────────────────────────────────────
    
    // Send code button
    if (loginSendCodeBtn && loginInput) {
        loginSendCodeBtn.addEventListener('click', function() {
            const validation = validateInput(loginInput.value);
            
            if (!validation.valid) {
                loginInput.classList.add('error');
                showToast('لطفاً شماره موبایل یا ایمیل معتبر وارد کنید', 'error');
                return;
            }
            
            loginInput.classList.remove('error');
            
            // Show loading state
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="auth-loading"></span> در حال ارسال...';
            this.disabled = true;
            
            // Simulate API call (replace with actual API)
            setTimeout(function() {
                loginSendCodeBtn.innerHTML = originalText;
                loginSendCodeBtn.disabled = false;
                
                // Update OTP target display
                if (loginOtpTarget) {
                    loginOtpTarget.textContent = validation.type === 'phone' 
                        ? formatPhone(validation.value) 
                        : validation.value;
                }
                
                // Go to step 2
                goToStep('panel-login', 2);
                
                // Start timer
                if (loginTimerInterval) clearInterval(loginTimerInterval);
                loginTimerInterval = startTimer({
                    minuteEl: loginTimerMinute,
                    secondEl: loginTimerSecond,
                    expiredEl: loginExpired,
                    resendBtn: loginResendBtn,
                    duration: 120
                });
                
                // Focus first OTP input
                const firstOtpInput = document.querySelector('#login-step-2 .otp-input');
                if (firstOtpInput) {
                    setTimeout(function() { firstOtpInput.focus(); }, 100);
                }
                
                showToast('کد تأیید ارسال شد', 'success');
                
            }, 1500);
        });
    }

    // Resend code button
    if (loginResendBtn) {
        loginResendBtn.addEventListener('click', function() {
            if (this.disabled) return;
            
            // Show loading state
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="auth-loading"></span> در حال ارسال...';
            this.disabled = true;
            
            // Clear existing OTP inputs
            const otpContainer = document.querySelector('#login-step-2 .otp-container');
            if (otpContainer) {
                clearOtpInputs(otpContainer);
            }
            
            // Simulate API call (replace with actual API)
            setTimeout(function() {
                loginResendBtn.innerHTML = originalText;
                
                // Hide expired message
                if (loginExpired) loginExpired.classList.add('hidden');
                
                // Restart timer
                if (loginTimerInterval) clearInterval(loginTimerInterval);
                loginTimerInterval = startTimer({
                    minuteEl: loginTimerMinute,
                    secondEl: loginTimerSecond,
                    expiredEl: loginExpired,
                    resendBtn: loginResendBtn,
                    duration: 120
                });
                
                showToast('کد تأیید مجدداً ارسال شد', 'success');
                
            }, 1500);
        });
    }

    // Login submit button (verify OTP)
    if (loginSubmitBtn) {
        loginSubmitBtn.addEventListener('click', function() {
            const otpContainer = document.querySelector('#login-step-2 .otp-container');
            if (!otpContainer) return;
            
            const otp = getOtpValue(otpContainer);
            
            if (otp.length !== 6) {
                showToast('لطفاً کد ۶ رقمی را کامل وارد کنید', 'error');
                return;
            }
            
            // Show loading state
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="auth-loading"></span> در حال تأیید...';
            this.disabled = true;
            
            // Simulate API call (replace with actual API)
            setTimeout(function() {
                loginSubmitBtn.innerHTML = originalText;
                loginSubmitBtn.disabled = false;
                
                // Clear timer
                if (loginTimerInterval) {
                    clearInterval(loginTimerInterval);
                    loginTimerInterval = null;
                }
                
                // Go to success step
                goToStep('panel-login', 3);
                
                showToast('ورود موفقیت‌آمیز!', 'success');
                
                // Redirect after delay (replace with actual redirect)
                setTimeout(function() {
                    // window.location.href = '/dashboard/';
                    console.log('Redirecting to dashboard...');
                }, 2000);
                
            }, 1500);
        });
    }

    // ─────────────────────────────────────────────────────────────────────────
    // REGISTER FLOW
    // ─────────────────────────────────────────────────────────────────────────
    
    // Send code button (Register)
    if (registerSendCodeBtn && registerInput) {
        registerSendCodeBtn.addEventListener('click', function() {
            const validation = validateInput(registerInput.value);
            
            if (!validation.valid) {
                registerInput.classList.add('error');
                showToast('لطفاً شماره موبایل یا ایمیل معتبر وارد کنید', 'error');
                return;
            }
            
            registerInput.classList.remove('error');
            
            // Show loading state
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="auth-loading"></span> در حال ارسال...';
            this.disabled = true;
            
            // Simulate API call (replace with actual API)
            setTimeout(function() {
                registerSendCodeBtn.innerHTML = originalText;
                registerSendCodeBtn.disabled = false;
                
                // Update OTP target display
                if (registerOtpTarget) {
                    registerOtpTarget.textContent = validation.type === 'phone' 
                        ? formatPhone(validation.value) 
                        : validation.value;
                }
                
                // Go to step 2
                goToStep('panel-register', 2);
                
                // Start timer
                if (registerTimerInterval) clearInterval(registerTimerInterval);
                registerTimerInterval = startTimer({
                    minuteEl: registerTimerMinute,
                    secondEl: registerTimerSecond,
                    expiredEl: registerExpired,
                    resendBtn: registerResendBtn,
                    duration: 120
                });
                
                // Focus first OTP input
                const firstOtpInput = document.querySelector('#register-step-2 .otp-input');
                if (firstOtpInput) {
                    setTimeout(function() { firstOtpInput.focus(); }, 100);
                }
                
                showToast('کد تأیید ارسال شد', 'success');
                
            }, 1500);
        });
    }

    // Resend code button (Register)
    if (registerResendBtn) {
        registerResendBtn.addEventListener('click', function() {
            if (this.disabled) return;
            
            // Show loading state
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="auth-loading"></span> در حال ارسال...';
            this.disabled = true;
            
            // Clear existing OTP inputs
            const otpContainer = document.querySelector('#register-step-2 .otp-container');
            if (otpContainer) {
                clearOtpInputs(otpContainer);
            }
            
            // Simulate API call (replace with actual API)
            setTimeout(function() {
                registerResendBtn.innerHTML = originalText;
                
                // Hide expired message
                if (registerExpired) registerExpired.classList.add('hidden');
                
                // Restart timer
                if (registerTimerInterval) clearInterval(registerTimerInterval);
                registerTimerInterval = startTimer({
                    minuteEl: registerTimerMinute,
                    secondEl: registerTimerSecond,
                    expiredEl: registerExpired,
                    resendBtn: registerResendBtn,
                    duration: 120
                });
                
                showToast('کد تأیید مجدداً ارسال شد', 'success');
                
            }, 1500);
        });
    }

    // Register submit button (verify OTP)
    if (registerSubmitBtn) {
        registerSubmitBtn.addEventListener('click', function() {
            const otpContainer = document.querySelector('#register-step-2 .otp-container');
            if (!otpContainer) return;
            
            const otp = getOtpValue(otpContainer);
            
            if (otp.length !== 6) {
                showToast('لطفاً کد ۶ رقمی را کامل وارد کنید', 'error');
                return;
            }
            
            // Show loading state
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="auth-loading"></span> در حال تأیید...';
            this.disabled = true;
            
            // Simulate API call (replace with actual API)
            setTimeout(function() {
                registerSubmitBtn.innerHTML = originalText;
                registerSubmitBtn.disabled = false;
                
                // Clear timer
                if (registerTimerInterval) {
                    clearInterval(registerTimerInterval);
                    registerTimerInterval = null;
                }
                
                // Go to success step
                goToStep('panel-register', 3);
                
                showToast('ثبت‌نام موفقیت‌آمیز!', 'success');
                
                // Redirect after delay (replace with actual redirect)
                setTimeout(function() {
                    // window.location.href = '/dashboard/';
                    console.log('Redirecting to dashboard...');
                }, 2000);
                
            }, 1500);
        });
    }

    // ─────────────────────────────────────────────────────────────────────────
    // INPUT VALIDATION ON TYPING
    // ─────────────────────────────────────────────────────────────────────────
    
    // Real-time validation for login input
    if (loginInput) {
        loginInput.addEventListener('input', function() {
            this.classList.remove('error');
            const validation = validateInput(this.value);
            
            if (this.value.length > 0) {
                if (validation.valid) {
                    this.classList.add('valid');
                    this.classList.remove('invalid');
                } else {
                    this.classList.remove('valid');
                    // Don't show invalid until blur or submit
                }
            } else {
                this.classList.remove('valid', 'invalid');
            }
        });
        
        loginInput.addEventListener('blur', function() {
            if (this.value.length > 0) {
                const validation = validateInput(this.value);
                if (!validation.valid) {
                    this.classList.add('invalid');
                }
            }
        });
        
        // Enter key to submit
        loginInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (loginSendCodeBtn) loginSendCodeBtn.click();
            }
        });
    }

    // Real-time validation for register input
    if (registerInput) {
        registerInput.addEventListener('input', function() {
            this.classList.remove('error');
            const validation = validateInput(this.value);
            
            if (this.value.length > 0) {
                if (validation.valid) {
                    this.classList.add('valid');
                    this.classList.remove('invalid');
                } else {
                    this.classList.remove('valid');
                }
            } else {
                this.classList.remove('valid', 'invalid');
            }
        });
        
        registerInput.addEventListener('blur', function() {
            if (this.value.length > 0) {
                const validation = validateInput(this.value);
                if (!validation.valid) {
                    this.classList.add('invalid');
                }
            }
        });
        
        // Enter key to submit
        registerInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (registerSendCodeBtn) registerSendCodeBtn.click();
            }
        });
    }

    // ─────────────────────────────────────────────────────────────────────────
    // AUTH MODAL FUNCTIONALITY (For header login button)
    // ─────────────────────────────────────────────────────────────────────────
    
    const authModal = document.getElementById('auth-modal');
    const authModalOverlay = document.getElementById('auth-modal-overlay');
    const authModalClose = document.getElementById('auth-modal-close');
    const openAuthModalBtns = document.querySelectorAll('[data-open-auth-modal]');

    /**
     * Open auth modal
     */
    function openAuthModal() {
        if (!authModal) return;
        
        authModal.classList.add('active');
        if (authModalOverlay) authModalOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Focus first input
        const firstInput = authModal.querySelector('input[type="text"], input[type="email"], input[type="tel"]');
        if (firstInput) {
            setTimeout(function() { firstInput.focus(); }, 100);
        }
    }

    /**
     * Close auth modal
     */
    function closeAuthModal() {
        if (!authModal) return;
        
        authModal.classList.remove('active');
        if (authModalOverlay) authModalOverlay.classList.remove('active');
        document.body.style.overflow = '';
        
        // Reset to first step and clear inputs
        const panels = authModal.querySelectorAll('.auth-panel');
        panels.forEach(function(panel) {
            resetPanelToStep1(panel);
            
            // Clear text inputs
            const textInputs = panel.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"]');
            textInputs.forEach(function(input) {
                input.value = '';
                input.classList.remove('valid', 'invalid', 'error');
            });
        });
        
        // Reset tabs
        const tabs = authModal.querySelectorAll('.auth-tab');
        tabs.forEach(function(tab, index) {
            if (index === 0) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
        
        // Reset panels
        panels.forEach(function(panel, index) {
            if (index === 0) {
                panel.classList.add('active');
            } else {
                panel.classList.remove('active');
            }
        });
        
        // Clear timers
        if (loginTimerInterval) {
            clearInterval(loginTimerInterval);
            loginTimerInterval = null;
        }
        if (registerTimerInterval) {
            clearInterval(registerTimerInterval);
            registerTimerInterval = null;
        }
    }

    // Event listeners for modal
    openAuthModalBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            openAuthModal();
        });
    });

    if (authModalClose) {
        authModalClose.addEventListener('click', closeAuthModal);
    }

    if (authModalOverlay) {
        authModalOverlay.addEventListener('click', closeAuthModal);
    }

    // Close modal on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && authModal && authModal.classList.contains('active')) {
            closeAuthModal();
        }
    });

    // ─────────────────────────────────────────────────────────────────────────
    // FORM SUBMIT PREVENTION (For standalone login page forms)
    // ─────────────────────────────────────────────────────────────────────────
    
    const authForms = document.querySelectorAll('.auth-form');
    authForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
        });
    });

    // ─────────────────────────────────────────────────────────────────────────
    // NEON GLOW EFFECT ON INPUT FOCUS
    // ─────────────────────────────────────────────────────────────────────────
    
    const neonInputs = document.querySelectorAll('.neon-input');
    neonInputs.forEach(function(input) {
        const wrapper = input.closest('.input-wrapper');
        
        input.addEventListener('focus', function() {
            if (wrapper) wrapper.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (wrapper) wrapper.classList.remove('focused');
        });
    });

    // ─────────────────────────────────────────────────────────────────────────
    // EXPOSE FUNCTIONS GLOBALLY (Optional - for external use)
    // ─────────────────────────────────────────────────────────────────────────
    
    window.MiniUpAuth = {
        openModal: openAuthModal,
        closeModal: closeAuthModal,
        validateInput: validateInput,
        goToStep: goToStep
    };

    // ─────────────────────────────────────────────────────────────────────────
    // INITIALIZATION LOG
    // ─────────────────────────────────────────────────────────────────────────
    
    console.log('🔐 Mini-up Auth System initialized');

})();
