/**
 * ThemeToggle component for dark mode switching
 * Displays sun/moon icon and cycles through light/dark/auto
 */

import React from 'react'
import { useTheme } from '../../hooks/useTheme'

export const ThemeToggle: React.FC = () => {
  const { theme, setTheme, isDark } = useTheme()

  const cycleTheme = () => {
    const next: Record<string, 'light' | 'dark' | 'auto'> = {
      light: 'dark',
      dark: 'auto',
      auto: 'light'
    }
    setTheme(next[theme])
  }

  return (
    <button
      onClick={cycleTheme}
      className="relative p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
      aria-label={`Current theme: ${theme}. Click to cycle themes.`}
      title={`Theme: ${theme}`}
    >
      {/* Sun icon (light mode) */}
      <svg
        className={`w-5 h-5 transition-opacity ${isDark ? 'opacity-0 absolute' : 'opacity-100'}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
        />
      </svg>

      {/* Moon icon (dark mode) */}
      <svg
        className={`w-5 h-5 transition-opacity ${isDark ? 'opacity-100' : 'opacity-0 absolute'}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
        />
      </svg>

      {/* Auto indicator */}
      {theme === 'auto' && (
        <span className="absolute -top-1 -right-1 w-2 h-2 bg-blue-500 rounded-full" />
      )}
    </button>
  )
}
