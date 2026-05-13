# Swarm-It Research Discovery

**Live at**: [swarmit.nextshiftconsulting.com](https://swarmit.nextshiftconsulting.com)

> **⚠️ STATUS: PAUSED** (as of 2026-03-24)
> Site deployment paused during weekend. The pipeline depends on swarm-it-api (api.swarms.network) which is currently not operational. Pipeline will resume once API dependency is restored.

Automated AI/ML paper discovery and analysis - the **dynamic research discovery tool** for [Next Shift Consulting](https://nextshiftconsulting.com).

## Overview

This is a **standalone subdomain** deployed on AWS (S3 + CloudFront) that serves as the dynamic part of Next Shift Consulting's web presence. It's architecturally separate from the main company site to:
- Isolate automated pipeline failures
- Enable independent daily deployment cadence
- Manage higher risk profile (ML pipeline, external APIs)

**What it does automatically**:
1. **Scans** arXiv and Semantic Scholar for new papers daily
2. **Matches** papers against curated research topics using semantic similarity
3. **Certifies** the analysis pipeline using Swarm-It RSCT
4. **Publishes** featured blog posts for high-relevance papers

**Infrastructure**: AWS S3 bucket (`swarmit-nextshift`) + CloudFront distribution, separate from main site deployment.

## Architecture

This repo is part of a **3-repo ecosystem**:

```
┌─────────────────────────────────────────────────────────────┐
│ swarm-it-adk         → Agent Development Kit (framework)    │
│ swarm-it-api         → RSCT API (api.swarms.network)        │
│ swarm-it-discovery   → THIS REPO (paper discovery site)     │
└─────────────────────────────────────────────────────────────┘
```

**Dependency chain**: `discovery pipeline → ADK (orchestrate) → API (certify)`

**Current Status**: Discovery pipeline paused. Dependency on swarm-it-api (RSCT certification) is blocking. API has deployment-ready code but is not operational in production. See README status banner above.

### This Repo Structure

```
swarm-it-discovery/
├── site/                  # Gatsby + TypeScript frontend
│   └── src/
│       ├── components/    # React components
│       ├── pages/         # Home, Reviews, Topics, About
│       └── templates/     # MDX review template
│
├── pipeline/              # Paper discovery pipeline (Python)
│   ├── scanner/           # Fetch papers (arXiv, bioRxiv, S2)
│   ├── analyzer/          # Match topics + RSCT scoring
│   ├── publisher/         # Generate MDX reviews
│   ├── run.py             # Legacy runner (procedural)
│   └── run_adk.py         # ADK-orchestrated runner (agents)
│
├── content/
│   ├── topics/            # Research topic definitions (JSON)
│   └── reviews/           # Auto-generated paper reviews (MDX)
│
├── docs/                  # Documentation
│   └── ARCHITECTURE.md    # Full 3-repo architecture guide
│
└── infra/                 # Prototype Terraform (NOT USED)
                           # Actual API infra in swarm-it-api repo
```

**📖 See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for complete multi-repo architecture.**

## Setup

### Prerequisites

- Node.js 18+
- Python 3.10+
- [Swarm-It ADK](https://github.com/nextshift/swarm-it-adk) (optional, for agent orchestration)

### Installation

```bash
# Site
cd site
npm install

# Pipeline
cd ../pipeline
pip install -r requirements.txt
```

### Configuration

Credentials are loaded via `swarm-it-auth` (P18). Source your credentials before running:

```bash
source ~/github/swarm-it-auth/keys/.env
```

The pipeline uses the ADK provider factory for LLM calls — provider is set via env vars, not hardcoded:

```bash
# LLM provider (openrouter | openai | anthropic | bedrock | mimo)
# Default: openrouter
LLM_PROVIDER=openrouter

# Model ID for the chosen provider (uses provider default if unset)
# Examples:
#   openrouter: moonshotai/kimi-k2.6, meta-llama/llama-3.1-8b-instruct:free
#   openai:     gpt-4o, gpt-4o-mini
#   anthropic:  claude-sonnet-4-6, claude-haiku-4-5-20251001
LLM_MODEL=

# Swarm-It API (defaults to production)
SWARMIT_URL=https://api.swarms.network

# Optional: More paper sources
SEMANTIC_SCHOLAR_API_KEY=...
```

Credentials for the chosen provider (e.g. `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`) are discovered automatically by `swarm-it-auth` — no direct key exports needed.

### Add Topics

Place your topic documents in `content/topics/`:

```bash
# As JSON (recommended)
content/topics/topics.json

# Or as text files
content/topics/representation_learning.txt
content/topics/multi_agent_systems.txt
```

## Usage

### Run Pipeline

**Option 1: Legacy (Procedural)**
```bash
# Full run
python pipeline/run.py

# Dry run (no post generation)
python pipeline/run.py --dry-run

# Custom options
python pipeline/run.py --days 7 --min-score 0.7
```

**Option 2: ADK-Orchestrated (Recommended if ADK installed)**
```bash
# Uses agent orchestration with same underlying functions
python pipeline/run_adk.py

# Automatically falls back to legacy if ADK not found
```

**When to use each**:
- **Legacy**: Simple, predictable, good for debugging
- **ADK**: Agent coordination, traceable logs, showcases ADK capabilities

### Develop Site

```bash
cd site
npm run develop    # http://localhost:8000
npm run build      # Production build
```

### Deploy

## Deployment Flows

### Site — swarmit.nextshiftconsulting.com

**Automatic (push to `main`)**: GitHub Actions (`.github/workflows/deploy.yml`) triggers on any push that touches `site/**`, `content/**`, or `pipeline/**`. It:
1. Runs `yarn install` + `yarn build` (Gatsby) on GitHub's Ubuntu runner — **no local build required**
2. Syncs `site/public/` to the S3 bucket (configured via GitHub Secret `S3_BUCKET`)
3. Invalidates the CloudFront distribution (configured via GitHub Secret `CLOUDFRONT_DIST_ID`)

**Manual trigger**: Go to Actions → Build and Deploy → Run workflow.

**GitHub Secrets required**:
- `AWS_ACCESS_KEY_ID` — IAM key for the production AWS account
- `AWS_SECRET_ACCESS_KEY` — IAM secret for the production AWS account
- `S3_BUCKET` — target S3 bucket name
- `CLOUDFRONT_DIST_ID` — CloudFront distribution ID

### DNS

- `swarmit.nextshiftconsulting.com` is a **Cloudflare CNAME** pointing to the CloudFront distribution domain
- DNS is managed in **Cloudflare** (not Route53 — Route53 zones are empty by design)
- SSL cert validated via Cloudflare CNAME (ACM DNS validation)

### Main Site — nextshiftconsulting.com

Separate repo, deployed to **Netlify**. Auto-deploys on push via Netlify's GitHub integration. Not managed here.

### Infrastructure

- **S3**: Static site bucket in us-east-1 with public read policy (no OAC/OAI required)
- **CloudFront**: Fronts the S3 bucket with HTTPS and the custom domain alias
- `infra/` contains Terraform for the API container infra (ECS/ECR), not the site

**Note**: This is a standalone deployment separate from the main Next Shift Consulting site. See [SITE_PRINCIPLES.md](SITE_PRINCIPLES.md) for architecture rationale.

## Certification

The pipeline uses Swarm-It RSCT to certify each stage:

| Stage | What's Certified | Gate |
|-------|-----------------|------|
| Scanner | Fetched paper list | Input quality |
| Analyzer | Match results | Analysis validity |
| Publisher | Generated posts | Output safety |

If any stage fails certification (kappa < threshold), the pipeline halts.

## Patent Notice

See [PATENT_NOTICE.md](PATENT_NOTICE.md).

## Security

- Pre-commit hooks prevent credential leaks
- All API keys via environment variables
- No secrets in repository

## License

Proprietary - Next Shift Consulting
