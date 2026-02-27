# Swarm-It Research Discovery

Automated AI/ML paper discovery and analysis for [nextshiftconsulting.com](https://nextshiftconsulting.com).

## Overview

This system automatically:
1. **Scans** arXiv and Semantic Scholar for new papers daily
2. **Matches** papers against curated research topics using semantic similarity
3. **Certifies** the analysis pipeline using Swarm-It RSCT
4. **Publishes** featured blog posts for high-relevance papers

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

Create `.env` (never commit this):

```bash
# Required for LLM-powered analysis
OPENAI_API_KEY=sk-...

# Swarm-It API (defaults to production)
SWARMIT_URL=https://api.swarms.network

# Optional: More paper sources
SEMANTIC_SCHOLAR_API_KEY=...
```

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

```bash
# Build and deploy to AWS
npm run build
aws s3 sync public/ s3://swarmit-nextshift --delete
aws cloudfront create-invalidation --distribution-id XXXX --paths "/*"
```

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
