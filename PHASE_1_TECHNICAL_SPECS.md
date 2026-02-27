# Phase 1: Foundation - Technical Specifications
**Week 1-2 Implementation Guide**

## 🎯 Goals

1. Standardize MDX frontmatter schema
2. Implement dark mode
3. Add basic search functionality
4. Calculate reading time
5. Set up component library structure
6. Create reusable hooks

---

## 📋 Task Breakdown

### Task 1.1: MDX Frontmatter Schema
**Priority:** CRITICAL
**Estimated Time:** 4 hours

#### Implementation

**Create schema validator:**
```typescript
// src/utils/validation.ts
export interface PaperFrontmatter {
  // Core metadata
  title: string
  arxiv_id: string
  authors: string[]
  published_date: string
  go_live_date: string

  // RSCT Certification
  kappa: number
  rsn_score: string  // "0.75/0.82/0.43"
  R: number
  S: number
  N: number

  // Classification
  tags: string[]
  primary_topic: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'

  // Content
  abstract: string
  tldr?: string
  reading_time?: number  // auto-calculated
  word_count?: number    // auto-calculated

  // Links
  arxiv_url: string
  pdf_url?: string
  github_url?: string

  // Status
  status: 'staging' | 'live'
  featured?: boolean
}

export function validatePaperFrontmatter(
  frontmatter: any
): { valid: boolean; errors: string[] } {
  const errors: string[] = []

  // Required fields
  if (!frontmatter.title) errors.push('Missing title')
  if (!frontmatter.arxiv_id) errors.push('Missing arxiv_id')
  if (typeof frontmatter.kappa !== 'number') errors.push('Invalid kappa')
  if (frontmatter.kappa < 0 || frontmatter.kappa > 1) {
    errors.push('Kappa must be between 0 and 1')
  }

  // RSN validation (must sum to ~1)
  const rsnSum = frontmatter.R + frontmatter.S + frontmatter.N
  if (Math.abs(rsnSum - 1.0) > 0.01) {
    errors.push(`RSN values must sum to 1.0 (got ${rsnSum})`)
  }

  // Tags validation
  if (!Array.isArray(frontmatter.tags) || frontmatter.tags.length === 0) {
    errors.push('Must have at least one tag')
  }

  return {
    valid: errors.length === 0,
    errors
  }
}
```

**Gatsby Node API:**
```typescript
// gatsby-node.ts
import { validatePaperFrontmatter } from './src/utils/validation'

export const onCreateNode: GatsbyNode['onCreateNode'] = ({ node, actions }) => {
  const { createNodeField } = actions

  if (node.internal.type === 'Mdx') {
    const frontmatter = node.frontmatter as any

    // Validate frontmatter
    const validation = validatePaperFrontmatter(frontmatter)
    if (!validation.valid) {
      console.error(`❌ Invalid frontmatter in ${node.fileAbsolutePath}:`)
      validation.errors.forEach(err => console.error(`   - ${err}`))
      throw new Error('Frontmatter validation failed')
    }

    // Add computed fields
    createNodeField({
      node,
      name: 'qualityTier',
      value: getQualityTier(frontmatter.kappa)
    })
  }
}

function getQualityTier(kappa: number): string {
  if (kappa >= 0.9) return 'exceptional'
  if (kappa >= 0.8) return 'high-quality'
  if (kappa >= 0.7) return 'certified'
  return 'pending'
}
```

**Template MDX file:**
```markdown
<!-- content/reviews/_TEMPLATE.mdx -->
---
# Core metadata
title: "Paper Title Here"
arxiv_id: "2402.12345"
authors: ["Last, First", "Last, First"]
published_date: "2024-02-15"
go_live_date: "2026-03-01"

# RSCT Certification
kappa: 0.85
rsn_score: "0.75/0.82/0.43"
R: 0.75
S: 0.82
N: 0.43

# Classification
tags: ["multi-agent", "llm-reasoning"]
primary_topic: "multi-agent"
difficulty: "advanced"

# Content
abstract: "Short abstract summarizing the paper's contribution..."
tldr: |
  • Key finding 1
  • Key finding 2
  • Key finding 3

# Links
arxiv_url: "https://arxiv.org/abs/2402.12345"
pdf_url: "https://arxiv.org/pdf/2402.12345.pdf"
github_url: "https://github.com/author/repo"

# Status
status: "live"
featured: false
---

## Summary

Paper analysis content here...

## Key Contributions

1. First contribution
2. Second contribution

## Methodology

...

## Results

...

## Implications

...
```

---

### Task 1.2: Dark Mode Implementation
**Priority:** HIGH
**Estimated Time:** 6 hours

#### Implementation

**Theme hook:**
```typescript
// src/hooks/useTheme.ts
import { useEffect, useState } from 'react'
import { useLocalStorage } from './useLocalStorage'

type Theme = 'light' | 'dark' | 'auto'

export function useTheme() {
  const [storedTheme, setStoredTheme] = useLocalStorage<Theme>('swarmit-theme', 'auto')
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    const applyTheme = () => {
      let theme: 'light' | 'dark' = 'light'

      if (storedTheme === 'auto') {
        // Use system preference
        theme = window.matchMedia('(prefers-color-scheme: dark)').matches
          ? 'dark'
          : 'light'
      } else {
        theme = storedTheme
      }

      // Apply to document
      document.documentElement.classList.remove('light', 'dark')
      document.documentElement.classList.add(theme)
      document.documentElement.style.colorScheme = theme

      setResolvedTheme(theme)
    }

    applyTheme()

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => {
      if (storedTheme === 'auto') applyTheme()
    }
    mediaQuery.addEventListener('change', handler)

    return () => mediaQuery.removeEventListener('change', handler)
  }, [storedTheme])

  return {
    theme: storedTheme,
    resolvedTheme,
    setTheme: setStoredTheme,
    toggleTheme: () => {
      setStoredTheme(prev => {
        if (prev === 'light') return 'dark'
        if (prev === 'dark') return 'auto'
        return 'light'
      })
    }
  }
}
```

**Theme toggle component:**
```tsx
// src/components/ui/ThemeToggle.tsx
import React from 'react'
import { useTheme } from '../../hooks/useTheme'

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme()

  const icons = {
    light: '☀️',
    dark: '🌙',
    auto: '⚙️'
  }

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
      aria-label={`Switch theme (current: ${theme})`}
      title={`Current: ${theme} mode`}
    >
      <span className="text-2xl" role="img" aria-hidden="true">
        {icons[theme]}
      </span>
    </button>
  )
}
```

**CSS variables:**
```css
/* src/styles/theme.css */
:root {
  /* Light mode (default) */
  --color-primary: #60a5fa;      /* blue-400 */
  --color-accent: #fbbf24;       /* amber-400 */
  --color-bg: #ffffff;
  --color-bg-secondary: #f9fafb; /* gray-50 */
  --color-text: #111827;         /* gray-900 */
  --color-text-secondary: #6b7280; /* gray-500 */
  --color-border: #e5e7eb;       /* gray-200 */

  /* Quality badges */
  --color-exceptional: #fbbf24;  /* gold */
  --color-high-quality: #e5e7eb; /* silver */
  --color-certified: #cd7f32;    /* bronze */
}

.dark {
  /* Dark mode overrides */
  --color-primary: #3b82f6;      /* blue-500 */
  --color-accent: #f59e0b;       /* amber-500 */
  --color-bg: #111827;           /* gray-900 */
  --color-bg-secondary: #1f2937; /* gray-800 */
  --color-text: #f3f4f6;         /* gray-100 */
  --color-text-secondary: #9ca3af; /* gray-400 */
  --color-border: #374151;       /* gray-700 */
}

/* Apply theme colors */
body {
  background-color: var(--color-bg);
  color: var(--color-text);
  transition: background-color 0.2s ease, color 0.2s ease;
}
```

**Tailwind configuration:**
```javascript
// site/tailwind.config.js
module.exports = {
  darkMode: 'class', // Use .dark class instead of media query
  content: [
    './src/**/*.{js,jsx,ts,tsx,md,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Map to CSS variables
        'primary': 'var(--color-primary)',
        'accent': 'var(--color-accent)',
      }
    }
  }
}
```

---

### Task 1.3: Reading Time Calculator
**Priority:** MEDIUM
**Estimated Time:** 2 hours

#### Implementation

**Reading time utility:**
```typescript
// src/utils/readingTime.ts
export interface ReadingTimeResult {
  text: string
  minutes: number
  words: number
  time: number  // milliseconds
}

export function calculateReadingTime(
  content: string,
  wordsPerMinute: number = 200
): ReadingTimeResult {
  // Remove MDX/HTML tags
  const plainText = content
    .replace(/<\/?[^>]+(>|$)/g, '')  // HTML tags
    .replace(/```[\s\S]*?```/g, '')  // Code blocks
    .replace(/`[^`]+`/g, '')         // Inline code

  // Count words
  const words = plainText.match(/\w+/g)?.length || 0

  // Calculate time
  const minutes = Math.ceil(words / wordsPerMinute)
  const time = Math.ceil((words / wordsPerMinute) * 60 * 1000)

  // Generate text
  const text = minutes === 1
    ? '1 min read'
    : `${minutes} min read`

  return {
    text,
    minutes,
    words,
    time
  }
}
```

**Gatsby node enhancement:**
```typescript
// gatsby-node.ts
import { calculateReadingTime } from './src/utils/readingTime'

export const onCreateNode: GatsbyNode['onCreateNode'] = ({ node, actions, getNode }) => {
  const { createNodeField } = actions

  if (node.internal.type === 'Mdx') {
    // Get the MDX content
    const fileNode = getNode(node.parent)
    const content = node.body || ''

    // Calculate reading time
    const readingTime = calculateReadingTime(content)

    // Add as field
    createNodeField({
      node,
      name: 'readingTime',
      value: readingTime
    })
  }
}
```

**Reading time component:**
```tsx
// src/components/content/ReadingTime.tsx
import React from 'react'

interface ReadingTimeProps {
  minutes: number
  words: number
  className?: string
}

export const ReadingTime: React.FC<ReadingTimeProps> = ({
  minutes,
  words,
  className = ''
}) => {
  return (
    <div className={`flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 ${className}`}>
      <span className="flex items-center gap-1">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {minutes} min read
      </span>
      <span className="flex items-center gap-1">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        {words.toLocaleString()} words
      </span>
    </div>
  )
}
```

---

### Task 1.4: Basic Search
**Priority:** HIGH
**Estimated Time:** 8 hours

#### Implementation

**Install dependencies:**
```bash
npm install fuse.js
npm install --save-dev @types/fuse.js
```

**Search utility:**
```typescript
// src/utils/search.ts
import Fuse from 'fuse.js'

export interface SearchablePaper {
  id: string
  title: string
  abstract: string
  authors: string[]
  tags: string[]
  kappa: number
  published_date: string
  slug: string
}

export function createSearchIndex(papers: SearchablePaper[]) {
  return new Fuse(papers, {
    keys: [
      { name: 'title', weight: 2 },
      { name: 'abstract', weight: 1.5 },
      { name: 'authors', weight: 1 },
      { name: 'tags', weight: 1.2 }
    ],
    threshold: 0.3,
    includeScore: true,
    useExtendedSearch: true
  })
}

export interface SearchOptions {
  query: string
  tags?: string[]
  minKappa?: number
  sortBy?: 'relevance' | 'date' | 'quality'
}

export function searchPapers(
  index: Fuse<SearchablePaper>,
  options: SearchOptions
): SearchablePaper[] {
  let results = options.query
    ? index.search(options.query).map(r => r.item)
    : index.getIndex().docs as SearchablePaper[]

  // Filter by tags
  if (options.tags && options.tags.length > 0) {
    results = results.filter(paper =>
      options.tags!.some(tag => paper.tags.includes(tag))
    )
  }

  // Filter by minimum kappa
  if (options.minKappa !== undefined) {
    results = results.filter(paper => paper.kappa >= options.minKappa!)
  }

  // Sort results
  switch (options.sortBy) {
    case 'date':
      results.sort((a, b) =>
        new Date(b.published_date).getTime() - new Date(a.published_date).getTime()
      )
      break
    case 'quality':
      results.sort((a, b) => b.kappa - a.kappa)
      break
    // 'relevance' is default from Fuse.js
  }

  return results
}
```

**Search hook:**
```typescript
// src/hooks/useSearch.ts
import { useMemo, useState } from 'react'
import { createSearchIndex, searchPapers, SearchablePaper, SearchOptions } from '../utils/search'

export function useSearch(papers: SearchablePaper[]) {
  const [query, setQuery] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [minKappa, setMinKappa] = useState<number>(0)
  const [sortBy, setSortBy] = useState<'relevance' | 'date' | 'quality'>('relevance')

  // Create search index (memoized)
  const searchIndex = useMemo(() => createSearchIndex(papers), [papers])

  // Perform search
  const results = useMemo(() => {
    const options: SearchOptions = {
      query,
      tags: selectedTags.length > 0 ? selectedTags : undefined,
      minKappa: minKappa > 0 ? minKappa : undefined,
      sortBy
    }
    return searchPapers(searchIndex, options)
  }, [searchIndex, query, selectedTags, minKappa, sortBy])

  return {
    query,
    setQuery,
    selectedTags,
    setSelectedTags,
    minKappa,
    setMinKappa,
    sortBy,
    setSortBy,
    results,
    resultCount: results.length
  }
}
```

**Search box component:**
```tsx
// src/components/search/SearchBox.tsx
import React from 'react'

interface SearchBoxProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

export const SearchBox: React.FC<SearchBoxProps> = ({
  value,
  onChange,
  placeholder = 'Search papers...',
  className = ''
}) => {
  return (
    <div className={`relative ${className}`}>
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
        aria-label="Search papers"
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute inset-y-0 right-0 pr-3 flex items-center"
          aria-label="Clear search"
        >
          <svg className="h-5 w-5 text-gray-400 hover:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  )
}
```

---

### Task 1.5: localStorage Hook
**Priority:** HIGH
**Estimated Time:** 2 hours

#### Implementation

```typescript
// src/hooks/useLocalStorage.ts
import { useState, useEffect } from 'react'

export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((val: T) => T)) => void] {
  // State to store our value
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue
    }

    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      console.warn(`Error loading localStorage key "${key}":`, error)
      return initialValue
    }
  })

  // Update localStorage when value changes
  const setValue = (value: T | ((val: T) => T)) => {
    try {
      // Allow value to be a function for same API as useState
      const valueToStore = value instanceof Function ? value(storedValue) : value

      setStoredValue(valueToStore)

      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore))
      }
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error)
    }
  }

  // Sync across tabs
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === key && e.newValue) {
        setStoredValue(JSON.parse(e.newValue))
      }
    }

    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [key])

  return [storedValue, setValue]
}
```

---

## 🧪 Testing Requirements

### Unit Tests

```typescript
// src/utils/readingTime.test.ts
import { calculateReadingTime } from './readingTime'

describe('calculateReadingTime', () => {
  it('calculates reading time correctly', () => {
    const content = 'word '.repeat(200)  // 200 words
    const result = calculateReadingTime(content)

    expect(result.words).toBe(200)
    expect(result.minutes).toBe(1)
    expect(result.text).toBe('1 min read')
  })

  it('handles code blocks', () => {
    const content = `
      Some text
      \`\`\`javascript
      const code = 'should be excluded'
      \`\`\`
      More text
    `
    const result = calculateReadingTime(content)

    expect(result.words).toBeLessThan(content.split(' ').length)
  })
})
```

```typescript
// src/hooks/useLocalStorage.test.ts
import { renderHook, act } from '@testing-library/react-hooks'
import { useLocalStorage } from './useLocalStorage'

describe('useLocalStorage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('returns initial value', () => {
    const { result } = renderHook(() => useLocalStorage('test', 'initial'))
    expect(result.current[0]).toBe('initial')
  })

  it('updates localStorage', () => {
    const { result } = renderHook(() => useLocalStorage('test', 'initial'))

    act(() => {
      result.current[1]('updated')
    })

    expect(result.current[0]).toBe('updated')
    expect(localStorage.getItem('test')).toBe('"updated"')
  })
})
```

---

## 📦 Deliverables

### Week 1
- [ ] MDX schema defined and documented
- [ ] Validation utility implemented
- [ ] Template MDX file created
- [ ] Dark mode fully functional
- [ ] Reading time calculator working

### Week 2
- [ ] Search functionality complete
- [ ] localStorage hook implemented
- [ ] Component library structure set up
- [ ] All unit tests passing
- [ ] Documentation updated

---

## 🚀 Deployment Checklist

- [ ] All TypeScript compiles without errors
- [ ] Gatsby build succeeds
- [ ] All tests pass
- [ ] Dark mode works in all browsers
- [ ] Search index generates correctly
- [ ] Reading times display on all papers
- [ ] localStorage persists across sessions
- [ ] Performance metrics met (Lighthouse >90)

---

**Status:** Ready to Implement
**Estimated Total Time:** 22 hours (11 hours/week × 2 weeks)
**Dependencies:** None
**Blockers:** None
