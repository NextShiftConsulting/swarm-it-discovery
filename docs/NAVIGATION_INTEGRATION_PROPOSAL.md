# Multi-Site Navigation Integration Proposal

**Document Version**: 1.0
**Date**: February 27, 2026
**Status**: Proposal / Awaiting Approval
**Author**: Development Team
**Repository**: nsc-swarmit (Swarm-It subdomain)
**Related**: nsc-main-gatsby (main site)

---

## Executive Summary

This proposal outlines the implementation of navigation for the Swarm-It Research Discovery subdomain (`swarmit.nextshiftconsulting.com`) and its integration with the main Next Shift Consulting website.

**Core Principle**: Each site maintains its own navigation structure. The main site provides a single link to this subdomain, and this subdomain provides a link back to the parent.

**Swarm-It Focus**: This document focuses on Phase 2 (Swarm-It navigation component) of the multi-site integration.

---

## Problem Statement

### Current State (This Site)

**Swarm-It (`swarmit.nextshiftconsulting.com`)**:
- ✅ Site exists and functions
- ✅ Has `review.tsx` template for paper reviews
- ❌ **No navigation component**
- ❌ **No header/branding**
- ❌ **No way to return to main site**
- ❌ Users land here and feel "lost"

### Issues

1. **No Context**: Users don't know this is part of Next Shift Consulting
2. **Dead End**: No way to navigate back to main site
3. **No Subnav**: Can't navigate between Reviews, Topics, etc.
4. **Branding Gap**: Doesn't feel connected to parent brand

---

## Proposed Solution

### Swarm-It Navigation Component

Create a minimal but complete navigation system that:
1. **Links back** to main site (← Next Shift Consulting)
2. **Shows branding** (Swarm-It logo/title)
3. **Provides subnav** (Home, Reviews, Topics)
4. **Maintains independence** (doesn't import main site's nav)

### Visual Design

```
┌────────────────────────────────────────────────────────────┐
│ ← Next Shift Consulting     [Swarm-It Logo]                │
│        ^                                                     │
│   Back link                 Home | Reviews | Topics         │
│                                  ^                           │
│                        This site's own subnav               │
└────────────────────────────────────────────────────────────┘
```

**Key Elements**:
- Back link (left)
- Branding (center-left)
- Local navigation (right)
- Responsive (mobile-friendly)

---

## Design Principles

### 1. Minimal but Complete
This site needs **just enough** navigation:
- Link back to parent ✅
- Site branding ✅
- Local pages (Reviews, Topics) ✅
- **NOT**: Copy main site's Services, Blog, Contact, etc. ❌

### 2. Independent Implementation
- Don't import components from `nsc-main-gatsby`
- Build our own navigation component
- Share design principles (colors, fonts) but not code

### 3. Clear Visual Hierarchy
```
[Back Link] | [Site Title] --------- [Local Nav]
   ↑              ↑                        ↑
  Most         Identity              Navigation
important                            within site
```

### 4. Mobile-First
- Hamburger menu for mobile
- Back link always visible
- Responsive breakpoints

---

## Technical Implementation

### Phase 2: Swarm-It Site (THIS REPO)

#### 2.1 Create Navigation Component

**File**: `site/src/components/Navigation.tsx`

```typescript
import React, { useState } from 'react';
import { Link } from 'gatsby';

interface NavigationProps {
  siteTitle?: string;
}

const Navigation: React.FC<NavigationProps> = ({
  siteTitle = 'Swarm-It Research Discovery'
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { label: 'Home', to: '/' },
    { label: 'Reviews', to: '/reviews' },
    { label: 'Topics', to: '/topics' },
  ];

  return (
    <header className="fixed w-full z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">

          {/* Left: Back link + Branding */}
          <div className="flex items-center gap-4 md:gap-6">
            {/* Back to parent site - ALWAYS VISIBLE */}
            <a
              href="https://nextshiftconsulting.com"
              className="text-xs md:text-sm text-gray-600 hover:text-blue-600 transition-colors flex items-center gap-1 whitespace-nowrap"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span className="hidden sm:inline">Next Shift Consulting</span>
              <span className="sm:hidden">Back</span>
            </a>

            {/* Divider */}
            <div className="hidden sm:block w-px h-6 bg-gray-300" />

            {/* Swarm-It branding */}
            <Link
              to="/"
              className="font-bold text-base md:text-lg text-gray-800 hover:text-blue-600 transition-colors"
            >
              {siteTitle}
            </Link>
          </div>

          {/* Right: Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            {navItems.map((item) => (
              <Link
                key={item.label}
                to={item.to}
                className="font-medium text-gray-700 hover:text-blue-600 transition-colors"
                activeClassName="text-blue-600 font-semibold"
              >
                {item.label}
              </Link>
            ))}
          </nav>

          {/* Mobile menu button */}
          <button
            className="md:hidden p-2 text-gray-600 hover:text-blue-600"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-200">
            <nav className="flex flex-col space-y-2">
              {navItems.map((item) => (
                <Link
                  key={item.label}
                  to={item.to}
                  className="px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-lg transition-colors"
                  activeClassName="bg-blue-50 text-blue-600 font-semibold"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};

export default Navigation;
```

#### 2.2 Create Layout Component

**File**: `site/src/components/Layout.tsx`

```typescript
import React from 'react';
import Navigation from './Navigation';
import Footer from './Footer';

interface LayoutProps {
  children: React.ReactNode;
  className?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, className = '' }) => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navigation />

      <main className={`flex-grow pt-16 ${className}`}>
        {children}
      </main>

      <Footer />
    </div>
  );
};

export default Layout;
```

#### 2.3 Create Footer Component

**File**: `site/src/components/Footer.tsx`

```typescript
import React from 'react';
import { Link } from 'gatsby';

const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-gray-200 mt-12 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid md:grid-cols-3 gap-8">

          {/* Column 1: About */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Swarm-It Discovery</h3>
            <p className="text-sm text-gray-600">
              AI-curated analysis of cutting-edge ML/AI research papers.
              Powered by Next Shift Consulting.
            </p>
          </div>

          {/* Column 2: Quick Links */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Quick Links</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/reviews" className="text-gray-600 hover:text-blue-600">
                  Paper Reviews
                </Link>
              </li>
              <li>
                <Link to="/topics" className="text-gray-600 hover:text-blue-600">
                  Research Topics
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Parent Site */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Next Shift Consulting</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="https://nextshiftconsulting.com"
                  className="text-gray-600 hover:text-blue-600"
                >
                  Main Website
                </a>
              </li>
              <li>
                <a
                  href="https://nextshiftconsulting.com/services"
                  className="text-gray-600 hover:text-blue-600"
                >
                  Our Services
                </a>
              </li>
              <li>
                <a
                  href="https://nextshiftconsulting.com/contact"
                  className="text-gray-600 hover:text-blue-600"
                >
                  Contact Us
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 pt-6 border-t border-gray-200 text-center text-sm text-gray-600">
          <p>
            Part of{' '}
            <a
              href="https://nextshiftconsulting.com"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Next Shift Consulting
            </a>
            {' '}&copy; {new Date().getFullYear()}
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
```

#### 2.4 Update Pages to Use Layout

**File**: `site/src/pages/index.tsx`

```typescript
import React from 'react';
import { graphql, PageProps } from 'gatsby';
import Layout from '../components/Layout';

const IndexPage: React.FC<PageProps> = () => {
  return (
    <Layout>
      <section className="max-w-7xl mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            AI Research Paper Discovery
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Automated analysis of cutting-edge ML/AI research papers.
            Certified by Swarm-It RSCT.
          </p>
        </div>

        {/* Recent Reviews */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Paper cards will go here */}
        </div>
      </section>
    </Layout>
  );
};

export default IndexPage;

export const Head = () => (
  <>
    <title>Swarm-It Research Discovery | Next Shift Consulting</title>
    <meta
      name="description"
      content="AI-curated analysis of cutting-edge ML/AI research papers"
    />
  </>
);
```

---

## What This Site Gets

### ✅ Components Created
1. **Navigation.tsx** - Header with back link and subnav
2. **Layout.tsx** - Page wrapper with nav + footer
3. **Footer.tsx** - Footer with links back to main site

### ✅ Features
- Back link to main site (always visible)
- Swarm-It branding
- Local navigation (Home, Reviews, Topics)
- Mobile-responsive menu
- Footer with parent site links

### ❌ What We DON'T Copy
- Main site's Services dropdown
- Main site's Blog navigation
- Main site's Contact/About links
- Complex mega menus

**Why?** We maintain independence per SITE_PRINCIPLES.md.

---

## Benefits for This Site

1. **User Orientation**: Users know where they are and how to get back
2. **Professional**: Complete navigation = professional appearance
3. **Independent**: Can evolve without touching main site
4. **Brand Connection**: Clear relationship with parent brand
5. **SEO**: Internal linking improves SEO

---

## Implementation Checklist

### Components
- [ ] Create `site/src/components/Navigation.tsx`
- [ ] Create `site/src/components/Layout.tsx`
- [ ] Create `site/src/components/Footer.tsx`
- [ ] Export from `site/src/components/index.ts`

### Pages
- [ ] Update `site/src/pages/index.tsx` to use Layout
- [ ] Update `site/src/pages/reviews.tsx` to use Layout
- [ ] Update `site/src/pages/topics.tsx` to use Layout
- [ ] Update `site/src/templates/review.tsx` to use Layout

### Styling
- [ ] Verify Tailwind classes work
- [ ] Test responsive breakpoints
- [ ] Test hover/active states
- [ ] Verify color consistency with brand

### Testing
- [ ] Desktop navigation works
- [ ] Mobile menu works
- [ ] Back link works
- [ ] Footer links work
- [ ] Active state highlights correct page
- [ ] Test in Chrome, Firefox, Safari, Edge

### Deployment
- [ ] Commit changes
- [ ] Push to GitHub
- [ ] Verify deployment to swarmit.nextshiftconsulting.com
- [ ] Test in production

---

## Testing Plan

### Functional Tests
1. **Back Link**: Click "← Next Shift Consulting" → navigates to main site
2. **Home Link**: Click "Swarm-It" logo → navigates to home
3. **Reviews Link**: Click "Reviews" → navigates to /reviews
4. **Topics Link**: Click "Topics" → navigates to /topics
5. **Active State**: Current page is highlighted
6. **Mobile Menu**: Hamburger opens/closes menu
7. **Footer Links**: All footer links work

### Visual Tests
1. **Desktop**: Nav looks good at 1920px, 1440px, 1024px
2. **Tablet**: Nav looks good at 768px
3. **Mobile**: Nav looks good at 375px, 320px
4. **Hover States**: Links change color on hover
5. **Active States**: Current page is visually distinct

### Cross-Browser
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

---

## Timeline

**Estimated Time**: 2-3 hours

### Hour 1: Component Creation
- [ ] Create Navigation.tsx (30 min)
- [ ] Create Layout.tsx (15 min)
- [ ] Create Footer.tsx (15 min)

### Hour 2: Integration
- [ ] Update all pages to use Layout (30 min)
- [ ] Update template to use Layout (15 min)
- [ ] Test locally (15 min)

### Hour 3: Testing & Deploy
- [ ] Browser testing (20 min)
- [ ] Mobile testing (20 min)
- [ ] Deploy and verify (20 min)

---

## Success Metrics

### Quantitative
- **Bounce Rate**: Should decrease (users can navigate back)
- **Return Visits**: Should increase (easier to return from main site)
- **Page Views**: Users can navigate between Reviews/Topics easily

### Qualitative
- **User Feedback**: "Easy to find my way back"
- **Brand Perception**: Feels connected to Next Shift Consulting
- **Developer Experience**: Easy to update navigation

---

## Related Documents

- [SITE_PRINCIPLES.md](../SITE_PRINCIPLES.md) - Why this is a separate repo
- [NAVIGATION_INTEGRATION_PROPOSAL.md](../../nsc-main-gatsby/docs/NAVIGATION_INTEGRATION_PROPOSAL.md) - Full multi-site proposal (main site perspective)
- [CLAUDE.md](../CLAUDE.md) - Development guidelines

---

## Approval & Sign-off

**Reviewed By**: _________________
**Approved By**: _________________
**Date**: _________________

**Approval Criteria**:
- [ ] Technical implementation is sound
- [ ] Maintains site independence (per SITE_PRINCIPLES.md)
- [ ] Timeline is realistic
- [ ] Testing plan is comprehensive
- [ ] Links back to main site properly

---

**Document Status**: Ready for Review
**Next Action**: Approval / Implementation
**Repository**: nsc-swarmit (this repo)
