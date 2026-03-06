/**
 * useTheme hook for dark mode support
 * Respects system preference and persists user choice
 *
 * IMPORTANT: Uses mounted state to prevent hydration mismatches
 */

import { useEffect, useState } from 'react'
import { useLocalStorage } from './useLocalStorage'

export type Theme = 'light' | 'dark' | 'auto'
export type ResolvedTheme = 'light' | 'dark'

/**
 * Hook to manage theme (light/dark/auto)
 * @returns Theme state and control functions
 */
export function useTheme() {
  const [theme, setTheme] = useLocalStorage<Theme>('swarmit-theme', 'auto')
  // Track if component has mounted to prevent hydration mismatch
  const [mounted, setMounted] = useState(false)
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>('light')

  // Set mounted after hydration completes
  useEffect(() => {
    setMounted(true)
  }, [])

  // Apply theme to document and compute resolved theme
  useEffect(() => {
    if (typeof window === 'undefined') return

    // Compute resolved theme
    let newResolvedTheme: ResolvedTheme = 'light'
    if (theme === 'auto') {
      newResolvedTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
    } else {
      newResolvedTheme = theme
    }

    setResolvedTheme(newResolvedTheme)

    // Update document class
    const root = document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(newResolvedTheme)

    // Update meta theme-color for mobile browsers
    const metaThemeColor = document.querySelector('meta[name="theme-color"]')
    if (metaThemeColor) {
      metaThemeColor.setAttribute(
        'content',
        newResolvedTheme === 'dark' ? '#111827' : '#ffffff'
      )
    }

    // Listen for system preference changes (only if theme is 'auto')
    if (theme === 'auto') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

      const handleChange = (e: MediaQueryListEvent) => {
        const updatedTheme = e.matches ? 'dark' : 'light'
        setResolvedTheme(updatedTheme)
        root.classList.remove('light', 'dark')
        root.classList.add(updatedTheme)
      }

      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    }
  }, [theme])

  // Return consistent values during SSR/hydration
  // Only return actual resolved theme after mounting
  return {
    theme,
    setTheme,
    resolvedTheme: mounted ? resolvedTheme : 'light',
    isDark: mounted ? resolvedTheme === 'dark' : false,
    isLight: mounted ? resolvedTheme === 'light' : true
  }
}
