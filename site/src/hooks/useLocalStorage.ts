/**
 * useLocalStorage hook for persistent browser storage
 * Used for reading lists, theme preferences, etc.
 */

import { useState, useEffect } from 'react'

/**
 * Hook to manage state synced with localStorage
 * @param key - localStorage key
 * @param initialValue - Default value if key doesn't exist
 * @returns [value, setValue] tuple
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((val: T) => T)) => void] {
  // State to store our value
  // Pass initial state function to useState so logic is only executed once
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue
    }

    try {
      // Get from local storage by key
      const item = window.localStorage.getItem(key)
      // Parse stored json or if none return initialValue
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      // If error also return initialValue
      console.error(`Error loading localStorage key "${key}":`, error)
      return initialValue
    }
  })

  // Return a wrapped version of useState's setter function that
  // persists the new value to localStorage
  const setValue = (value: T | ((val: T) => T)) => {
    try {
      // Allow value to be a function so we have same API as useState
      const valueToStore = value instanceof Function ? value(storedValue) : value

      // Save state
      setStoredValue(valueToStore)

      // Save to local storage
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore))

        // Dispatch custom event for cross-tab synchronization
        window.dispatchEvent(
          new CustomEvent('localStorage', {
            detail: { key, value: valueToStore }
          })
        )
      }
    } catch (error) {
      // More advanced implementation would handle the error
      console.error(`Error setting localStorage key "${key}":`, error)
    }
  }

  // Listen for changes in other tabs/windows
  useEffect(() => {
    if (typeof window === 'undefined') return

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === key && e.newValue !== null) {
        try {
          setStoredValue(JSON.parse(e.newValue))
        } catch (error) {
          console.error(`Error parsing localStorage change for key "${key}":`, error)
        }
      }
    }

    const handleCustomStorageChange = (e: Event) => {
      const customEvent = e as CustomEvent
      if (customEvent.detail?.key === key) {
        setStoredValue(customEvent.detail.value)
      }
    }

    // Listen for changes from other tabs
    window.addEventListener('storage', handleStorageChange)
    // Listen for changes from same tab
    window.addEventListener('localStorage', handleCustomStorageChange as EventListener)

    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('localStorage', handleCustomStorageChange as EventListener)
    }
  }, [key])

  return [storedValue, setValue]
}

/**
 * Hook to manage reading list in localStorage
 * @returns [readingList, addToList, removeFromList, clearList]
 */
export function useReadingList() {
  const [readingList, setReadingList] = useLocalStorage<string[]>('swarmit-reading-list', [])

  const addToList = (arxivId: string) => {
    setReadingList(prev => {
      if (prev.includes(arxivId)) return prev
      return [...prev, arxivId]
    })
  }

  const removeFromList = (arxivId: string) => {
    setReadingList(prev => prev.filter(id => id !== arxivId))
  }

  const clearList = () => {
    setReadingList([])
  }

  const isInList = (arxivId: string) => {
    return readingList.includes(arxivId)
  }

  return {
    readingList,
    addToList,
    removeFromList,
    clearList,
    isInList,
    count: readingList.length
  }
}
