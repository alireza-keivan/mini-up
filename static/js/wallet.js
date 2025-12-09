/* ============================================================================
   Wallet Page – Interaction Controller
   Author: Mini-Up Frontend System
   Handles: balance animation, refresh, filters, transactions, modals, export
   ============================================================================ */

document.addEventListener("DOMContentLoaded", () => {
    WalletBalanceAnimator.init();
    WalletRefresh.init();
    WalletAmountInput.init();
    WalletGatewayValidator.init();
    WalletFilters.init();
    WalletTransactions.init();
    WalletSecurityModals.init();
    WalletExport.init();
});


/* ============================================================================
   1) Balance Counter Animation
   ============================================================================ */
const WalletBalanceAnimator = {
    init() {
        // Check for both data-balance (actual template) and data-wallet-balance (fallback)
        const el = document.querySelector("#main-balance");
        if (!el) return;

        const target = parseInt(el.dataset.balance || el.dataset.walletBalance || 0);
        if (target === 0) return;

        const duration = 1200;
        const start = 0;
        const startTime = performance.now();

        const animate = (time) => {
            const progress = Math.min((time - startTime) / duration, 1);
            const current = Math.floor(start + (target - start) * progress);
            el.textContent = current.toLocaleString("fa-IR");

            if (progress < 1) requestAnimationFrame(animate);
        };

        requestAnimationFrame(animate);
    }
};


/* ============================================================================
   2) Balance Refresh
   ============================================================================ */
const WalletRefresh = {
    init() {
        const btn = document.querySelector("#refresh-balance-btn");
        if (!btn) return;

        btn.addEventListener("click", async () => {
            const icon = document.querySelector("#refresh-icon");
            if (icon) icon.classList.add("animate-spin");
            btn.disabled = true;

            try {
                // TODO: Replace with actual API endpoint
                const response = await fetch("/wallet/api/balance/");
                if (response.ok) {
                    const data = await response.json();
                    this.updateBalance(data.balance);
                    this.showToast("موجودی بروزرسانی شد", "success");
                } else {
                    throw new Error("Failed to refresh");
                }
            } catch (error) {
                console.error("Refresh error:", error);
                this.showToast("خطا در بروزرسانی", "error");
            } finally {
                if (icon) icon.classList.remove("animate-spin");
                btn.disabled = false;
            }
        });
    },

    updateBalance(newBalance) {
        const el = document.querySelector("#main-balance");
        if (el) {
            el.dataset.balance = newBalance;
            WalletBalanceAnimator.init();
        }
    },

    showToast(message, type = "info") {
        const toast = document.createElement("div");
        const bgColor = type === "success" ? "bg-green-500" : type === "error" ? "bg-red-500" : "bg-dark-700";
        toast.className = `fixed bottom-5 right-5 ${bgColor} text-white px-4 py-3 rounded-xl shadow-2xl z-50 animate-slide-up`;
        toast.textContent = message;

        document.body.appendChild(toast);
        setTimeout(() => toast.style.opacity = "0", 2500);
        setTimeout(() => toast.remove(), 3000);
    }
};


/* ============================================================================
   3) Amount Input Handler (Top-up)
   ============================================================================ */
const WalletAmountInput = {
    input: null,
    min: 0,
    max: 0,
    payBtn: null,
    validationMsg: null,

    init() {
        this.input = document.querySelector("#topup-amount");
        this.payBtn = document.querySelector("#topup-submit-btn");
        this.validationMsg = document.querySelector("#amount-validation-msg");

        if (!this.input) return;

        this.min = parseInt(this.input.dataset.min || 10000);
        this.max = parseInt(this.input.dataset.max || 50000000);

        this.input.addEventListener("input", this.handleInput.bind(this));
        this.input.addEventListener("blur", this.cleanNumber.bind(this));
        this.input.addEventListener("keypress", this.onlyNumbers.bind(this));
        
        // Quick amount buttons
        this.bindQuickAmounts();
    },

    bindQuickAmounts() {
        document.querySelectorAll(".preset-amount-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const amount = parseInt(btn.dataset.amount || 0);
                if (amount > 0) {
                    this.input.value = amount.toLocaleString("fa-IR");
                    this.handleInput();
                }
            });
        });
    },

    onlyNumbers(e) {
        // Allow numbers and Persian/Arabic numerals
        const char = e.key;
        if (!/[0-9۰-۹٠-٩]/.test(char) && e.key !== "Backspace" && e.key !== "Delete") {
            e.preventDefault();
        }
    },

    handleInput() {
        // Remove non-numeric characters (keep Persian/Arabic numerals)
        let raw = this.input.value
            .replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d)) // Persian to English
            .replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d)) // Arabic to English
            .replace(/[^0-9]/g, "");

        if (!raw) raw = "0";
        let num = parseInt(raw);

        // Validate range
        let isValid = true;
        let message = "";

        if (num < this.min && num > 0) {
            isValid = false;
            message = `حداقل مبلغ ${this.min.toLocaleString("fa-IR")} تومان است`;
        } else if (num > this.max) {
            num = this.max;
            message = `حداکثر مبلغ ${this.max.toLocaleString("fa-IR")} تومان است`;
        }

        // Update UI
        this.input.value = num.toLocaleString("fa-IR");

        if (this.payBtn) {
            if (isValid && num >= this.min) {
                this.payBtn.disabled = false;
                this.payBtn.classList.remove("opacity-40");
            } else {
                this.payBtn.disabled = true;
                this.payBtn.classList.add("opacity-40");
            }
        }

        if (this.validationMsg) {
            if (message) {
                this.validationMsg.textContent = message;
                this.validationMsg.classList.remove("hidden");
            } else {
                this.validationMsg.classList.add("hidden");
            }
        }
    },

    cleanNumber() {
        let num = parseInt(this.input.value.replace(/[^0-9]/g, "") || "0");
        if (num > 0 && num < this.min) {
            num = this.min;
        }
        if (num > this.max) {
            num = this.max;
        }
        this.input.value = num.toLocaleString("fa-IR");
        this.handleInput();
    }
};


/* ============================================================================
   4) Payment Gateway Validator
   ============================================================================ */
const WalletGatewayValidator = {
    form: null,
    gatewayRadios: null,
    validationMsg: null,

    init() {
        this.form = document.querySelector("#topup-form");
        if (!this.form) return;

        this.gatewayRadios = this.form.querySelectorAll('input[name="gateway"]');
        this.validationMsg = document.querySelector("#gateway-validation-msg");

        // Visual feedback on gateway selection
        this.bindGatewaySelection();

        // Validate on form submit
        this.form.addEventListener("submit", (e) => {
            if (!this.validateGateway()) {
                e.preventDefault();
                this.showValidationError();
            }
        });
    },

    bindGatewaySelection() {
        this.gatewayRadios.forEach(radio => {
            radio.addEventListener("change", () => {
                this.hideValidationError();
                this.updateGatewayVisuals(radio);
            });
        });

        // Initialize visual state for checked gateway
        const checkedGateway = this.form.querySelector('input[name="gateway"]:checked');
        if (checkedGateway) {
            this.updateGatewayVisuals(checkedGateway);
        }
    },

    updateGatewayVisuals(selectedRadio) {
        // Remove selection style from all gateway options
        this.gatewayRadios.forEach(radio => {
            const label = radio.closest(".gateway-option");
            if (label) {
                label.classList.remove("ring-2", "ring-neon-cyan", "border-neon-cyan");
            }
        });

        // Add selection style to chosen gateway
        const selectedLabel = selectedRadio.closest(".gateway-option");
        if (selectedLabel) {
            selectedLabel.classList.add("ring-2", "ring-neon-cyan", "border-neon-cyan");
        }
    },

    validateGateway() {
        const selectedGateway = this.form.querySelector('input[name="gateway"]:checked');
        return selectedGateway !== null;
    },

    showValidationError() {
        if (this.validationMsg) {
            this.validationMsg.classList.remove("hidden");
            
            // Scroll to gateway section
            const gatewaySection = document.querySelector("#gateway-selector");
            if (gatewaySection) {
                gatewaySection.scrollIntoView({ behavior: "smooth", block: "center" });
            }
        }
    },

    hideValidationError() {
        if (this.validationMsg) {
            this.validationMsg.classList.add("hidden");
        }
    }
};


/* ============================================================================
   5) Filters Controller (Updated for actual template structure)
   ============================================================================ */
const WalletFilters = {
    init() {
        this.bindDateButtons();
        this.bindResetFilters();
        this.bindCustomDateToggle();
    },

    bindDateButtons() {
        const dateButtons = document.querySelectorAll(".wallet-date-btn");
        dateButtons.forEach(btn => {
            btn.addEventListener("click", () => {
                // Remove active from all
                dateButtons.forEach(b => b.classList.remove("filter-active"));
                // Add active to clicked
                btn.classList.add("filter-active");

                const range = btn.dataset.range;
                if (range === "custom") {
                    document.querySelector("#wallet-date-custom")?.classList.remove("hidden");
                } else {
                    document.querySelector("#wallet-date-custom")?.classList.add("hidden");
                    // Apply filter
                    this.applyFilters({ date_range: range });
                }
            });
        });
    },

    bindResetFilters() {
        const resetBtn = document.querySelector("#wallet-reset-filters");
        if (!resetBtn) return;

        resetBtn.addEventListener("click", () => {
            const form = document.querySelector("#wallet-filters-form");
            if (form) form.reset();
            
            // Reload page without filters
            window.location.href = window.location.pathname;
        });
    },

    bindCustomDateToggle() {
        // Custom date range will be handled by form submission
        const form = document.querySelector("#wallet-filters-form");
        if (form) {
            form.addEventListener("submit", (e) => {
                e.preventDefault();
                const formData = new FormData(form);
                const params = {};
                for (let [key, value] of formData.entries()) {
                    if (value) params[key] = value;
                }
                this.applyFilters(params);
            });
        }
    },

    applyFilters(params) {
        const url = new URL(window.location);
        Object.keys(params).forEach(key => {
            url.searchParams.set(key, params[key]);
        });
        window.location.href = url.toString();
    }
};


/* ============================================================================
   5) Transactions: Click handling and details
   ============================================================================ */
const WalletTransactions = {
    init() {
        this.bindTransactionClicks();
        this.bindCopyTracking();
    },

    bindTransactionClicks() {
        // Transaction items are clickable in the actual template
        document.querySelectorAll(".transaction-item").forEach(item => {
            item.addEventListener("click", (e) => {
                // Don't trigger if clicking a button or link inside
                if (e.target.closest("button") || e.target.closest("a")) return;

                const txId = item.dataset.txId;
                if (txId) {
                    // TODO: Open transaction details modal or navigate to detail page
                    console.log("Transaction clicked:", txId);
                }
            });
        });
    },

    bindCopyTracking() {
        // Look for copy buttons (if they exist in details)
        document.querySelectorAll("[data-copy-id]").forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                const id = btn.dataset.copyId;
                this.copyToClipboard(id);
            });
        });
    },

    copyToClipboard(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                this.showToast("کپی شد ✓");
            }).catch(() => {
                this.fallbackCopy(text);
            });
        } else {
            this.fallbackCopy(text);
        }
    },

    fallbackCopy(text) {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand("copy");
            this.showToast("کپی شد ✓");
        } catch (err) {
            console.error("Copy failed:", err);
        }
        document.body.removeChild(textarea);
    },

    showToast(text) {
        const toast = document.createElement("div");
        toast.className = "fixed bottom-5 left-5 bg-green-500 text-white px-4 py-3 rounded-xl shadow-2xl z-50 flex items-center gap-2";
        toast.innerHTML = `
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            <span>${text}</span>
        `;

        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateY(20px)";
            toast.style.transition = "all 0.3s ease";
        }, 2000);
        setTimeout(() => toast.remove(), 2500);
    }
};


/* ============================================================================
   6) Security Modals (PIN, 2FA, etc.)
   ============================================================================ */
const WalletSecurityModals = {
    init() {
        // Set up global functions for inline onclick handlers in template
        window.openSetPinModal = () => this.open("pinSetupModal");
        window.openChangePinModal = () => this.open("pinChangeModal");
        window.openRemovePinModal = () => this.open("pinRemoveModal");
        window.open2FASetupModal = () => this.open("2faSetupModal");
        window.open2FASettingsModal = () => this.open("2faSettingsModal");

        this.bindOpenButtons();
        this.bindCloseButtons();
        this.bindOverlayClicks();
        this.bindEscapeKey();
    },

    bindOpenButtons() {
        document.querySelectorAll("[data-open-modal]").forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                const modalId = btn.dataset.openModal;
                this.open(modalId);
            });
        });
    },

    bindCloseButtons() {
        document.querySelectorAll("[data-close-modal]").forEach(btn => {
            btn.addEventListener("click", () => {
                const modalId = btn.dataset.closeModal;
                this.close(modalId);
            });
        });
    },

    bindOverlayClicks() {
        document.querySelectorAll(".security-modal-overlay, .modal-overlay").forEach(overlay => {
            overlay.addEventListener("click", (e) => {
                if (e.target === overlay) {
                    // Find the modal element (could be overlay itself or parent)
                    const modal = overlay.id ? overlay : overlay.closest("[id$='Modal']");
                    if (modal) this.close(modal.id);
                }
            });
        });
    },

    bindEscapeKey() {
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                // Close all visible modals
                const openModals = document.querySelectorAll("[id$='Modal']:not(.hidden):not(.opacity-0)");
                openModals.forEach(modal => this.close(modal.id));
            }
        });
    },

    open(modalId) {
        const modal = document.querySelector(`#${modalId}`);
        if (!modal) {
            console.warn(`Modal #${modalId} not found`);
            return;
        }

        // Handle different modal visibility styles
        modal.classList.remove("opacity-0", "invisible", "hidden");
        modal.classList.add("opacity-100");
        modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";

        // Focus first input
        setTimeout(() => {
            const firstInput = modal.querySelector("input, textarea, button");
            if (firstInput) firstInput.focus();
        }, 100);
    },

    close(modalId) {
        const modal = document.querySelector(`#${modalId}`);
        if (!modal) return;

        // Handle different modal visibility styles
        modal.classList.add("opacity-0", "invisible");
        modal.classList.remove("opacity-100");
        modal.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";

        // Reset form if exists
        const form = modal.querySelector("form");
        if (form) form.reset();
    }
};


/* ============================================================================
   7) Export Transactions
   ============================================================================ */
const WalletExport = {
    init() {
        const exportBtn = document.querySelector("#export-transactions-btn");
        if (!exportBtn) return;

        exportBtn.addEventListener("click", async () => {
            exportBtn.disabled = true;
            const originalText = exportBtn.innerHTML;
            exportBtn.innerHTML = `
                <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
                <span>در حال دانلود...</span>
            `;

            try {
                // TODO: Implement actual export endpoint
                const params = new URLSearchParams(window.location.search);
                const response = await fetch(`/wallet/export/?${params.toString()}`);
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `wallet-transactions-${Date.now()}.xlsx`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                    
                    this.showToast("فایل دانلود شد ✓", "success");
                } else {
                    throw new Error("Export failed");
                }
            } catch (error) {
                console.error("Export error:", error);
                this.showToast("خطا در دانلود فایل", "error");
            } finally {
                exportBtn.disabled = false;
                exportBtn.innerHTML = originalText;
            }
        });
    },

    showToast(message, type = "info") {
        const toast = document.createElement("div");
        const bgClass = type === "success" ? "bg-green-500" : type === "error" ? "bg-red-500" : "bg-dark-700";
        toast.className = `fixed bottom-5 left-5 ${bgClass} text-white px-4 py-3 rounded-xl shadow-2xl z-50`;
        toast.textContent = message;

        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transition = "opacity 0.3s ease";
        }, 2500);
        setTimeout(() => toast.remove(), 3000);
    }
};
