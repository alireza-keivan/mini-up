function dashboard() {
    return {
        activeTab: 'info',
        saving: false,
        depositProcessing: false,
        showAddAddressForm: false,
        showCardForm: false,
        submittingAddress: false,
        submittingCard: false,
        
        // User Data - Will be set by Django template
        userData: {
            first_name: '',
            last_name: '',
            email: '',
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
            id: null,
            title: '',
            recipient_name: '',
            recipient_phone: '',
            province: '',
            city: '',
            postal_code: '',
            full_address: '',
            is_default: false
        },
        
        // Available cities based on selected province
        availableCities: [],
        
        // Cities data for each province
        citiesData: {
  'آذربایجان شرقی': ['تبریز','آذرشهر','اسکو','اهر','بستان‌آباد','بناب','جلفا','چاراویماق','سراب','شبستر','عجب‌شیر','کلیبر','مراغه','مرند','ملکان','میانه','ورزقان','هریس','هشترود','خداآفرین'],
  'آذربایجان غربی': ['ارومیه','اشنویه','بوکان','پیرانشهر','تکاب','چالدران','خوی','سردشت','سلماس','شاهین‌دژ','شوط','ماکو','مهاباد','میاندوآب','نقده','پلدشت'],
  'اردبیل': ['اردبیل','بیله‌سوار','پارس‌آباد','خلخال','کوثر','گرمی','مشگین‌شهر','نمین','نیر'],
  'اصفهان': ['اصفهان','آران و بیدگل','اردستان','برخوار','بوئین‌میاندشت','تیران و کرون','چادگان','خمینی‌شهر','خوانسار','خور و بیابانک','دهاقان','سمیرم','شاهین‌شهر و میمه','شهرضا','فریدن','فریدون‌شهر','فلاورجان','کاشان','گلپایگان','لنجان','مبارکه','نائین','نجف‌آباد'],
  'البرز': ['کرج','اشتهارد','ساوجبلاغ','طالقان','نظرآباد','فردیس'],
  'ایلام': ['ایلام','آبدانان','ایوان','بدره','چرداول','دهلران','دره‌شهر','مهران','سیروان'],
  'بوشهر': ['بوشهر','تنگستان','جم','دشتستان','دشتی','دیر','دیلم','عسلویه','کنگان','گناوه'],
  'تهران': ['تهران','اسلام‌شهر','بهارستان','پاکدشت','پردیس','پیشوا','ری','رباط‌کریم','شمیرانات','شهریار','فیروزکوه','قدس','قرچک','ملارد','ورامین','دماوند'],
  'چهارمحال و بختیاری': ['شهرکرد','بن','بروجن','خانمیرزا','اردل','سامان','فارسان','کوهرنگ','کیار','لردگان'],
  'خراسان جنوبی': ['بیرجند','بشرویه','درمیان','زیرکوه','سرایان','سربیشه','طبس','فردوس','قائنات','نهبندان'],
  'خراسان رضوی': ['مشهد','بجستان','بردسکن','تایباد','تربت جام','تربت حیدریه','جغتای','جوین','چناران','خواف','داورزن','درگز','رشتخوار','زاوه','سبزوار','سرخس','فریمان','فیروزه','قوچان','کاشمر','کلات','گناباد','مه‌ولات','نیشابور'],
  'خراسان شمالی': ['بجنورد','اسفراین','جاجرم','راز و جرگلان','شیروان','فاروج','گرمه'],
  'خوزستان': ['اهواز','آبادان','آغاجاری','امیدیه','اندیکا','اندیمشک','ایذه','باوی','بندر ماهشهر','بهبهان','حمیدیه','خرمشهر','دزپارت','دزفول','دشت آزادگان','رامشیر','رامهرمز','شادگان','شوش','شوشتر','کارون','گتوند','لالی','مسجدسلیمان','هفتکل','هندیجان','هویزه'],
  'زنجان': ['زنجان','ابهر','ایجرود','خدابنده','خرمدره','سلطانیه','طارم','ماهنشان'],
  'سمنان': ['سمنان','آرادان','دامغان','سرخه','شاهرود','گرمسار','مهدی‌شهر','میامی'],
  'سیستان و بلوچستان': ['زاهدان','ایرانشهر','چابهار','دلگان','راسک','زابل','زهک','سراوان','سرباز','سیب و سوران','فنوج','قصرقند','کنارک','مهرستان','میرجاوه','نیکشهر','هامون','هیرمند'],
  'فارس': ['شیراز','آباده','ارسنجان','استهبان','اقلید','بوانات','بیضا','پاسارگاد','خرامه','خرم‌بید','خنج','داراب','زرین‌دشت','سپیدان','سروستان','فراشبند','فسا','فیروزآباد','قیر و کارزین','کازرون','کوار','گراش','لارستان','لامرد','مرودشت','ممسنی','مهر','نی‌ریز'],
  'قزوین': ['قزوین','آبیک','آوج','بوئین‌زهرا','تاکستان'],
  'قم': ['قم'],
  'کردستان': ['سنندج','بانه','بیجار','دهگلان','دیواندره','سروآباد','سقز','قروه','کامیاران','مریوان'],
  'کرمان': ['کرمان','ارزوئیه','انار','بافت','بردسیر','بم','جیرفت','رابر','راور','رفسنجان','رودبار جنوب','ریگان','سیرجان','شهربابک','عنبرآباد','فاریاب','قلعه‌گنج','کوهبنان','کهنوج','مانوجان','نرماشیر'],
  'کرمانشاه': ['کرمانشاه','اسلام‌آباد غرب','پاوه','ثلاث باباجانی','جوانرود','دالاهو','روانسر','سرپل ذهاب','سنقر','صحنه','قصر شیرین','کنگاور','گیلان‌غرب','هرسین'],
  'کهگیلویه و بویراحمد': ['یاسوج','باشت','بویراحمد','چرام','دنا','گچساران','کهگیلویه','لنده','مارگون'],
  'گلستان': ['گرگان','آزادشهر','آق‌قلا','بندرگز','ترکمن','رامیان','علی‌آباد','کردکوی','کلاله','گالیکش','گمیشان','مینودشت'],
  'گیلان': ['رشت','آستارا','آستانه اشرفیه','املش','بندر انزلی','رودبار','رودسر','سیاهکل','شفت','صومعه‌سرا','تالش','فومن','لاهیجان','لنگرود','ماسال'],
  'لرستان': ['خرم‌آباد','ازنا','الیگودرز','بروجرد','پلدختر','چگنی','دورود','دلفان','رومشکان','سلسله','کوهدشت'],
  'مازندران': ['ساری','آمل','بابل','بابلسر','بهشهر','تنکابن','جویبار','چالوس','رامسر','سوادکوه','سوادکوه شمالی','سیمرغ','عباس‌آباد','فریدونکنار','قایم‌شهر','کلاردشت','گلوگاه','محمودآباد','میاندرود','نکا','نور','نوشهر'],
  'مرکزی': ['اراک','آشتیان','تفرش','خمین','خنداب','دلیجان','زرندیه','ساوه','شازند','فراهان','محلات'],
  'هرمزگان': ['بندرعباس','ابوموسی','بستک','بشاگرد','بندر لنگه','جاسک','حاجی‌آباد','خمیر','رودان','سیریک','قشم','کیش','میناب','پارسیان'],
  'همدان': ['همدان','اسدآباد','بهار','تویسرکان','رزن','کبودرآهنگ','ملایر','نهاوند'],
  'یزد': ['یزد','ابرکوه','اردکان','اشکذر','بافق','بهاباد','تفت','خاتم','مهریز','میبد']
        },

        // Bank Card Form Data
        cardForm: {
            id: null,
            card_number: '',
            is_default: false
        },

        // Security Form Data - PIN Management
        hasPinCode: false,
        settingPin: false,
        changingPin: false,
        activeSecuritySection: null, // No section active by default
        
        pinForm: {
            pin: '',
            confirm_pin: ''
        },
        
        changePinForm: {
            current_pin: '',
            new_pin: '',
            confirm_pin: ''
        },

        // Initialize component
        init() {
            // Load initial data from Django if available
            if (window.dashboardInitData) {
                if (window.dashboardInitData.userData) {
                    this.userData = { ...this.userData, ...window.dashboardInitData.userData };
                }
                if (window.dashboardInitData.walletData) {
                    this.walletData = { ...this.walletData, ...window.dashboardInitData.walletData };
                }
            }
            
            // Check PIN status
            this.checkPinStatus();
            
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
            // Validate required fields are not empty
            if (!this.userData.first_name || !this.userData.first_name.trim()) {
                this.showNotification('❌ نام نمی‌تواند خالی باشد', 'error');
                // Revert to original value
                this.userData.first_name = window.dashboardInitData.userData.first_name || '';
                return;
            }

            if (!this.userData.last_name || !this.userData.last_name.trim()) {
                this.showNotification('❌ نام خانوادگی نمی‌تواند خالی باشد', 'error');
                // Revert to original value
                this.userData.last_name = window.dashboardInitData.userData.last_name || '';
                return;
            }

            if (!this.userData.email || !this.userData.email.trim()) {
                this.showNotification('❌ ایمیل نمی‌تواند خالی باشد', 'error');
                // Revert to original value
                this.userData.email = window.dashboardInitData.userData.email || '';
                return;
            }

            // Validate email format
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailPattern.test(this.userData.email)) {
                this.showNotification('❌ فرمت ایمیل صحیح نیست', 'error');
                // Revert to original value
                this.userData.email = window.dashboardInitData.userData.email || '';
                return;
            }

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
                    
                    // Update displayed values and init data
                    if (data.user) {
                        this.userData.first_name = data.user.first_name;
                        this.userData.last_name = data.user.last_name;
                        this.userData.email = data.user.email;
                        // Update init data to keep latest values
                        window.dashboardInitData.userData.first_name = data.user.first_name;
                        window.dashboardInitData.userData.last_name = data.user.last_name;
                        window.dashboardInitData.userData.email = data.user.email;
                    }
                } else {
                    this.showNotification('❌ ' + (data.message || 'خطا در ذخیره اطلاعات'), 'error');
                    // Revert to original values on error
                    this.userData.first_name = window.dashboardInitData.userData.first_name || '';
                    this.userData.last_name = window.dashboardInitData.userData.last_name || '';
                    this.userData.email = window.dashboardInitData.userData.email || '';
                }
            } catch (error) {
                console.error('Save error:', error);
                this.showNotification('❌ خطا در ارتباط با سرور', 'error');
                // Revert to original values on error
                this.userData.first_name = window.dashboardInitData.userData.first_name || '';
                this.userData.last_name = window.dashboardInitData.userData.last_name || '';
                this.userData.email = window.dashboardInitData.userData.email || '';
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
            
            // Check if trying to remove default when there are multiple addresses
            // This check happens on the backend, but we add a warning here too
            if (this.addressForm.id && !this.addressForm.is_default) {
                // User is editing and unchecking default
                if (!confirm('آیا مطمئن هستید که می‌خواهید این آدرس را از حالت پیش‌فرض خارج کنید؟\nحداقل یک آدرس باید به عنوان آدرس پیش‌فرض انتخاب شود.')) {
                    return;
                }
            }

            this.submittingAddress = true;

            try {
                const csrfToken = this.getCSRFToken();
                
                // Determine action based on whether we're editing or adding
                const action = this.addressForm.id ? 'update_address' : 'add_address';
                
                // Combine first and last name into recipient_name
                const addressData = { ...this.addressForm };
                addressData.recipient_name = `${this.addressForm.first_name || ''} ${this.addressForm.last_name || ''}`.trim();
                delete addressData.first_name;
                delete addressData.last_name;
                
                const response = await fetch(window.dashboardUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        action: action,
                        ...addressData
                    })
                });

                const data = await response.json();

                if (data.success) {
                    const message = this.addressForm.id ? '✅ آدرس با موفقیت بروزرسانی شد' : '✅ آدرس با موفقیت ذخیره شد';
                    this.showNotification(message, 'success');
                    this.showAddAddressForm = false;
                    this.resetAddressForm();
                    // Reload to show updated address
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

        // Reset address form
        resetAddressForm() {
            this.addressForm = {
                id: null,
                title: '',
                first_name: '',
                last_name: '',
                recipient_phone: '',
                province: '',
                city: '',
                postal_code: '',
                full_address: '',
                is_default: false
            };
        },

        // Edit address - populate form with address data
        editAddress(address) {
            this.addressForm = { ...address };
            // Split recipient_name into first and last name
            if (address.recipient_name) {
                const names = address.recipient_name.split(' ');
                this.addressForm.first_name = names[0] || '';
                this.addressForm.last_name = names.slice(1).join(' ') || '';
            }
            // Update cities for the selected province
            this.updateCities();
            this.showAddAddressForm = true;
            // Scroll to form
            setTimeout(() => {
                const form = document.querySelector('form');
                if (form) {
                    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
        },
        
        // Update available cities based on selected province
        updateCities() {
            const province = this.addressForm.province;
            if (province && this.citiesData[province]) {
                this.availableCities = this.citiesData[province];
                // If current city is not in the new province, clear it
                if (!this.availableCities.includes(this.addressForm.city)) {
                    this.addressForm.city = '';
                }
            } else {
                this.availableCities = [];
                this.addressForm.city = '';
            }
        },

        // Delete address
        async deleteAddress(addressId) {
            if (!confirm('آیا از حذف این آدرس اطمینان دارید؟')) {
                return;
            }

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
                        action: 'delete_address',
                        address_id: addressId
                    })
                });

                const data = await response.json();

                if (data.success) {
                    this.showNotification('✅ آدرس با موفقیت حذف شد', 'success');
                    // Reload to update address list
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    this.showNotification('❌ ' + (data.message || 'خطا در حذف آدرس'), 'error');
                }
            } catch (error) {
                console.error('Delete address error:', error);
                this.showNotification('❌ خطا در ارتباط با سرور', 'error');
            }
        },

        // Submit Bank Card
        async submitBankCard() {
            // Remove spaces and validate card number (must be 16 digits)
            const cleanCardNumber = this.cardForm.card_number.replace(/\s/g, '');
            if (!/^\d{16}$/.test(cleanCardNumber)) {
                this.showNotification('❌ شماره کارت باید ۱۶ رقم باشد', 'error');
                return;
            }

            this.submittingCard = true;

            try {
                const csrfToken = this.getCSRFToken();
                
                // Determine action based on whether we're editing or adding
                const action = this.cardForm.id ? 'update_bank_card' : 'add_bank_card';

                const response = await fetch(window.dashboardUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        action: action,
                        id: this.cardForm.id,
                        card_number: cleanCardNumber,
                        is_default: this.cardForm.is_default
                    })
                });

                const data = await response.json();

                if (data.success) {
                    const message = this.cardForm.id ? '✅ کارت بانکی با موفقیت بروزرسانی شد' : '✅ کارت بانکی با موفقیت ذخیره شد';
                    this.showNotification(message, 'success');
                    this.showCardForm = false;
                    // Reset form
                    this.cardForm = {
                        id: null,
                        card_number: '',
                        is_default: false
                    };
                    // Reload to show updated card
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

        // Edit Bank Card
        editBankCard(id, cardNumber, isDefault) {
            this.cardForm = {
                id: id,
                card_number: cardNumber,
                is_default: isDefault
            };
            this.showCardForm = true;
            // Scroll to form
            setTimeout(() => {
                document.querySelector('.form-section').scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 100);
        },

        // Delete Bank Card
        async deleteBankCard(cardId) {
            if (!confirm('آیا از حذف این کارت بانکی اطمینان دارید؟')) {
                return;
            }

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
                        action: 'delete_bank_card',
                        card_id: cardId
                    })
                });

                const data = await response.json();

                if (data.success) {
                    this.showNotification('✅ کارت بانکی با موفقیت حذف شد', 'success');
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    this.showNotification('❌ ' + (data.message || 'خطا در حذف کارت'), 'error');
                }
            } catch (error) {
                console.error('Delete card error:', error);
                this.showNotification('❌ خطا در ارتباط با سرور', 'error');
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

        // Check PIN status
        async checkPinStatus() {
            try {
                const response = await fetch('/wallet/api/pin/status/', {
                    method: 'GET',
                    credentials: 'same-origin'
                });

                const data = await response.json();
                this.hasPinCode = data.has_pin || false;
            } catch (error) {
                console.error('Check PIN status error:', error);
            }
        },

        // Setup PIN
        async setupPin() {
            // Validate PIN
            if (!this.pinForm.pin || !this.pinForm.confirm_pin) {
                this.showNotification('❌ لطفاً رمز را وارد کنید', 'error');
                return;
            }

            if (this.pinForm.pin !== this.pinForm.confirm_pin) {
                this.showNotification('❌ رمزها مطابقت ندارند', 'error');
                return;
            }

            if (!/^\d{4}$/.test(this.pinForm.pin)) {
                this.showNotification('❌ رمز باید ۴ رقم باشد', 'error');
                return;
            }

            this.settingPin = true;

            try {
                const csrfToken = this.getCSRFToken();
                const response = await fetch('/wallet/api/pin/setup/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify(this.pinForm)
                });

                const data = await response.json();

                if (data.success) {
                    this.showNotification('✅ رمز امنیتی با موفقیت تنظیم شد', 'success');
                    this.pinForm = { pin: '', confirm_pin: '' };
                    this.hasPinCode = true;
                } else {
                    this.showNotification('❌ ' + (data.message || 'خطا در تنظیم رمز'), 'error');
                }
            } catch (error) {
                console.error('Setup PIN error:', error);
                this.showNotification('❌ خطا در ارتباط با سرور', 'error');
            } finally {
                this.settingPin = false;
            }
        },

        // Change PIN
        async changePin() {
            // Validate
            if (!this.changePinForm.current_pin || !this.changePinForm.new_pin || !this.changePinForm.confirm_pin) {
                this.showNotification('❌ لطفاً تمام فیلدها را پر کنید', 'error');
                return;
            }

            if (this.changePinForm.new_pin !== this.changePinForm.confirm_pin) {
                this.showNotification('❌ رمز جدید و تکرار آن مطابقت ندارند', 'error');
                return;
            }

            if (!/^\d{4}$/.test(this.changePinForm.new_pin)) {
                this.showNotification('❌ رمز جدید باید ۴ رقم باشد', 'error');
                return;
            }

            if (this.changePinForm.current_pin === this.changePinForm.new_pin) {
                this.showNotification('❌ رمز جدید نباید با رمز فعلی یکسان باشد', 'error');
                return;
            }

            this.changingPin = true;

            try {
                const csrfToken = this.getCSRFToken();
                const response = await fetch('/wallet/api/pin/change/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify(this.changePinForm)
                });

                const data = await response.json();

                if (data.success) {
                    this.showNotification('✅ رمز امنیتی با موفقیت تغییر کرد', 'success');
                    this.changePinForm = { current_pin: '', new_pin: '', confirm_pin: '' };
                } else {
                    this.showNotification('❌ ' + (data.message || 'خطا در تغییر رمز'), 'error');
                }
            } catch (error) {
                console.error('Change PIN error:', error);
                this.showNotification('❌ خطا در ارتباط با سرور', 'error');
            } finally {
                this.changingPin = false;
            }
        },

        // Copy referral code to clipboard
        copyReferralCode(code) {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(code).then(() => {
                    this.showNotification('✅ کد معرف کپی شد', 'success');
                }).catch(() => {
                    this.fallbackCopy(code);
                });
            } else {
                this.fallbackCopy(code);
            }
        },

        // Fallback copy method for older browsers
        fallbackCopy(text) {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {
                document.execCommand('copy');
                this.showNotification('✅ کد معرف کپی شد', 'success');
            } catch (err) {
                this.showNotification('❌ خطا در کپی کردن', 'error');
            }
            document.body.removeChild(textArea);
        },

        // Share referral code via different platforms
        shareReferralCode(platform) {
            const code = document.querySelector('[dir="ltr"]').textContent.trim();
            const url = window.location.origin;
            const message = `به مینی‌آپ بپیوندید و از تخفیف‌های ویژه بهره‌مند شوید! 🎁\n\nکد معرف من: ${code}\n\nلینک ثبت‌نام: ${url}/accounts/register/?ref=${code}`;
            
            switch(platform) {
                case 'whatsapp':
                    window.open(`https://wa.me/?text=${encodeURIComponent(message)}`, '_blank');
                    break;
                case 'telegram':
                    window.open(`https://t.me/share/url?url=${encodeURIComponent(url + '/accounts/register/?ref=' + code)}&text=${encodeURIComponent(message)}`, '_blank');
                    break;
                case 'link':
                    const shareUrl = `${url}/accounts/register/?ref=${code}`;
                    this.copyReferralCode(shareUrl);
                    this.showNotification('✅ لینک دعوت کپی شد', 'success');
                    break;
                default:
                    this.showNotification('❌ پلتفرم انتخاب شده معتبر نیست', 'error');
            }
        }
    };
}
