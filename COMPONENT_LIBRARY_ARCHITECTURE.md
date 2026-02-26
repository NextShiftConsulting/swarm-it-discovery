# Component Library Architecture
**Complete Component Hierarchy for nsc-swarmit**

## 🏗️ Architecture Overview

```
Atomic Design Principles:
├── Atoms      → Basic UI elements (buttons, badges, inputs)
├── Molecules  → Simple component groups (card headers, search bars)
├── Organisms  → Complex components (paper cards, leaderboards)
├── Templates  → Page layouts
└── Pages      → Fully composed pages
```

---

## 📦 Component Structure

### `/src/components/ui/` - Atoms & Basic UI
**Purpose:** Reusable, unstyled UI primitives

```
ui/
├── ThemeToggle.tsx           # Phase 1 - Dark mode switch
├── Badge.tsx                 # Phase 3 - Quality badges
├── Button.tsx                # Phase 1 - Styled buttons
├── Input.tsx                 # Phase 1 - Form inputs
├── Select.tsx                # Phase 2 - Dropdowns
├── Tooltip.tsx               # Phase 2 - Hover info
├── Modal.tsx                 # Phase 2 - Dialogs
├── Spinner.tsx               # Phase 1 - Loading states
└── Icon.tsx                  # Phase 1 - SVG icons
```

**Example: Badge.tsx**
```tsx
export interface BadgeProps {
  variant: 'exceptional' | 'high-quality' | 'certified' | 'default'
  size?: 'sm' | 'md' | 'lg'
  children: React.ReactNode
}

export const Badge: React.FC<BadgeProps> = ({
  variant,
  size = 'md',
  children
}) => {
  const variantClasses = {
    exceptional: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    'high-quality': 'bg-gray-100 text-gray-800 border-gray-300',
    certified: 'bg-amber-100 text-amber-800 border-amber-300',
    default: 'bg-blue-100 text-blue-800 border-blue-300'
  }

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base'
  }

  return (
    <span className={`inline-flex items-center border rounded-full font-medium ${variantClasses[variant]} ${sizeClasses[size]}`}>
      {children}
    </span>
  )
}
```

---

### `/src/components/search/` - Search & Discovery
**Purpose:** Search functionality components

```
search/
├── SearchBox.tsx             # Phase 1 - Basic text search
├── SearchFilters.tsx         # Phase 2 - Advanced filters
│   ├── TagFilter.tsx         # Phase 2 - Filter by tags
│   ├── KappaFilter.tsx       # Phase 2 - κ threshold slider
│   └── DateRangeFilter.tsx   # Phase 2 - Date range picker
├── SearchResults.tsx         # Phase 2 - Results display
├── SearchStats.tsx           # Phase 2 - "X results in Yms"
└── SavedSearches.tsx         # Phase 2 - Quick search presets
```

**Example: SearchFilters.tsx**
```tsx
interface SearchFiltersProps {
  selectedTags: string[]
  onTagsChange: (tags: string[]) => void
  minKappa: number
  onKappaChange: (kappa: number) => void
  sortBy: 'relevance' | 'date' | 'quality'
  onSortChange: (sort: 'relevance' | 'date' | 'quality') => void
  availableTags: string[]
}

export const SearchFilters: React.FC<SearchFiltersProps> = ({
  selectedTags,
  onTagsChange,
  minKappa,
  onKappaChange,
  sortBy,
  onSortChange,
  availableTags
}) => {
  return (
    <div className="space-y-4 p-4 bg-white dark:bg-gray-800 rounded-lg border">
      {/* Tag checkboxes */}
      <TagFilter
        selected={selectedTags}
        onChange={onTagsChange}
        available={availableTags}
      />

      {/* Kappa slider */}
      <KappaFilter
        value={minKappa}
        onChange={onKappaChange}
      />

      {/* Sort dropdown */}
      <Select value={sortBy} onChange={onSortChange}>
        <option value="relevance">Relevance</option>
        <option value="date">Newest First</option>
        <option value="quality">Highest κ</option>
      </Select>
    </div>
  )
}
```

---

### `/src/components/quality/` - RSCT Certification
**Purpose:** Quality scoring and certification display

```
quality/
├── KappaGateBadge.tsx        # Phase 3 - κ score badge
├── RSNBar.tsx                # Phase 3 - R/S/N visualization
├── RSNBreakdown.tsx          # Phase 3 - Detailed RSN metrics
├── QualityLeaderboard.tsx    # Phase 3 - Top papers by κ
├── QualityTrend.tsx          # Phase 4 - κ over time chart
├── CompareView.tsx           # Phase 3 - Side-by-side comparison
└── CertificateExport.tsx     # Phase 5 - Download certificate
```

**Example: RSNBar.tsx**
```tsx
interface RSNBarProps {
  R: number  // 0-1
  S: number  // 0-1
  N: number  // 0-1
  showLabels?: boolean
  className?: string
}

export const RSNBar: React.FC<RSNBarProps> = ({
  R, S, N,
  showLabels = true,
  className = ''
}) => {
  // Normalize to percentages
  const total = R + S + N
  const rPct = (R / total) * 100
  const sPct = (S / total) * 100
  const nPct = (N / total) * 100

  return (
    <div className={className}>
      {showLabels && (
        <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
          <span>R: {R.toFixed(2)}</span>
          <span>S: {S.toFixed(2)}</span>
          <span>N: {N.toFixed(2)}</span>
        </div>
      )}
      <div className="flex h-2 rounded-full overflow-hidden">
        <div
          className="bg-blue-500"
          style={{ width: `${rPct}%` }}
          title={`Relevance: ${R.toFixed(2)}`}
        />
        <div
          className="bg-green-500"
          style={{ width: `${sPct}%` }}
          title={`Stability: ${S.toFixed(2)}`}
        />
        <div
          className="bg-amber-500"
          style={{ width: `${nPct}%` }}
          title={`Novelty: ${N.toFixed(2)}`}
        />
      </div>
    </div>
  )
}
```

---

### `/src/components/content/` - Paper Content Display
**Purpose:** Paper card, summary, and content components

```
content/
├── PaperCard.tsx             # Phase 1 - Paper preview card
├── PaperCardList.tsx         # Phase 2 - Grid/list of cards
├── PaperSummary.tsx          # Phase 5 - TL;DR section
├── PaperMetadata.tsx         # Phase 1 - Authors, dates, links
├── ReadingTime.tsx           # Phase 1 - Est. reading time
├── DifficultyBadge.tsx       # Phase 5 - Difficulty indicator
├── TldrSummary.tsx           # Phase 5 - Bullet point summary
├── CitationExport.tsx        # Phase 5 - BibTeX/APA export
└── SocialShare.tsx           # Phase 5 - Share buttons
```

**Example: PaperCard.tsx**
```tsx
interface PaperCardProps {
  paper: {
    title: string
    abstract: string
    authors: string[]
    tags: string[]
    kappa: number
    R: number
    S: number
    N: number
    published_date: string
    reading_time: { minutes: number; words: number }
    slug: string
    qualityTier: 'exceptional' | 'high-quality' | 'certified'
  }
  variant?: 'compact' | 'default' | 'detailed'
}

export const PaperCard: React.FC<PaperCardProps> = ({
  paper,
  variant = 'default'
}) => {
  return (
    <article className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <Link to={`/papers/${paper.slug}`}>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 hover:text-primary">
            {paper.title}
          </h3>
        </Link>
        <KappaGateBadge kappa={paper.kappa} tier={paper.qualityTier} />
      </div>

      {/* Metadata */}
      <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-3">
        <span>{paper.authors.slice(0, 3).join(', ')}</span>
        <span>•</span>
        <span>{new Date(paper.published_date).toLocaleDateString()}</span>
        <span>•</span>
        <ReadingTime minutes={paper.reading_time.minutes} words={paper.reading_time.words} compact />
      </div>

      {/* RSN Bar */}
      <RSNBar R={paper.R} S={paper.S} N={paper.N} className="mb-3" />

      {/* Abstract */}
      <p className="text-gray-700 dark:text-gray-300 mb-3 line-clamp-3">
        {paper.abstract}
      </p>

      {/* Tags */}
      <div className="flex flex-wrap gap-2">
        {paper.tags.map(tag => (
          <Badge key={tag} variant="default" size="sm">
            {tag}
          </Badge>
        ))}
      </div>
    </article>
  )
}
```

---

### `/src/components/discovery/` - Discovery Features
**Purpose:** Topic filters, reading lists, related papers

```
discovery/
├── TopicFilter.tsx           # Phase 2 - Filter by topic
├── TopicCloud.tsx            # Phase 4 - Tag cloud visualization
├── RelatedPapers.tsx         # Phase 2 - Similarity suggestions
├── ReadingList.tsx           # Phase 2 - Saved papers list
├── ReadingListButton.tsx     # Phase 2 - Add to list CTA
└── RecommendedPapers.tsx     # Phase 4 - Algorithm-based recs
```

**Example: RelatedPapers.tsx**
```tsx
interface RelatedPapersProps {
  currentPaper: {
    id: string
    tags: string[]
    authors: string[]
  }
  allPapers: Paper[]
  maxResults?: number
}

export const RelatedPapers: React.FC<RelatedPapersProps> = ({
  currentPaper,
  allPapers,
  maxResults = 5
}) => {
  const related = useMemo(() => {
    return findRelatedPapers(currentPaper, allPapers, maxResults)
  }, [currentPaper, allPapers, maxResults])

  if (related.length === 0) return null

  return (
    <aside className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Related Papers</h3>
      <ul className="space-y-3">
        {related.map(paper => (
          <li key={paper.id}>
            <Link
              to={`/papers/${paper.slug}`}
              className="block hover:bg-gray-100 dark:hover:bg-gray-700 p-3 rounded transition"
            >
              <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                {paper.title}
              </h4>
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <span>{Math.round(paper.similarity * 100)}% similar</span>
                <span>•</span>
                <KappaGateBadge kappa={paper.kappa} size="sm" />
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </aside>
  )
}

// Similarity algorithm
function findRelatedPapers(
  current: { tags: string[]; authors: string[] },
  all: Paper[],
  limit: number
): (Paper & { similarity: number })[] {
  return all
    .filter(p => p.id !== current.id)
    .map(paper => {
      let score = 0

      // Shared tags
      const sharedTags = paper.tags.filter(t => current.tags.includes(t))
      score += sharedTags.length * 0.4

      // Shared authors
      const sharedAuthors = paper.authors.filter(a => current.authors.includes(a))
      score += sharedAuthors.length * 0.6

      return { ...paper, similarity: Math.min(score, 1) }
    })
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, limit)
}
```

---

### `/src/components/visualization/` - Data Visualizations
**Purpose:** Charts, graphs, timelines

```
visualization/
├── Timeline.tsx              # Phase 4 - Publication timeline
├── TopicHeatmap.tsx          # Phase 4 - Topics over time
├── SimilarityGraph.tsx       # Phase 4 - Network graph (D3)
├── TrendsDashboard.tsx       # Phase 4 - Multi-chart dashboard
├── AuthorNetwork.tsx         # Phase 4 - Co-author graph
└── QualityDistribution.tsx   # Phase 4 - κ histogram
```

**Dependencies:**
```json
{
  "d3": "^7.9.0",
  "react-d3-graph": "^8.6.0",
  "recharts": "^2.10.0"
}
```

**Example: TopicHeatmap.tsx**
```tsx
import { ResponsiveHeatMap } from '@nivo/heatmap'

interface TopicHeatmapProps {
  data: {
    topic: string
    months: { month: string; count: number }[]
  }[]
}

export const TopicHeatmap: React.FC<TopicHeatmapProps> = ({ data }) => {
  return (
    <div className="h-96">
      <ResponsiveHeatMap
        data={data}
        margin={{ top: 60, right: 90, bottom: 60, left: 90 }}
        valueFormat=">-.0s"
        axisTop={{
          tickSize: 5,
          tickPadding: 5,
          tickRotation: -90,
        }}
        colors={{
          type: 'diverging',
          scheme: 'blue_green',
          divergeAt: 0.5,
        }}
        emptyColor="#555555"
        borderColor={{ from: 'color', modifiers: [['darker', 0.6]] }}
      />
    </div>
  )
}
```

---

### `/src/components/workflow/` - Staging & Publishing
**Purpose:** Workflow management components

```
workflow/
├── StagingPreview.tsx        # Phase 6 - Show unpublished papers
├── StagingBanner.tsx         # Phase 6 - "Preview mode" indicator
├── PublicationCalendar.tsx   # Phase 6 - Scheduled publications
├── EmailDigest.tsx           # Phase 6 - Generate email HTML
└── MetadataValidator.tsx     # Phase 6 - Frontmatter checker
```

---

### `/src/components/layout/` - Page Layouts
**Purpose:** Page structure and navigation

```
layout/
├── Layout.tsx                # Phase 1 - Main layout wrapper
├── Header.tsx                # Phase 1 - Site header
├── Footer.tsx                # Phase 1 - Site footer (exists)
├── Sidebar.tsx               # Phase 2 - Optional sidebar
└── SEO.tsx                   # Phase 5 - Meta tags
```

---

## 🔄 Component Interactions

### Search Flow
```
User Input → SearchBox
           ↓
      useSearch hook
           ↓
      SearchFilters (tags, kappa, sort)
           ↓
      searchPapers utility
           ↓
      SearchResults
           ↓
      PaperCardList
           ↓
      PaperCard[]
```

### Paper Detail Flow
```
URL (/papers/:slug)
    ↓
Paper Template
    ├── PaperMetadata
    ├── KappaGateBadge
    ├── RSNBar
    ├── MDX Content
    ├── CitationExport
    ├── SocialShare
    └── RelatedPapers
```

### Reading List Flow
```
PaperCard
    ↓
ReadingListButton (click)
    ↓
useLocalStorage('reading-list')
    ↓
Update state
    ↓
Show in ReadingList page
```

---

## 📊 Props Interfaces

### Shared Types
```typescript
// src/types/paper.ts
export interface Paper {
  id: string
  slug: string
  title: string
  abstract: string
  authors: string[]
  published_date: string
  go_live_date: string

  // RSCT
  kappa: number
  rsn_score: string
  R: number
  S: number
  N: number

  // Classification
  tags: string[]
  primary_topic: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'

  // Content
  tldr?: string
  reading_time: ReadingTime
  word_count: number

  // Links
  arxiv_url: string
  pdf_url?: string
  github_url?: string

  // Status
  status: 'staging' | 'live'
  featured: boolean

  // Computed
  qualityTier: 'exceptional' | 'high-quality' | 'certified' | 'pending'
}

export interface ReadingTime {
  text: string
  minutes: number
  words: number
  time: number
}
```

---

## 🎨 Styling Guidelines

### Tailwind Class Patterns

```typescript
// Card container
const cardClasses = "bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6"

// Text styles
const headingClasses = "text-xl font-semibold text-gray-900 dark:text-gray-100"
const bodyClasses = "text-gray-700 dark:text-gray-300"
const mutedClasses = "text-gray-600 dark:text-gray-400"

// Interactive elements
const buttonClasses = "px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition"
const linkClasses = "text-primary hover:text-primary/80 underline-offset-2 hover:underline"

// Quality tiers
const qualityClasses = {
  exceptional: "bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700",
  'high-quality': "bg-gray-50 dark:bg-gray-800 border-gray-300 dark:border-gray-700",
  certified: "bg-amber-50 dark:bg-amber-900/20 border-amber-300 dark:border-amber-700"
}
```

---

## 🧪 Component Testing

### Test Structure
```
__tests__/
├── components/
│   ├── search/
│   │   ├── SearchBox.test.tsx
│   │   └── SearchFilters.test.tsx
│   ├── quality/
│   │   ├── RSNBar.test.tsx
│   │   └── KappaGateBadge.test.tsx
│   └── content/
│       └── PaperCard.test.tsx
├── hooks/
│   ├── useSearch.test.ts
│   ├── useTheme.test.ts
│   └── useLocalStorage.test.ts
└── utils/
    ├── search.test.ts
    ├── readingTime.test.ts
    └── similarity.test.ts
```

### Example Test
```tsx
// __tests__/components/quality/RSNBar.test.tsx
import { render, screen } from '@testing-library/react'
import { RSNBar } from '../../../src/components/quality/RSNBar'

describe('RSNBar', () => {
  it('renders with correct proportions', () => {
    render(<RSNBar R={0.5} S={0.3} N={0.2} />)

    // Check bar segments exist
    const bars = screen.getAllByRole('presentation')
    expect(bars).toHaveLength(3)

    // Check proportions (50%, 30%, 20%)
    expect(bars[0]).toHaveStyle({ width: '50%' })
    expect(bars[1]).toHaveStyle({ width: '30%' })
    expect(bars[2]).toHaveStyle({ width: '20%' })
  })

  it('shows labels when enabled', () => {
    render(<RSNBar R={0.75} S={0.20} N={0.05} showLabels />)

    expect(screen.getByText('R: 0.75')).toBeInTheDocument()
    expect(screen.getByText('S: 0.20')).toBeInTheDocument()
    expect(screen.getByText('N: 0.05')).toBeInTheDocument()
  })
})
```

---

## 📦 Export Pattern

```typescript
// src/components/index.ts (barrel export)
export * from './ui'
export * from './search'
export * from './quality'
export * from './content'
export * from './discovery'
export * from './visualization'
export * from './workflow'
export * from './layout'

// Usage in pages:
import {
  SearchBox,
  PaperCard,
  RSNBar,
  TopicFilter
} from '../components'
```

---

**Status:** Architecture Defined
**Ready for:** Phase 1 Implementation
**Total Components:** 60+
**Complexity:** Medium-High
