# Swarm-It Research Discovery

Automated AI/ML paper discovery and analysis for [nextshiftconsulting.com](https://nextshiftconsulting.com).

## Overview

This system automatically:
1. **Scans** arXiv and Semantic Scholar for new papers daily
2. **Matches** papers against curated research topics using semantic similarity
3. **Certifies** the analysis pipeline using Swarm-It RSCT
4. **Publishes** featured blog posts for high-relevance papers

## Architecture

```
swarmit-site/
├── site/                  # Gatsby + TypeScript frontend
│   └── src/
│       ├── components/    # React components (matches nextshiftconsulting.com)
│       ├── pages/         # Site pages
│       └── styles/        # CSS
│
├── pipeline/              # Daily scanner (Python)
│   ├── scanner/           # Paper fetching (arXiv, S2)
│   ├── analyzer/          # Similarity matching
│   └── publisher/         # MDX generation
│
├── content/
│   ├── topics/            # Your curated topic PDFs/embeddings
│   └── reviews/           # Auto-generated paper reviews (.mdx)
│
└── infra/                 # AWS deployment (Lambda, S3, CloudFront)
```

## Setup

### Prerequisites

- Node.js 18+
- Python 3.10+
- [Swarm-It sidecar](https://github.com/nextshift/swarm-it) (optional, for certification)

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

```bash
# Full run
python pipeline/run.py

# Dry run (no post generation)
python pipeline/run.py --dry-run

# Custom options
python pipeline/run.py --days 7 --min-score 0.7
```

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
