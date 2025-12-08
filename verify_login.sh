#!/bin/bash
# Login Page Verification Script
# This script helps debug the login page rendering issue

echo "========================================="
echo "Mini-Up Login Page Verification"
echo "========================================="
echo ""

# Check if server is running
echo "1. Checking Django server status..."
if pgrep -f "manage.py runserver" > /dev/null; then
    echo "   ✓ Django server is running"
else
    echo "   ✗ Django server is NOT running"
    echo "   Please start with: python manage.py runserver"
    exit 1
fi
echo ""

# Check template file
echo "2. Checking login template..."
if [ -f "templates/accounts/login.html" ]; then
    MODIFIED=$(stat -c %y templates/accounts/login.html)
    echo "   ✓ Template exists"
    echo "   Last modified: $MODIFIED"
    
    # Check for key changes
    if grep -q "ورود به مینی‌آپ" templates/accounts/login.html; then
        echo "   ✓ Title updated correctly"
    else
        echo "   ✗ Title NOT updated"
    fi
    
    if grep -q "شماره موبایل خود را وارد کنید" templates/accounts/login.html; then
        echo "   ✓ Subtitle updated correctly"
    else
        echo "   ✗ Subtitle NOT updated"
    fi
    
    if grep -q "fas fa-mobile-alt" templates/accounts/login.html; then
        echo "   ✓ Icon changed to mobile"
    else
        echo "   ✗ Icon NOT changed"
    fi
else
    echo "   ✗ Template file not found!"
    exit 1
fi
echo ""

# Check JavaScript file
echo "3. Checking JavaScript file..."
if [ -f "static/js/auth-login.js" ]; then
    SIZE=$(stat -c %s static/js/auth-login.js)
    echo "   ✓ auth-login.js exists (${SIZE} bytes)"
else
    echo "   ✗ auth-login.js NOT found!"
fi
echo ""

# Check CSS variables
echo "4. Checking CSS variables..."
if grep -q "neon-pink" static/css/base/_variables.css 2>/dev/null; then
    echo "   ✓ CSS variables defined"
else
    echo "   ⚠ CSS variables might not be loaded"
fi
echo ""

echo "========================================="
echo "TROUBLESHOOTING STEPS:"
echo "========================================="
echo ""
echo "If changes are not visible in browser:"
echo ""
echo "1. Hard Refresh Browser:"
echo "   • Chrome/Firefox: Ctrl + Shift + R (Linux/Windows)"
echo "   • Or: Ctrl + F5"
echo "   • Or: Open DevTools (F12) → Right-click refresh → Empty Cache and Hard Reload"
echo ""
echo "2. Clear Browser Cache:"
echo "   • Chrome: Settings → Privacy → Clear browsing data → Cached images and files"
echo "   • Firefox: Settings → Privacy → Clear Data → Cached Web Content"
echo ""
echo "3. Use Incognito/Private Window:"
echo "   • Ctrl + Shift + N (Chrome)"
echo "   • Ctrl + Shift + P (Firefox)"
echo ""
echo "4. Check Browser Console (F12):"
echo "   • Look for any JavaScript errors"
echo "   • Check Network tab for 304 (cached) vs 200 (fresh) responses"
echo ""
echo "5. Restart Django Server:"
echo "   • Stop server (Ctrl+C)"
echo "   • Run: python manage.py runserver"
echo ""
echo "6. Verify URL:"
echo "   • Make sure you're accessing: http://127.0.0.1:8000/accounts/login/"
echo "   • NOT an old cached URL"
echo ""
echo "========================================="
