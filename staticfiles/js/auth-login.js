/**
 * OTP Login Page JavaScript
 * Handles phone number validation and OTP request
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('loginForm');
    const phoneInput = document.getElementById('phone');
    const submitBtn = document.getElementById('submitBtn');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    
    // Phone input formatting - only allow digits
    phoneInput.addEventListener('input', function(e) {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length > 11) {
            value = value.slice(0, 11);
        }
        e.target.value = value;
        
        // Remove error styling when user starts typing
        if (errorMessage.classList.contains('show')) {
            errorMessage.classList.remove('show');
        }
    });
    
    // Phone input validation on blur
    phoneInput.addEventListener('blur', function() {
        const phone = this.value.trim();
        if (phone && !/^09\d{9}$/.test(phone)) {
            showError('شماره موبایل باید با ۰۹ شروع شده و ۱۱ رقم باشد');
        }
    });
    
    // Show error message
    function showError(message) {
        errorText.textContent = message;
        errorMessage.classList.add('show');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorMessage.classList.remove('show');
        }, 5000);
    }
    
    // Validate phone number
    function validatePhone(phone) {
        if (!phone) {
            return 'لطفاً شماره موبایل را وارد کنید';
        }
        
        if (!/^09\d{9}$/.test(phone)) {
            return 'شماره موبایل باید با ۰۹ شروع شده و ۱۱ رقم باشد';
        }
        
        return null;
    }
    
    // Form submission handler
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const phone = phoneInput.value.trim();
        
        // Validate phone number
        const validationError = validatePhone(phone);
        if (validationError) {
            showError(validationError);
            phoneInput.focus();
            return;
        }
        
        // Disable form during submission
        submitBtn.disabled = true;
        submitBtn.classList.add('loading');
        phoneInput.disabled = true;
        
        try {
            // Get CSRF token from cookie
            const csrfToken = document.cookie
                .split('; ')
                .find(row => row.startsWith('csrftoken='))
                ?.split('=')[1] || '';

            if (!csrfToken) {
                console.error('❌ CSRF token not found in cookies!');
                showError('خطای امنیتی - لطفاً صفحه را رفرش کنید');
                submitBtn.disabled = false;
                submitBtn.classList.remove('loading');
                phoneInput.disabled = false;
                return;
            }

            console.log('✅ Using CSRF Token:', csrfToken.substring(0, 10) + '...');
            
            // Send OTP request with correct CSRF header
            const response = await fetch(form.action || window.location.href, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,  // Django accepts this
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                body: JSON.stringify({ phone: phone })
            });
            
            // Check if response is actually JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Response is not JSON:', await response.text());
                if (response.status === 403) {
                    showError('خطای CSRF - لطفاً صفحه را رفرش کنید');
                } else {
                    showError('خطای سرور - لطفاً دوباره تلاش کنید');
                }
                submitBtn.disabled = false;
                submitBtn.classList.remove('loading');
                phoneInput.disabled = false;
                return;
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Success - redirect to verification page
                window.location.href = data.redirect_url || '/accounts/verify/';
            } else {
                // Show error message
                showError(data.message || 'خطایی رخ داد. لطفاً دوباره تلاش کنید');
                
                // Re-enable form
                submitBtn.disabled = false;
                submitBtn.classList.remove('loading');
                phoneInput.disabled = false;
                phoneInput.focus();
                
                // If there's a wait time, show countdown
                if (data.wait_seconds) {
                    let waitTime = data.wait_seconds;
                    const countdown = setInterval(() => {
                        waitTime--;
                        if (waitTime <= 0) {
                            clearInterval(countdown);
                            submitBtn.disabled = false;
                        } else {
                            submitBtn.disabled = true;
                            errorText.textContent = `لطفاً ${waitTime} ثانیه صبر کنید`;
                        }
                    }, 1000);
                }
            }
        } catch (error) {
            console.error('Login error:', error);
            showError('خطا در ارتباط با سرور. لطفاً اتصال اینترنت خود را بررسی کنید');
            
            // Re-enable form
            submitBtn.disabled = false;
            submitBtn.classList.remove('loading');
            phoneInput.disabled = false;
            phoneInput.focus();
        }
    });
    
    // Allow Enter key to submit
    phoneInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            submitBtn.click(); // Simulate button click - most reliable
        }
    });
});
