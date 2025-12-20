function dashboard() {
    return {
        activeTab: 'info',
        saving: false,
        depositProcessing: false,
        showAddAddressModal: false,
        showAddCardModal: false,
        submittingAddress: false,
        submittingCard: false,
        
        // User Data - Will be set by Django template
        userData: {
            first_name: '',
            last_name: '',
            national_code: ''
        },

        // Wallet Data - Will be set by Django template
        walletData: {
            balance: 0,
            gift_balance: 0
        },

        // Deposit Data
        depositData: {
            amount: null,
            gateway: 'zarinpal'
        },

        // Address Form Data
        addressForm: {
            title: '',
            recipient_name: '',
            recipient_phone: '',
            province: '',
            city: '',
            postal_code: '',
            full_address: '',
            is_default: false
        },

        // Bank Card Form Data
        cardForm: {
            card_number: '',
            bank_name: '',
            is_default: false
        },

        // Security Form Data
        securityForm: {
            current_password: '',
            new_password: '',
            confirm_password: ''
        },

        changingPassword: false,

        // Initialize component
        init() {
            // Check URL hash and switch to appropriate tab
            this.checkHashAndSwitchTab();
            
            // Listen for hash changes (browser back/forward)
            window.addEventListener('hashchange', () => {
                this.checkHashAndSwitchTab();
            });
        },

        // Check URL hash and switch tab
        checkHashAndSwitchTab() {
            const hash = window.location.hash.substring(1); // Remove #
            const validTabs = ['info', 'bank', 'security', 'addresses'];
            
            if (hash && validTabs.includes(hash)) {
                this.activeTab = hash;
            }
        },

        // Switch tab and update URL hash
        switchTab(tab) {
            this.activeTab = tab;
            window.history.pushState(null, '', '#' + tab);
        },

        // Format currency helper
        formatCurrency(amount) {
            return new Intl.NumberFormat('fa-IR').format(amount) + ' تومان';
        },

        // Set deposit amount from quick buttons
        setDepositAmount(amount) {
            this.depositData.amount = amount;
        },

        // Save personal info
        async savePersonalInfo() {
            this.saving = true;

            try {
                const csrfToken = this.getCSRFToken();

                const response = await fetch(window.dashboardUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        action: 'update_profile',
                        ...this.userData
                    })
                });

                const data = await response.json();

                if (data.success) {
                    this.showNotification('✅ تغییرات با موفقیت ذخیره شد', 'success');
                    
                    // Update displayed values
                    if (data.user) {
                        this.userData.first_name = data.user.first_name;
                        this.userData.last_name = data.user.last_name;
                    }
                } else {
                    this.showNotification('❌ ' + (data.message || 'خطا در ذخیره اطلاعات'), 'error');
                }
            } catch (error) {
                console.error('Save error:', error);
                this.showNotification('❌ خطا در ارتباط با سرور', 'error');
            } finally {
                this.saving = false;
            }
        },

        // Process wallet deposit
        async processDeposit() {
            const amount = parseInt(this.depositData.amount);

            // Validation
            if (!amount || amount < 10000) {
                this.showNotification('❌ حداقل مبلغ شارژ ۱۰,۰۰۰ تومان است', 'error');
                return;
            }

            if (amount > 50000000) {
                this.showNotification('❌ حداکثر مبلغ شارژ ۵۰,۰۰۰,۰۰۰ تومان است', 'error');
                return;
            }

            this.depositProcessing = true;

            try {
                const csrfToken = this.getCSRFToken();

                const response = await fetch(window.dashboardUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        action: 'wallet_deposit',
                        amount: amount,
                        gateway: this.depositData.gateway
                    })
                });

                const data = await response.json();

                if (data.success && data.payment_url) {
                    this.showNotification('✅ در حال انتقال به درگاه پرداخت...', 'success');
                    // Redirect to payment gateway
                    setTimeout(() => {
                        window.location.href = data.payment_url;
                    }, 1000);
                } else {
                    this.showNotification('❌ ' + (data.message || 'خطا در ایجاد درخواست پرداخت'), 'error');
                    this.depositProcessing = false;
                }
            } catch (error) {
                console.error('Deposit error:', error);
                this.showNotification('❌ خطا در ارتباط با سرور', 'error');
                this.depositProcessing = false;
            }
        },

        // Submit Address
        async submitAddress() {
            // Validate phone number
            if (!/^09\d{9}$/.test(this.addressForm.recipient_phone)) {
                this.showNotification('❌ شماره تماس باید با ۰۹ شروع شده و ۱۱ رقم باشد', 'error');
                return;
            }

            // Validate postal code
            if (!/^\d{10}$/.test(this.addressForm.postal_code)) {
                this.showNotification('❌ کد پستی باید ۱۰ رقم باشد', 'error');
                return;
            }

            this.submittingAddress = true;

            try {
                const csrfToken = this.getCSRFToken();

                const response = await fetch(window.dashboardUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        action: 'add_address',
                        ...this.addressForm
                    })
                });

                const data = await response.json();

                if (data.success) {
                    this.showNotification('✅ آدرس با موفقیت ذخیره شد', 'success');
                    this.showAddAddressModal = false;
                    // Reset form
                    this.addressForm = {
                        title: '',
                        recipient_name: '',
                        recipient_phone: '',
                        province: '',
                        city: '',
                        postal_code: '',
                        full_address: '',
                        is_default: false
                    };
                    // Reload to show new address
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    this.showNotification('❌ ' + (data.message || 'خطا در ذخیره آدرس'), 'error');
                }
            } catch (error) {
                console.error('Address error:', error);
                this.showNotification('❌ خطا در ارتباط با سرور', 'error');
            } finally {
                this.submittingAddress = false;
            }
        },

        // Submit Bank Card
        async submitBankCard() {
            // Validate card number (must be 16 digits)
            if (!/^\d{16}$/.test(this.cardForm.card_number)) {
                this.showNotification('❌ شماره کارت باید ۱۶ رقم باشد', 'error');
                return;
            }

            this.submittingCard = true;

            try {
                const csrfToken = this.getCSRFToken();

                const response = await fetch(window.dashboardUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        action: 'add_bank_card',
                        ...this.cardForm
                    })
                });

                const data = await response.json();

                if (data.success) {
                    this.showNotification('✅ کارت بانکی با موفقیت ذخیره شد', 'success');
                    this.showAddCardModal = false;
                    // Reset form
                    this.cardForm = {
                        card_number: '',
                        bank_name: '',
                        is_default: false
                    };
                    // Reload to show new card
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    this.showNotification('❌ ' + (data.message || 'خطا در ذخیره کارت'), 'error');
                }
            } catch (error) {
                console.error('Card error:', error);
                this.showNotification('❌ خطا در ارتباط با سرور', 'error');
            } finally {
                this.submittingCard = false;
            }
        },

        // Upload avatar
        async uploadAvatar(event) {
            const file = event.target.files[0];
            if (!file) return;

            // Validate file type
            if (!file.type.startsWith('image/')) {
                this.showNotification('❌ لطفا یک فایل تصویری انتخاب کنید', 'error');
                return;
            }

            // Validate file size (max 5MB)
            if (file.size > 5 * 1024 * 1024) {
                this.showNotification('❌ حجم فایل نباید بیشتر از ۵ مگابایت باشد', 'error');
                return;
            }

            this.saving = true;

            try {
                const formData = new FormData();
                formData.append('avatar', file);
                formData.append('action', 'upload_avatar');

                const csrfToken = this.getCSRFToken();

                const response = await fetch(window.dashboardUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    this.showNotification('✅ تصویر پروفایل با موفقیت بروزرسانی شد', 'success');
                    // Reload page to show new avatar
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    this.showNotification('❌ ' + (data.message || 'خطا در آپلود تصویر'), 'error');
                }
            } catch (error) {
                console.error('Upload error:', error);
                this.showNotification('❌ خطا در آپلود تصویر', 'error');
            } finally {
                this.saving = false;
            }
        },

        // Get CSRF token
        getCSRFToken() {
            return document.cookie
                .split('; ')
                .find(row => row.startsWith('csrftoken='))
                ?.split('=')[1] || '';
        },

        // Show notification
        showNotification(message, type) {
            // Simple notification - enhance with toast library if needed
            alert(message);
        },

        // Change Password
        async changePassword() {
            // Validate passwords match
            if (this.securityForm.new_password !== this.securityForm.confirm_password) {
                this.showNotification('❌ رمز عبور جدید و تکرار آن یکسان نیستند', 'error');
                return;
            }

            // Validate password length
            if (this.securityForm.new_password.length < 8) {
                this.showNotification('❌ رمز عبور باید حداقل 8 کاراکتر باشد', 'error');
                return;
            }

            this.changingPassword = true;

            try {
                const csrfToken = this.getCSRFToken();
                const response = await fetch(window.dashboardUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        action: 'change_password',
                        ...this.securityForm
                    })
                });

                const data = await response.json();

                if (data.success) {
                    this.showNotification('✅ رمز عبور با موفقیت تغییر کرد', 'success');
                    // Reset form
                    this.securityForm = {
                        current_password: '',
                        new_password: '',
                        confirm_password: ''
                    };
                } else {
                    this.showNotification('❌ ' + (data.message || 'خطا در تغییر رمز عبور'), 'error');
                }
            } catch (error) {
                console.error('Change password error:', error);
                this.showNotification('❌ خطا در ارتباط با سرور', 'error');
            } finally {
                this.changingPassword = false;
            }
        }
    };
}
