/**
 * useTheme hook for dark mode support
 * Respects system preference and persists user choice
 */

import { useEffect } from 'react'
import { useLocalStorage } from './useLocalStorage'

export type Theme = 'light' | 'dark' | 'auto'
export type ResolvedTheme = 'light' | 'dark'

/**
 * Hook to manage theme (light/dark/auto)
 * @returns Theme state and control functions
 */
export function useTheme() {
  const [theme, setTheme] = useLocalStorage<Theme>('swarmit-theme', 'auto')

  // Get resolved theme (light or dark)
  const getResolvedTheme = (): ResolvedTheme => {
    if (typeof window === 'undefined') return 'light'

    if (theme === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
    }

    return theme
  }

  // Apply theme to document
  useEffect(() => {
    if (typeof window === 'undefined') return

    const resolvedTheme = getResolvedTheme()

    // Update document class
    const root = document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(resolvedTheme)

    // Update meta theme-color for mobile browsers
    const metaThemeColor = document.querySelector('meta[name="theme-color"]')
    if (metaThemeColor) {
      metaThemeColor.setAttribute(
        'content',
        resolvedTheme === 'dark' ? '#111827' : '#ffffff'
      )
    }

    // Listen for system preference changes (only if theme is 'auto')
    if (theme === 'auto') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

      const handleChange = (e: MediaQueryListEvent) => {
        const newResolvedTheme = e.matches ? 'dark' : 'light'
        root.classList.remove('light', 'dark')
        root.classList.add(newResolvedTheme)
      }

      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    }
  }, [theme])

  return {
    theme,
    setTheme,
    resolvedTheme: getResolvedTheme(),
    isDark: getResolvedTheme() === 'dark',
    isLight: getResolvedTheme() === 'light'
  }
}
