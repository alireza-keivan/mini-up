// static/js/auth-verify.js

/**
 * OTP Verification Page JavaScript
 * Handles OTP input and verification
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('verifyForm');
    const otpInputs = document.querySelectorAll('.otp-input');
    const submitBtn = document.getElementById('submitBtn');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    const resendBtn = document.getElementById('resendBtn');
    const timerElement = document.getElementById('timer');
    
    // Get phone from hidden input or data attribute
    const phoneInput = document.getElementById('phone');
    const phone = phoneInput ? phoneInput.value : '';
    
    // ═══════════════════════════════════════════════════════════════════════════
    // CSRF TOKEN HELPER
    // ═══════════════════════════════════════════════════════════════════════════
    
    function getCookie(name) {
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
    }
    
    const csrftoken = getCookie('csrftoken');
    
    // ═══════════════════════════════════════════════════════════════════════════
    // OTP INPUT HANDLING
    // ═══════════════════════════════════════════════════════════════════════════
    
    // Auto-focus first input
    if (otpInputs.length > 0) {
        otpInputs[0].focus();
    }
    
    otpInputs.forEach(function(input, index) {
        // Only allow numbers
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            if (value.length > 1) {
                value = value.charAt(0);
            }
            
            e.target.value = value;
            
            // Auto-focus next input
            if (value && index < otpInputs.length - 1) {
                otpInputs[index + 1].focus();
            }
            
            // Hide error when typing
            hideError();
            
            // Auto-submit when all filled
            if (isOTPComplete()) {
                // Small delay for better UX
                setTimeout(() => {
                    if (isOTPComplete()) {
                        form.dispatchEvent(new Event('submit'));
                    }
                }, 200);
            }
        });
        
        // Handle backspace
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Backspace' && !e.target.value && index > 0) {
                otpInputs[index - 1].focus();
            }
        });
        
        // Handle paste
        input.addEventListener('paste', function(e) {
            e.preventDefault();
            const pastedData = e.clipboardData.getData('text').replace(/\D/g, '');
            
            otpInputs.forEach(function(inp, i) {
                if (pastedData[i]) {
                    inp.value = pastedData[i];
                }
            });
            
            // Focus last filled or next empty
            const lastIndex = Math.min(pastedData.length, otpInputs.length) - 1;
            if (lastIndex >= 0) {
                otpInputs[Math.min(lastIndex + 1, otpInputs.length - 1)].focus();
            }
            
            // Auto-submit if complete
            if (isOTPComplete()) {
                setTimeout(() => form.dispatchEvent(new Event('submit')), 200);
            }
        });
    });
    
    // ═══════════════════════════════════════════════════════════════════════════
    // HELPER FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════
    
    function getOTPCode() {
        let code = '';
        otpInputs.forEach(function(input) {
            code += input.value;
        });
        return code;
    }
    
    function isOTPComplete() {
        return getOTPCode().length === otpInputs.length;
    }
    
    function showError(message) {
        if (errorText) errorText.textContent = message;
        if (errorMessage) errorMessage.classList.add('show');
        
        // Shake animation on inputs
        otpInputs.forEach(function(input) {
            input.classList.add('error');
        });
        
        setTimeout(function() {
            otpInputs.forEach(function(input) {
                input.classList.remove('error');
            });
        }, 500);
    }
    
    function hideError() {
        if (errorMessage) errorMessage.classList.remove('show');
    }
    
    function clearOTP() {
        otpInputs.forEach(function(input) {
            input.value = '';
        });
        otpInputs[0].focus();
    }
    
    function setLoading(loading) {
        if (submitBtn) {
            submitBtn.disabled = loading;
            if (loading) {
                submitBtn.classList.add('loading');
            } else {
                submitBtn.classList.remove('loading');
            }
        }
        
        otpInputs.forEach(function(input) {
            input.disabled = loading;
        });
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // FORM SUBMISSION
    // ═══════════════════════════════════════════════════════════════════════════
    
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const code = getOTPCode();
            
            // Validate OTP
            if (code.length !== otpInputs.length) {
                showError('لطفاً کد را کامل وارد کنید');
                return;
            }
            
            setLoading(true);
            
            try {
                const response = await fetch('/accounts/verify/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        phone: phone,
                        code: code
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Success - show message and redirect
                    if (window.showToast) {
                        showToast(data.message || 'ورود موفق!', 'success');
                    }
                    
                    // Redirect after short delay
                    setTimeout(function() {
                        window.location.href = data.redirect_url || '/';
                    }, 500);
                    
                } else {
                    // Error
                    showError(data.message || 'کد وارد شده صحیح نیست');
                    setLoading(false);
                    
                    // Clear inputs for retry
                    if (data.clear_code !== false) {
                        clearOTP();
                    }
                }
                
            } catch (error) {
                console.error('Verify error:', error);
                showError('خطا در برقراری ارتباط با سرور');
                setLoading(false);
            }
        });
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // RESEND OTP TIMER
    // ═══════════════════════════════════════════════════════════════════════════
    
    let resendTimer = null;
    let remainingTime = 120; // 2 minutes
    
    function startResendTimer() {
        if (resendBtn) resendBtn.disabled = true;
        
        resendTimer = setInterval(function() {
            remainingTime--;
            
            if (timerElement) {
                const minutes = Math.floor(remainingTime / 60);
                const seconds = remainingTime % 60;
                timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            }
            
            if (remainingTime <= 0) {
                clearInterval(resendTimer);
                if (resendBtn) {
                    resendBtn.disabled = false;
                    resendBtn.textContent = 'ارسال مجدد کد';
                }
                if (timerElement) {
                    timerElement.textContent = '';
                }
            }
        }, 1000);
    }
    
    // Start timer on page load
    startResendTimer();
    
    // ═══════════════════════════════════════════════════════════════════════════
    // RESEND OTP
    // ═══════════════════════════════════════════════════════════════════════════
    
    if (resendBtn) {
        resendBtn.addEventListener('click', async function() {
            if (this.disabled) return;
            
            this.disabled = true;
            this.textContent = 'در حال ارسال...';
            
            try {
                const response = await fetch('/accounts/login/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        phone: phone
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    if (window.showToast) {
                        showToast('کد جدید ارسال شد', 'success');
                    }
                    
                    // Reset timer
                    remainingTime = data.wait_seconds || 120;
                    startResendTimer();
                    
                    // Clear old code
                    clearOTP();
                    
                } else {
                    showError(data.message || 'خطا در ارسال کد');
                    this.disabled = false;
                    this.textContent = 'ارسال مجدد کد';
                }
                
            } catch (error) {
                console.error('Resend error:', error);
                showError('خطا در برقراری ارتباط');
                this.disabled = false;
                this.textContent = 'ارسال مجدد کد';
            }
        });
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // KEYBOARD SHORTCUTS
    // ═══════════════════════════════════════════════════════════════════════════
    
    document.addEventListener('keydown', function(e) {
        // Submit on Enter
        if (e.key === 'Enter' && isOTPComplete()) {
            form.dispatchEvent(new Event('submit'));
        }
    });
    
});
