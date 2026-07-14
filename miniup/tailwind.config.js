/**
 * Mini-up.ir Tailwind Configuration
 * RTL Dark Neon Gaming Theme
 */

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './static/**/*.js',
  ],
  safelist: [
    { pattern: /^vs-/ }, // Preserve all virtual-services classes
    { pattern: /^mg-/ }, // Preserve all mini-game classes
  ],
  darkMode: 'class',
  theme: {
    extend: {
      /* ═══════════════════════════════════════════
         CUSTOM COLORS - Neon Dark Theme
         ═══════════════════════════════════════════ */
      colors: {
        // Base backgrounds
        'dark': {
          DEFAULT: '#0a0a0f',
          50: '#1a1a25',
          100: '#15151f',
          200: '#12121a',
          300: '#0f0f15',
          400: '#0a0a0f',
          500: '#080810',
          600: '#050508',
          700: '#030305',
          800: '#020203',
          900: '#000000',
        },
        // Neon accent colors
        'neon': {
          'pink': '#ff0055',
          'pink-light': '#ff3377',
          'pink-dark': '#cc0044',
          'cyan': '#00ffff',
          'cyan-light': '#66ffff',
          'cyan-dark': '#00cccc',
          'purple': '#b400ff',
          'purple-light': '#cc44ff',
          'green': '#00ff88',
          'green-light': '#44ffaa',
          'yellow': '#ffee00',
          'yellow-light': '#fff544',
        },
        // Semantic colors
        'primary': '#00ffff',
        'secondary': '#ff0055',
        'accent': '#b400ff',
        'success': '#00ff88',
        'warning': '#ffee00',
        'error': '#ff4455',
        'info': '#00aaff',
      },

      /* ═══════════════════════════════════════════
         TYPOGRAPHY - Persian Fonts
         ═══════════════════════════════════════════ */
      fontFamily: {
        'vazir': ['Vazirmatn', 'Tahoma', 'Arial', 'sans-serif'],
        'lalezar': ['Lalezar', 'Vazirmatn', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        'display-1': ['clamp(3rem, 8vw, 6rem)', { lineHeight: '1.1', fontWeight: '900' }],
        'display-2': ['clamp(2.5rem, 6vw, 4.5rem)', { lineHeight: '1.15', fontWeight: '800' }],
        'display-3': ['clamp(2rem, 5vw, 3.5rem)', { lineHeight: '1.2', fontWeight: '700' }],
      },

      /* ═══════════════════════════════════════════
         SPACING & LAYOUT
         ═══════════════════════════════════════════ */
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      maxWidth: {
        '8xl': '88rem',
        '9xl': '96rem',
      },

      /* ═══════════════════════════════════════════
         SHADOWS & GLOWS
         ═══════════════════════════════════════════ */
      boxShadow: {
        'neon-pink': '0 0 5px #ff0055, 0 0 20px rgba(255, 0, 85, 0.5), 0 0 40px rgba(255, 0, 85, 0.3)',
        'neon-pink-lg': '0 0 10px #ff0055, 0 0 40px rgba(255, 0, 85, 0.6), 0 0 80px rgba(255, 0, 85, 0.4)',
        'neon-cyan': '0 0 5px #00ffff, 0 0 20px rgba(0, 255, 255, 0.5), 0 0 40px rgba(0, 255, 255, 0.3)',
        'neon-cyan-lg': '0 0 10px #00ffff, 0 0 40px rgba(0, 255, 255, 0.6), 0 0 80px rgba(0, 255, 255, 0.4)',
        'neon-purple': '0 0 5px #b400ff, 0 0 20px rgba(180, 0, 255, 0.5), 0 0 40px rgba(180, 0, 255, 0.3)',
        'neon-green': '0 0 5px #00ff88, 0 0 20px rgba(0, 255, 136, 0.5), 0 0 40px rgba(0, 255, 136, 0.3)',
        'glass': '0 8px 32px rgba(0, 0, 0, 0.5)',
        'inner-glow': 'inset 0 0 20px rgba(0, 255, 255, 0.1)',
      },
      dropShadow: {
        'neon-pink': ['0 0 5px rgba(255, 0, 85, 0.8)', '0 0 20px rgba(255, 0, 85, 0.5)'],
        'neon-cyan': ['0 0 5px rgba(0, 255, 255, 0.8)', '0 0 20px rgba(0, 255, 255, 0.5)'],
        'glow': '0 0 10px rgba(255, 255, 255, 0.3)',
      },

      /* ═══════════════════════════════════════════
         ANIMATIONS
         ═══════════════════════════════════════════ */
      animation: {
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'slide-up': 'slide-up 0.5s ease-out',
        'slide-down': 'slide-down 0.5s ease-out',
        'fade-in': 'fade-in 0.5s ease-out',
        'scale-in': 'scale-in 0.3s ease-out',
        'spin-slow': 'spin 8s linear infinite',
        'gradient-shift': 'gradient-shift 8s ease infinite',
        'border-glow': 'border-glow 3s ease-in-out infinite',
        'text-shimmer': 'text-shimmer 3s ease-in-out infinite',
      },
      keyframes: {
        'glow-pulse': {
          '0%, 100%': { opacity: '1', filter: 'brightness(1)' },
          '50%': { opacity: '0.8', filter: 'brightness(1.2)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'slide-down': {
          '0%': { transform: 'translateY(-20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'scale-in': {
          '0%': { transform: 'scale(0.9)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        'gradient-shift': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        'border-glow': {
          '0%, 100%': { borderColor: 'rgba(0, 255, 255, 0.5)' },
          '50%': { borderColor: 'rgba(255, 0, 85, 0.5)' },
        },
        'text-shimmer': {
          '0%': { backgroundPosition: '-200% center' },
          '100%': { backgroundPosition: '200% center' },
        },
      },

      /* ═══════════════════════════════════════════
         BACKGROUNDS & GRADIENTS
         ═══════════════════════════════════════════ */
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'mesh-gradient': 'linear-gradient(135deg, #0a0a0f 0%, #1a1a25 50%, #0a0a0f 100%)',
        'neon-gradient': 'linear-gradient(135deg, #00ffff 0%, #ff0055 50%, #b400ff 100%)',
        'hero-gradient': 'radial-gradient(ellipse at center, rgba(0, 255, 255, 0.15) 0%, transparent 70%)',
        'card-gradient': 'linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, transparent 100%)',
      },

      /* ═══════════════════════════════════════════
         BORDERS
         ═══════════════════════════════════════════ */
      borderWidth: {
        '3': '3px',
      },
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem',
      },

      /* ═══════════════════════════════════════════
         TRANSITIONS
         ═══════════════════════════════════════════ */
      transitionDuration: {
        '400': '400ms',
        '600': '600ms',
      },
      transitionTimingFunction: {
        'bounce-in': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },

      /* ═══════════════════════════════════════════
         BACKDROP BLUR
         ═══════════════════════════════════════════ */
      backdropBlur: {
        'xs': '2px',
      },
    },
  },
  plugins: [
    // RTL support plugin
    function({ addUtilities, addComponents, theme }) {
      // RTL-specific utilities
      addUtilities({
        '.text-start': {
          'text-align': 'start',
        },
        '.text-end': {
          'text-align': 'end',
        },
        '.ms-auto': {
          'margin-inline-start': 'auto',
        },
        '.me-auto': {
          'margin-inline-end': 'auto',
        },
        '.ps-4': {
          'padding-inline-start': '1rem',
        },
        '.pe-4': {
          'padding-inline-end': '1rem',
        },
        '.border-s': {
          'border-inline-start-width': '1px',
        },
        '.border-e': {
          'border-inline-end-width': '1px',
        },
        '.rounded-s': {
          'border-start-start-radius': '0.25rem',
          'border-end-start-radius': '0.25rem',
        },
        '.rounded-e': {
          'border-start-end-radius': '0.25rem',
          'border-end-end-radius': '0.25rem',
        },
      });

      // Custom neon components
      addComponents({
        '.btn-neon': {
          '@apply relative px-6 py-3 font-bold rounded-lg transition-all duration-300': {},
          '@apply bg-transparent border-2 border-neon-cyan text-neon-cyan': {},
          '@apply hover:bg-neon-cyan hover:text-dark hover:shadow-neon-cyan': {},
          '@apply active:scale-95': {},
        },
        '.btn-neon-pink': {
          '@apply relative px-6 py-3 font-bold rounded-lg transition-all duration-300': {},
          '@apply bg-transparent border-2 border-neon-pink text-neon-pink': {},
          '@apply hover:bg-neon-pink hover:text-white hover:shadow-neon-pink': {},
          '@apply active:scale-95': {},
        },
        '.btn-solid': {
          '@apply relative px-6 py-3 font-bold rounded-lg transition-all duration-300': {},
          '@apply bg-neon-cyan text-dark': {},
          '@apply hover:shadow-neon-cyan-lg hover:scale-105': {},
          '@apply active:scale-95': {},
        },
        '.card-glass': {
          '@apply bg-dark-100/50 backdrop-blur-md rounded-2xl': {},
          '@apply border border-white/10': {},
          '@apply transition-all duration-300': {},
          '@apply hover:border-neon-cyan/30 hover:shadow-glass': {},
        },
        '.text-gradient': {
          '@apply bg-clip-text text-transparent': {},
          '@apply bg-gradient-to-l from-neon-cyan via-neon-pink to-neon-purple': {},
        },
        '.input-neon': {
          '@apply w-full px-4 py-3 bg-dark-100 border-2 border-white/10 rounded-lg': {},
          '@apply text-white placeholder-white/40': {},
          '@apply focus:border-neon-cyan focus:outline-none focus:shadow-neon-cyan': {},
          '@apply transition-all duration-300': {},
        },
      });
    },
  ],
};
