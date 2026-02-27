# Multi-Repo Architecture

**Date**: February 27, 2026
**Status**: Production
**Ecosystem**: Swarm-It Platform

---

## Overview

The Swarm-It platform is built across **three separate repositories**, each with a distinct purpose and deployment model.

```
┌─────────────────────────────────────────────────────────────┐
│                    SWARM-IT ECOSYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. swarm-it-adk (Agent Development Kit)                    │
│     └─ Framework for building multi-agent systems           │
│     └─ Client library for API access                        │
│     └─ Location: ~/GitHub/swarm-it-adk                      │
│                                                              │
│  2. swarm-it-api (RSCT Certification API)                   │
│     └─ FastAPI backend service                              │
│     └─ Deployed: https://api.swarms.network                 │
│     └─ Infrastructure: ALB + ECS/Fargate                    │
│                                                              │
│  3. swarm-it-discovery (THIS REPO)                          │
│     └─ Research paper discovery site                        │
│     └─ Deployed: https://swarmit.nextshiftconsulting.com   │
│     └─ Infrastructure: S3 + CloudFront (GitHub Actions)     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Repository Details

### 1. swarm-it-adk

**Purpose**: Agent Development Kit (framework + primitives)

**Contains**:
- Agent orchestration primitives
- Multi-agent coordination patterns
- Swarm intelligence algorithms
- Python client library (`from swarm_it import SwarmIt`)
- SDK for building certified agent applications

**Used By**:
- This repo (swarm-it-discovery pipeline)
- Customer applications
- Internal tools

**Location**: `~/GitHub/swarm-it-adk`

**Installation**:
```bash
# Editable install (recommended for development)
pip install -e ~/GitHub/swarm-it-adk/clients/python

# Or use in-repo via sys.path (current approach)
sys.path.insert(0, os.path.expanduser("~/GitHub/swarm-it-adk/clients/python"))
```

---

### 2. swarm-it-api

**Purpose**: RSCT Certification API (backend service)

**Deployed At**: https://api.swarms.network

**Technology Stack**:
- FastAPI application (Python 3.11+)
- Infrastructure: AWS ALB + ECS Fargate (or Lambda)
- DNS: Cloudflare
- Monitoring: CloudWatch

**API Endpoints**:
- `GET /health` - Health check
- `POST /api/v1/certify` - RSCT certification
- `GET /api/v1/statistics` - Usage statistics
- `GET /docs` - Swagger UI documentation

**What It Does**:
- Receives content for certification
- Computes R/S/N decomposition (Relevance/Spurious/Noise)
- Returns κ-gate score (0-1 quality metric)
- Decision: EXECUTE, REPAIR, or REJECT

**Example Request**:
```python
import requests

response = requests.post("https://api.swarms.network/api/v1/certify", json={
    "prompt": "User input to certify"
})

cert = response.json()
# {
#   "kappa_gate": 0.92,
#   "R": 0.85, "S": 0.12, "N": 0.03,
#   "decision": "EXECUTE",
#   "allowed": true
# }
```

---

### 3. swarm-it-discovery (THIS REPO)

**Purpose**: Research paper discovery & reviews

**Deployed At**: https://swarmit.nextshiftconsulting.com

**Components**:

#### Frontend (Gatsby Site)
- `site/` - Gatsby 5 + React 18 + TypeScript
- Pages: Home, Reviews, Topics, About
- Displays: RSCT-certified papers with quality badges
- Dark mode support

#### Backend (Python Pipeline)
- `pipeline/` - Paper discovery and analysis
- Daily scans: arXiv, bioRxiv, Semantic Scholar
- Topic matching: Semantic similarity
- RSCT scoring: Certification via API
- MDX generation: Automated review writing

#### Content
- `content/reviews/` - Generated paper reviews (MDX)
- `content/topics/` - Research topic definitions (JSON)

**Infrastructure**:
- Hosting: AWS S3 + CloudFront
- DNS: Cloudflare
- Deployment: GitHub Actions (auto-deploys on push to `main`)
- S3 Bucket: `swarmit-nextshift-site`
- CloudFront Distribution: `E3DPB09HCVDU9L`

---

## Dependency Chain

### Information Flow
```
1. Pipeline scans papers (daily cron)
2. ADK orchestrates scanning/analysis/writing agents
3. API certifies each paper (R/S/N + κ-score)
4. Pipeline generates MDX reviews
5. GitHub Actions builds Gatsby site
6. Site deploys to S3 + CloudFront
```

### Code Dependencies
```
discovery pipeline → swarm-it-adk (orchestrate) → swarm-it-api (certify)
```

- **Discovery depends on ADK** (optional): For agent orchestration
- **Discovery depends on API** (required): For RSCT certification
- **ADK depends on API**: Client library talks to certification endpoint

---

## What `infra/` Means in This Repo

⚠️ **Important**: The `infra/` directory in this repo contains **prototype Terraform code** that was used for early planning.

**Actual production infrastructure is deployed from the `swarm-it-api` repository.**

### Why This Exists
- Early exploration of multi-site architecture
- Planning CloudFront + API Gateway integration
- Landing page prototype (`landing/`)

### Why It's Not Used
- API is deployed from `swarm-it-api` repo (not here)
- No `terraform.tfstate` file exists in this repo
- Actual infrastructure is ALB-based (not API Gateway as prototype defined)

### Should You Deploy This?
**No.** Keep it for reference, but don't run `terraform apply`.

The production API infrastructure is managed in `swarm-it-api`.

---

## Running the Pipeline

### Option 1: Legacy (Procedural)
Direct Python execution without ADK orchestration:

```bash
cd pipeline
python run.py --days 7 --min-score 0.5 --min-rsct-score 0.3
```

**Use When**:
- ADK not installed
- Debugging pipeline issues
- Simple, predictable execution

### Option 2: ADK-Orchestrated (Recommended)
Uses Swarm-It ADK for agent coordination:

```bash
cd pipeline
python run_adk.py
```

**Use When**:
- ADK installed and stable
- Want traceable agent logs
- Showcasing ADK capabilities
- Need parallel execution

**Fallback**: If ADK not found, automatically falls back to legacy runner.

---

## Deployment Models

### Discovery Site (This Repo)
**Method**: GitHub Actions (automatic)

**Trigger**: Push to `main` branch

**Steps**:
1. Checkout code
2. Install dependencies (`yarn install`)
3. Copy content (`content/reviews/` → `site/content/reviews/`)
4. Build Gatsby site (`yarn build`)
5. Deploy to S3 (`aws s3 sync`)
6. Invalidate CloudFront cache

**Workflow**: `.github/workflows/deploy.yml`

### API (swarm-it-api repo)
**Method**: Manual or CI/CD (varies)

**Infrastructure**: Managed in separate repo

---

## Environment Variables

### Required
```bash
OPENAI_API_KEY=sk-...           # For LLM-powered analysis
```

### Optional
```bash
SWARMIT_URL=https://api.swarms.network  # Defaults to production
SEMANTIC_SCHOLAR_API_KEY=...            # For additional paper sources
```

### GitHub Secrets (for deployment)
```bash
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

---

## Cross-Repo Coordination

### When to Update Each Repo

**Update `swarm-it-adk`**:
- ADK framework improvements
- New agent primitives
- API client bug fixes

**Update `swarm-it-api`**:
- RSCT algorithm improvements
- API endpoint changes
- Infrastructure scaling

**Update `swarm-it-discovery` (this repo)**:
- New pages or features
- Pipeline improvements
- Content updates (topics, generated reviews)

### Breaking Changes

If `swarm-it-api` changes its API contract:
1. Update ADK client library first
2. Update discovery pipeline second
3. Coordinate deployment timing

---

## Security & Credentials

### What Goes Where

**Never Commit**:
- API keys (OpenAI, AWS, etc.)
- `.env` files
- `terraform.tfvars`
- `/keys/` directory contents

**Safe to Commit**:
- API URLs (production endpoints are public)
- Infrastructure code (Terraform)
- Documentation
- Generated content (papers are public)

### Credential Storage

- **Local Dev**: `.env` files (gitignored)
- **GitHub Actions**: Repository secrets
- **AWS Lambda**: Environment variables or Secrets Manager

---

## Monitoring & Observability

### Discovery Site
- **Logs**: CloudWatch Logs (via Lambda/build process)
- **Errors**: GitHub Actions build failures
- **Metrics**: CloudFront analytics

### API (swarm-it-api)
- **Logs**: CloudWatch Logs
- **Metrics**: API Gateway/ALB metrics
- **Alerts**: CloudWatch Alarms (managed in swarm-it-api repo)

### Pipeline
- **Logs**: Printed to stdout (captured in GitHub Actions)
- **Errors**: Pipeline summary JSON
- **Metrics**: Papers fetched/matched/published counts

---

## Future Improvements

### Short-Term
- [ ] Migrate to `pip install` for ADK (remove sys.path hack)
- [ ] Add structured logging to pipeline
- [ ] Implement retry logic for API failures
- [ ] Add CloudWatch alarms for pipeline failures

### Medium-Term
- [ ] Full autonomous agent behaviors (ADK Phase 2)
- [ ] Multi-agent coordination for paper selection
- [ ] Real-time updates (SSE from API)
- [ ] Search functionality (Fuse.js integration)

### Long-Term
- [ ] Monorepo consideration (if repos become tightly coupled)
- [ ] Shared infrastructure module (if patterns emerge)
- [ ] Unified deployment pipeline

---

## Related Documents

- [SITE_PRINCIPLES.md](../SITE_PRINCIPLES.md) - Why separate from nsc-main-gatsby
- [NAVIGATION_INTEGRATION_PROPOSAL.md](NAVIGATION_INTEGRATION_PROPOSAL.md) - Multi-site nav
- [SWARM_ANALYSIS_FIXES.md](SWARM_ANALYSIS_FIXES.md) - 10-agent analysis results
- [CLAUDE.md](../CLAUDE.md) - Development guidelines

---

## Questions & Support

**For ADK issues**: See `swarm-it-adk` repository
**For API issues**: See `swarm-it-api` repository
**For discovery site issues**: This repository

---

**Document Status**: Current
**Last Updated**: February 27, 2026
**Owner**: Development Team
