# Site Architecture Principles

## Repository Structure

This repository (`nsc-swarmit`) is the **Swarm-It Research Discovery Tool** - a subdomain of Next Shift Consulting.

### Related Repositories

- **nsc-swarmit** (`swarmit.nextshiftconsulting.com`) - THIS REPO
  - Research paper discovery tool (subdomain)
  - Automated pipeline with APIs
  - Scheduled deployments (automated)
  - Higher risk of errors (ML pipeline, external APIs)

- **nsc-main-gatsby** (`nextshiftconsulting.com`) - SEPARATE REPO
  - Main company website
  - Services, blog, contact, about pages
  - Manual deployments (on-demand)
  - Stable, production-critical

## Why Separate Repositories?

### 1. Fault Isolation
**This site** has automated pipelines, external API dependencies, and ML processing that can fail.

**Solution**: Separate repo means **our errors don't break the main company site**.

### 2. Different Deployment Cadence
- **This site**: Automated, scheduled deployments (daily paper ingestion)
- **Main site**: Manual, controlled deployments for company updates

### 3. Higher Risk Profile
This site includes:
- External API dependencies (arXiv, Semantic Scholar, OpenAI)
- ML pipeline (embeddings, similarity matching)
- Automated content generation
- Real-time data processing

**All of these can fail** - we don't want to risk the main site.

### 4. Independent Infrastructure
- **This site**: AWS S3 + CloudFront (automated deployment)
- **Main site**: Netlify (manual deployment)

## This Site's Purpose

### What We Do
- Automatically scan arXiv and Semantic Scholar for new papers
- Match papers against curated research topics using semantic similarity
- Generate MDX review pages for high-relevance papers
- Provide research discovery interface

### What We Don't Do
- ❌ Not a blog (that's on the main site)
- ❌ Not for company services/contact (that's on the main site)
- ❌ Not for general content (focused on research papers only)

## Relationship to Main Site

### Architecture
```
nextshiftconsulting.com (Main Site)
    ↓
    Links to →  swarmit.nextshiftconsulting.com (THIS SITE)
                    ↓
                    Links back ← Main Site
```

### Design Consistency

**SHARED** (Design Principles):
- Brand colors (blue-600, amber-600, gray palette)
- Typography (Poppins headings, system font body)
- Core design tokens (spacing, border radius)
- Logo and branding assets

**NOT SHARED** (Components/Templates):
- We have **1 template**: `review.tsx` (for paper reviews)
- We do NOT copy blog-post, contact, services templates from main site
- We have minimal navigation (just links to Reviews, Topics, Main Site)

### This is intentional:
- Simpler = less to break
- Focused = paper reviews only
- Minimal = faster builds

## Content Strategy

### This Site (Automated)
- **Paper reviews** - ML-generated from pipeline
- **Topic pages** - Curated research areas
- **Discovery interface** - Search and browse papers
- Dynamic, pipeline-generated content

### Main Site (Manual)
- Company services and value proposition
- General blog posts (thought leadership)
- Static, curated content

## Deployment Strategy

### This Site (Automated)
```bash
# Scheduled pipeline runs daily
python pipeline/run.py  # Generates new paper reviews
cd site
npm run build
./scripts/deploy.sh     # Auto-deploys to AWS S3/CloudFront
```

**Triggered by**:
- Scheduled cron job (daily)
- GitHub Actions workflow
- Manual pipeline run

### Main Site (Manual)
```bash
# On-demand deployments only
cd nsc-main-gatsby
yarn build
# Push to trigger Netlify deploy
```

## Error Handling Philosophy

**This Site**:
- Graceful degradation (show cached content if pipeline fails)
- Error monitoring and alerts
- Can be temporarily unavailable without affecting main site
- Pipeline failures are logged but don't crash the site

**Main Site**:
- Zero tolerance for downtime
- Must always be accessible
- Our issues don't affect it (that's the point!)

## Technical Stack

### Frontend (Gatsby + TypeScript)
```
site/
├── src/
│   ├── components/    # Minimal, purpose-built
│   ├── templates/     # ONLY review.tsx
│   └── pages/         # Index, reviews list, topics
└── content/
    └── reviews/       # Auto-generated MDX files
```

### Backend (Python Pipeline)
```
pipeline/
├── scanner/           # Fetch papers (arXiv, S2)
├── analyzer/          # Match against topics
├── publisher/         # Generate MDX files
└── certifier/         # RSCT quality gates
```

### Infrastructure
- **Hosting**: AWS S3 + CloudFront
- **DNS**: Subdomain of nextshiftconsulting.com
- **CI/CD**: GitHub Actions (scheduled)

## Navigation

### This Site's Header
- Minimal navigation
- "← Back to Next Shift Consulting" (links to main site)
- Internal links: Reviews, Topics
- No dropdown menus, no complex nav

### Main Site Links Here
- Main site has "Research" → "Swarm-It Discovery" dropdown
- External link to this subdomain

## Templates & Components

**What We Have:**
- ✅ 1 template: `review.tsx` (paper reviews)
- ✅ Minimal navigation component
- ✅ Basic layout wrapper
- ✅ Research-specific components (paper card, topic badge, etc.)

**What We DON'T Have (intentionally):**
- ❌ Blog post template (use main site)
- ❌ Contact form (use main site)
- ❌ Service pages (use main site)
- ❌ About/Privacy/Terms (use main site)
- ❌ Complex navigation (keep it simple)

**Why?** Less complexity = less to break = more reliable.

## When to Consolidate?

**DO NOT** merge with main repo unless:
1. This site becomes stable enough to not risk main site
2. Deployment cadences align (both become manual or both automated)
3. The business value of consolidation outweighs the risk

For now: **KEEP SEPARATE**.

## Security & Compliance

Same patterns as main site:
- `.githooks/` - Pre-commit security checks
- `CLAUDE.md` - AI coding instructions (no attribution)
- `PATENT_NOTICE.md` - Patent-pending technology notice
- `/keys/` - Gitignored credentials directory
- No credentials in code
- All API keys via environment variables

## Summary

✅ **Subdomain with focused purpose (research discovery)**
✅ **Automated deployments (daily paper ingestion)**
✅ **Higher error risk = isolated from main site**
✅ **Minimal templates (just review.tsx)**
✅ **Share design principles, not components**
✅ **Links back to main site for everything else**

This is an **architectural decision**, not a temporary state.

**Our errors stay here. The main site stays up.**
