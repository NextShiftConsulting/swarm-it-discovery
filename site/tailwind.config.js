// tailwind.config.js - Production Optimized (Updated for Tailwind v3+)
const isProduction = process.env.NODE_ENV === 'production'

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx,md,mdx}',
    './src/**/*.{html,vue}',
    './static/admin/*.html',
  ],
  
  // Dark mode support
  darkMode: 'class',
  
  theme: {
    extend: {
      // Custom theme extensions
      fontFamily: {
        // CLS-optimized font stacks with metric-matched fallbacks
        sans: ['Inter', 'Inter-fallback', 'system-ui', '-apple-system', 'sans-serif'],
        heading: ['Poppins', 'Poppins-fallback', 'system-ui', '-apple-system', 'sans-serif'],
        serif: ['Merriweather', 'Georgia', 'serif'],
        mono: ['Fira Code', 'ui-monospace', 'monospace'],
      },
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        secondary: {
          50: '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
        },
        accent: {
          orange: '#f59e0b',
          pink: '#ec4899',
          green: '#10b981',
        },
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
        'gradient-secondary': 'linear-gradient(135deg, #8b5cf6, #ec4899)',
        'gradient-accent': 'linear-gradient(135deg, #f59e0b, #ec4899)',
        'gradient-hero': 'linear-gradient(135deg, #2563eb, #7c3aed, #1e40af)',
        'gradient-hero-alt': 'linear-gradient(135deg, #7c3aed, #ec4899, #2563eb)',
        'gradient-success': 'linear-gradient(135deg, #10b981, #3b82f6)',
      },
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        'strong': '0 10px 40px -10px rgba(0, 0, 0, 0.2)',
        'glow': '0 0 20px rgba(59, 130, 246, 0.3)',
        'glow-lg': '0 0 40px rgba(59, 130, 246, 0.4)',
        'colored': '0 10px 30px -5px rgba(59, 130, 246, 0.3)',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
      },
      animation: {
        fadeIn: 'fadeIn 0.6s ease-out forwards',
        float: 'float 6s ease-in-out infinite',
        gradient: 'gradient 3s ease infinite',
      },
      typography: (theme) => ({
        DEFAULT: {
          css: {
            maxWidth: 'none',
            color: theme('colors.gray.900'),
            lineHeight: theme('lineHeight.relaxed'),
            // Add better typography styles
            h1: {
              fontWeight: theme('fontWeight.bold'),
              letterSpacing: theme('letterSpacing.tight'),
            },
            h2: {
              fontWeight: theme('fontWeight.semibold'),
              letterSpacing: theme('letterSpacing.tight'),
            },
            a: {
              color: theme('colors.primary.600'),
              textDecoration: 'none',
              fontWeight: theme('fontWeight.medium'),
              '&:hover': {
                color: theme('colors.primary.700'),
                textDecoration: 'underline',
              },
            },
            code: {
              backgroundColor: theme('colors.gray.100'),
              padding: theme('spacing.1'),
              borderRadius: theme('borderRadius.sm'),
              fontWeight: theme('fontWeight.normal'),
            },
            'code::before': {
              content: '""',
            },
            'code::after': {
              content: '""',
            },
          },
        },
        dark: {
          css: {
            color: theme('colors.gray.100'),
            h1: {
              color: theme('colors.gray.100'),
            },
            h2: {
              color: theme('colors.gray.200'),
            },
            a: {
              color: theme('colors.primary.400'),
              '&:hover': {
                color: theme('colors.primary.300'),
              },
            },
            code: {
              backgroundColor: theme('colors.gray.800'),
              color: theme('colors.gray.200'),
            },
          },
        },
      }),
    },
  },
  
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
  
  // Note: JIT mode and safelist are handled differently in Tailwind v3+
  // JIT is enabled by default, and purging is automatic based on 'content' array
  // If you need to safelist specific classes, uncomment below:
  
  // safelist: [
  //   // Keep dynamic classes that might be missed
  //   'text-sm',
  //   'text-lg', 
  //   'text-xl',
  //   /^bg-/, // Keep all background classes
  //   /^text-/, // Keep all text color classes
  // ],
}