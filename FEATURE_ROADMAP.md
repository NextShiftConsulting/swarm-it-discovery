# Swarm-It Feature Roadmap
**ncs-swarmit Enhancement Plan - Gatsby + MDX + File-Based**

## 📋 Overview

Complete feature set for automated research discovery platform using:
- ✅ Gatsby static site generation
- ✅ MDX for paper content
- ✅ File-based workflow (no database)
- ✅ Staging → Live publication system
- ✅ RSCT certification (κ-gate quality scoring)

---

## 🎯 Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal:** Core infrastructure & quick wins

- [ ] Project structure reorganization
- [ ] MDX frontmatter schema standardization
- [ ] Component library setup
- [ ] Dark mode implementation
- [ ] Basic search functionality
- [ ] Reading time calculator

**Priority:** CRITICAL - Everything depends on this

---

### Phase 2: Discovery & Navigation (Week 3-4)
**Goal:** Help users find relevant papers

- [ ] Advanced client-side search (Fuse.js)
- [ ] Dynamic topic filters
- [ ] Related papers algorithm
- [ ] Smart reading list (localStorage)
- [ ] Keyboard shortcuts
- [ ] RSS feed configuration (per topic)

**Priority:** HIGH - Core user experience

---

### Phase 3: Quality & Certification (Week 5-6)
**Goal:** Showcase RSCT value proposition

- [ ] κ-gate badge system
- [ ] RSN score visualizations
- [ ] Quality leaderboard
- [ ] Paper comparison view
- [ ] Certificate export/sharing

**Priority:** HIGH - Unique differentiator

---

### Phase 4: Visualizations (Week 7-8)
**Goal:** Visual insights into research landscape

- [ ] Research timeline view
- [ ] Topic heatmap
- [ ] Paper similarity graph (D3.js)
- [ ] Trends dashboard
- [ ] Author spotlight

**Priority:** MEDIUM - Nice-to-have insights

---

### Phase 5: Content Enhancement (Week 9-10)
**Goal:** Rich paper presentation

- [ ] TL;DR auto-summary extraction
- [ ] Citation export (BibTeX, APA, RIS)
- [ ] Print-optimized views
- [ ] Social share cards (OG tags)
- [ ] Estimated difficulty scoring

**Priority:** MEDIUM - Polish & utility

---

### Phase 6: Workflow Automation (Week 11-12)
**Goal:** Support staging → live workflow

- [ ] Staging preview mode
- [ ] Publication calendar
- [ ] Email digest generator
- [ ] Automated metadata validation
- [ ] Git-based publication triggers

**Priority:** LOW - Process improvements

---

## 📊 Feature Details Matrix

| Feature | Phase | Complexity | Impact | Dependencies |
|---------|-------|------------|--------|--------------|
| Dark Mode | 1 | Low | High | None |
| Reading Time | 1 | Low | Medium | None |
| Basic Search | 1 | Low | High | None |
| MDX Schema | 1 | Medium | Critical | None |
| Advanced Search | 2 | Medium | High | Phase 1 |
| Topic Filters | 2 | Medium | High | MDX Schema |
| Reading List | 2 | Low | Medium | localStorage |
| κ-Gate Badges | 3 | Low | High | MDX Schema |
| RSN Visualization | 3 | Medium | High | κ-Gate |
| Leaderboard | 3 | Low | Medium | MDX Schema |
| Timeline View | 4 | High | Medium | D3.js |
| Similarity Graph | 4 | High | Low | D3.js |
| Citation Export | 5 | Medium | High | MDX Schema |
| Staging Preview | 6 | Medium | Medium | Build config |

---

## 🏗️ Technical Architecture

### File Structure
```
ncs-swarmit/
├── site/
│   ├── src/
│   │   ├── components/
│   │   │   ├── search/
│   │   │   │   ├── SearchBox.tsx          # Phase 1
│   │   │   │   ├── AdvancedSearch.tsx     # Phase 2
│   │   │   │   └── SearchFilters.tsx      # Phase 2
│   │   │   ├── discovery/
│   │   │   │   ├── TopicFilter.tsx        # Phase 2
│   │   │   │   ├── RelatedPapers.tsx      # Phase 2
│   │   │   │   └── ReadingList.tsx        # Phase 2
│   │   │   ├── quality/
│   │   │   │   ├── KappaGateBadge.tsx     # Phase 3
│   │   │   │   ├── RSNBar.tsx             # Phase 3
│   │   │   │   ├── QualityLeaderboard.tsx # Phase 3
│   │   │   │   └── CompareView.tsx        # Phase 3
│   │   │   ├── visualization/
│   │   │   │   ├── Timeline.tsx           # Phase 4
│   │   │   │   ├── TopicHeatmap.tsx       # Phase 4
│   │   │   │   ├── SimilarityGraph.tsx    # Phase 4
│   │   │   │   └── TrendsDashboard.tsx    # Phase 4
│   │   │   ├── content/
│   │   │   │   ├── PaperCard.tsx          # Phase 5
│   │   │   │   ├── TldrSummary.tsx        # Phase 5
│   │   │   │   ├── CitationExport.tsx     # Phase 5
│   │   │   │   └── ReadingTime.tsx        # Phase 1
│   │   │   ├── workflow/
│   │   │   │   ├── StagingPreview.tsx     # Phase 6
│   │   │   │   ├── PublicationCalendar.tsx# Phase 6
│   │   │   │   └── EmailDigest.tsx        # Phase 6
│   │   │   └── ui/
│   │   │       ├── ThemeToggle.tsx        # Phase 1
│   │   │       ├── KeyboardShortcuts.tsx  # Phase 2
│   │   │       └── SocialShareCard.tsx    # Phase 5
│   │   ├── hooks/
│   │   │   ├── useLocalStorage.ts         # Phase 1
│   │   │   ├── useSearch.ts               # Phase 2
│   │   │   ├── useTheme.ts                # Phase 1
│   │   │   ├── useHotkeys.ts              # Phase 2
│   │   │   └── usePaperAnalytics.ts       # Phase 4
│   │   ├── utils/
│   │   │   ├── search.ts                  # Phase 2
│   │   │   ├── readingTime.ts             # Phase 1
│   │   │   ├── similarity.ts              # Phase 4
│   │   │   ├── citations.ts               # Phase 5
│   │   │   └── validation.ts              # Phase 6
│   │   └── styles/
│   │       ├── theme.css                  # Phase 1 (dark mode)
│   │       └── print.css                  # Phase 5
│   ├── content/
│   │   ├── reviews/                       # Live papers (published)
│   │   │   └── 2026-02-26-paper-title.mdx
│   │   ├── staging/                       # Unpublished papers
│   │   │   └── 2026-03-15-future-paper.mdx
│   │   └── topics/
│   │       └── topics.json                # Topic definitions
│   └── gatsby-config.ts
└── pipeline/                              # Python RSCT pipeline (existing)
```

---

## 📝 MDX Frontmatter Schema (Standardized)

### Required Fields
```yaml
---
# Core metadata
title: "Paper Title"
arxiv_id: "2402.12345"
authors: ["Smith, J.", "Chen, L.", "Kumar, R."]
published_date: "2024-02-15"
go_live_date: "2026-03-01"         # When to publish from staging

# RSCT Certification
kappa: 0.85                         # κ-gate score
rsn_score: "0.75/0.82/0.43"        # R/S/N breakdown
R: 0.75                             # Relevance
S: 0.82                             # Stability
N: 0.43                             # Novelty

# Classification
tags: ["multi-agent", "llm-reasoning", "control-theory"]
primary_topic: "multi-agent"
difficulty: "advanced"              # beginner|intermediate|advanced

# Content metadata
abstract: "Short abstract text..."
tldr: "• Key point 1\n• Key point 2\n• Key point 3"
reading_time: 12                    # minutes (auto-calculated)
word_count: 2400                    # (auto-calculated)

# Links
arxiv_url: "https://arxiv.org/abs/2402.12345"
pdf_url: "https://arxiv.org/pdf/2402.12345.pdf"
github_url: "https://github.com/author/repo"  # optional

# Status
status: "staging"                   # staging|live
featured: false                     # Show on homepage?
---
```

---

## 🔧 Technology Stack

### Core
- **Gatsby 5.14.0** - Static site generation
- **React 18.2.0** - Component framework
- **TypeScript 5.3.3** - Type safety
- **MDX 2.3.0** - Paper content format
- **Tailwind CSS 3.4.0** - Styling

### New Dependencies (Phase-specific)

#### Phase 1
```json
{
  "fuse.js": "^7.0.0",              // Fast fuzzy search
  "reading-time": "^1.5.0"          // Reading time calculation
}
```

#### Phase 2
```json
{
  "react-hotkeys-hook": "^4.4.0",   // Keyboard shortcuts
  "date-fns": "^3.0.0"              // Date utilities
}
```

#### Phase 4
```json
{
  "d3": "^7.9.0",                   // Visualizations
  "react-d3-graph": "^8.6.0",       // Graph component
  "recharts": "^2.10.0"             // Charts/heatmaps
}
```

#### Phase 5
```json
{
  "citation-js": "^0.7.0",          // Citation generation (BibTeX, APA)
  "react-to-print": "^2.15.0"       // Print optimization
}
```

---

## 🎨 Design System

### Color Palette (from nsc-main consistency)
```css
/* Light Mode */
--primary: #60a5fa;       /* blue-400 */
--accent: #fbbf24;        /* amber-400 */
--bg: #ffffff;
--text: #111827;          /* gray-900 */

/* Dark Mode */
--primary: #3b82f6;       /* blue-500 */
--accent: #f59e0b;        /* amber-500 */
--bg: #111827;            /* gray-900 */
--text: #f3f4f6;          /* gray-100 */

/* Quality Badges */
--exceptional: #fbbf24;   /* gold - κ≥0.9 */
--high-quality: #e5e7eb;  /* silver - κ≥0.8 */
--certified: #cd7f32;     /* bronze - κ≥0.7 */
```

### Component Variants
```typescript
// Badge sizes
type BadgeSize = 'sm' | 'md' | 'lg'

// Quality tiers
type QualityTier = 'exceptional' | 'high-quality' | 'certified' | 'pending'

// Theme modes
type Theme = 'light' | 'dark' | 'auto'
```

---

## 📦 Data Flow Architecture

### Paper Loading Pipeline
```
1. MDX Files (content/reviews/*.mdx)
   ↓
2. Gatsby GraphQL Layer
   ↓
3. React Components
   ↓
4. Client-side Enhancement
   - Search indexing (Fuse.js)
   - Similarity calculations
   - localStorage (reading list, theme)
```

### Search Architecture
```
Build Time:
- All MDX → GraphQL nodes
- Generate search index (Fuse.js)

Runtime:
- User types query
- Fuse.js searches pre-built index
- Filter by tags, kappa, date
- Sort by relevance/date/quality
```

### Staging → Live Workflow
```
1. Pipeline generates paper → staging/YYYY-MM-DD-title.mdx
2. Frontmatter: go_live_date: "2026-03-15"
3. Build script checks dates:
   - If go_live_date ≤ today → move to reviews/
   - If go_live_date > today → stays in staging/
4. Gatsby build only includes reviews/ (unless preview mode)
```

---

## 🧪 Testing Strategy

### Unit Tests
```bash
# Component tests
src/components/**/*.test.tsx

# Utility tests
src/utils/**/*.test.ts

# Hook tests
src/hooks/**/*.test.ts
```

### Integration Tests
```bash
# Search functionality
- Index generation
- Query matching
- Filter combinations

# Reading list
- Add/remove papers
- localStorage persistence
- Sync across tabs

# Theme switching
- localStorage persistence
- CSS variable updates
- Prefers-color-scheme
```

### E2E Tests (Playwright)
```bash
# Critical user flows
- Search → Filter → View paper
- Add to reading list → View list
- Dark mode toggle
- Citation export
```

---

## 📈 Success Metrics

### Performance Targets
- **Lighthouse Score:** 95+ (all categories)
- **Build Time:** <2 min for 100 papers
- **Search Response:** <50ms for 1000 papers
- **Bundle Size:** <500KB (main bundle)

### User Experience
- **Average Session:** 5+ min
- **Pages per Session:** 3+
- **Reading List Usage:** 20% of visitors
- **Citation Exports:** 10% of paper views

### Content Quality
- **Average κ Score:** ≥0.75
- **Papers per Week:** 5-10
- **Topics Covered:** 10+
- **False Positive Rate:** <5% (RSN classification)

---

## 🚀 Deployment Strategy

### Build Process
```bash
# Development
npm run develop

# Production build
npm run build

# Preview staging papers (dev only)
SHOW_STAGING=true npm run develop
```

### CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # Daily rebuild (for go_live_date)

jobs:
  deploy:
    - Check staging/ for papers ready to go live
    - Move to reviews/ if go_live_date passed
    - Build Gatsby site
    - Deploy to AWS S3 / Netlify
    - Invalidate CloudFront
```

---

## 📅 Timeline Summary

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1-2  | Phase 1 | Dark mode, search, reading time, MDX schema |
| 3-4  | Phase 2 | Advanced search, filters, reading list, RSS |
| 5-6  | Phase 3 | κ-badges, RSN viz, leaderboard, comparison |
| 7-8  | Phase 4 | Timeline, heatmap, similarity graph, trends |
| 9-10 | Phase 5 | Citations, print views, social cards |
| 11-12| Phase 6 | Staging preview, calendar, email digest |

**Total Duration:** ~12 weeks (3 months)

---

## 🎯 Next Steps

1. ✅ **Review & Approve Roadmap** (you are here)
2. ⏳ Create detailed technical specs for Phase 1
3. ⏳ Set up feature branches
4. ⏳ Begin Phase 1 implementation

---

## 📝 Notes

- All features must work **without a database**
- File-based workflow is **non-negotiable**
- Maintain **brand consistency** with nsc-main-gatsby
- **No AI attribution** in commits (git hooks enforced)
- RSCT certification is the **unique value proposition**

---

**Last Updated:** 2026-02-26
**Status:** Planning Approved ✅
**Next Milestone:** Phase 1 Technical Specs
