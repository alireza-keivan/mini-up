/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * User Dropdown Component
 * Handles the user menu dropdown with proper accessibility and mobile support
 * Works with navbar CSS system using 'active' class
 * ═══════════════════════════════════════════════════════════════════════════════
 */

(function() {
    'use strict';

    document.addEventListener("DOMContentLoaded", () => {
        const container = document.querySelector("[data-user-dropdown]");
        if (!container) {
            console.log('User dropdown container not found');
            return;
        }

        const trigger = container.querySelector("[data-ud-trigger]");
        const dropdown = container.querySelector("[data-ud-dropdown]");
        const arrow = container.querySelector("[data-ud-arrow]");

        // Check if all required elements exist
        if (!trigger || !dropdown) {
            console.warn('User dropdown: Required elements not found');
            return;
        }

        let isOpen = false;

        const open = () => {
            if (isOpen) return;
            
            // Close any other open user dropdowns
            document.querySelectorAll('[data-user-dropdown]').forEach(c => {
                if (c !== container && c.classList.contains('active')) {
                    c.classList.remove('active');
                }
            });

            // Add active class to show dropdown (CSS handles animation)
            container.classList.add('active');
            
            if (arrow) {
                arrow.style.transform = 'rotate(180deg)';
            }
            
            trigger.setAttribute("aria-expanded", "true");
            isOpen = true;

            // Focus trap for accessibility
            setTimeout(() => {
                const firstLink = dropdown.querySelector('a, button');
                if (firstLink) firstLink.focus();
            }, 100);
        };

        const close = () => {
            if (!isOpen) return;

            // Remove active class to hide dropdown (CSS handles animation)
            container.classList.remove('active');
            
            if (arrow) {
                arrow.style.transform = 'rotate(0deg)';
            }
            
            trigger.setAttribute("aria-expanded", "false");
            isOpen = false;
        };

        const toggle = () => {
            isOpen ? close() : open();
        };

        // Click trigger handler
        trigger.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            toggle();
        });

        // Close on outside click
        document.addEventListener("click", (e) => {
            if (isOpen && !container.contains(e.target)) {
                close();
            }
        });

        // Close on Escape key
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && isOpen) {
                close();
                trigger.focus();
            }
        });

        // Close on scroll (optional, better UX on mobile)
        let scrollTimeout;
        window.addEventListener("scroll", () => {
            if (!isOpen) return;
            
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                close();
            }, 100);
        }, { passive: true });

        // Handle window resize
        window.addEventListener("resize", () => {
            if (isOpen && window.innerWidth < 768) {
                close();
            }
        });

        console.log('User dropdown initialized successfully');
    });

})();
