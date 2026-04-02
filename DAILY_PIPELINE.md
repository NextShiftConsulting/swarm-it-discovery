# Daily Discovery Pipeline

Simple daily paper discovery with source-specific SWARM agents.

## Two Pipelines (Dev vs Prod)

| Pipeline | Location | S3 Path | When |
|----------|----------|---------|------|
| **Lambda (PROD)** | AWS | `content/reviews/` | Daily 6am UTC |
| **Local (DEV)** | Your machine | `content/reviews-dev/` | Manual |

**They don't conflict** - local runs go to `-dev/` by default.

## Quick Start

### 1. Run Locally (Dev Mode)

```bash
cd ~/github/swarm-it-discovery
./scripts/run_daily.sh
```

Results go to `content/reviews-dev/` (won't touch production).

### 2. Run with Options

```bash
# Preview only (no uploads)
./scripts/run_daily.sh --dry-run

# More papers
./scripts/run_daily.sh 100

# Look back 3 days
./scripts/run_daily.sh 50 3

# PRODUCTION MODE (same as Lambda) - use carefully!
./scripts/run_daily.sh --prod
```

### 3. Set Up Daily Cron

Add to your crontab (`crontab -e`):

```cron
# Run daily at 6am (adjust path to your installation)
0 6 * * * ~/github/swarm-it-discovery/scripts/run_daily.sh >> /tmp/discovery.log 2>&1
```

Or use launchd (Mac):

```bash
# Copy the plist
cp scripts/com.swarmit.discovery.plist ~/Library/LaunchAgents/

# Load it
launchctl load ~/Library/LaunchAgents/com.swarmit.discovery.plist

# Verify
launchctl list | grep swarmit
```

## What It Does

1. **Fetches papers** from 6 sources:
   - arXiv (ML/AI preprints)
   - PubMed (biomedical)
   - bioRxiv/medRxiv (life sciences)
   - Semantic Scholar (citations)
   - OpenAlex (comprehensive)

2. **Matches** against your research topics

3. **Analyzes** with source-specific SWARM agents:
   - ArXivAgent: Conference potential
   - PubMedAgent: Clinical relevance
   - BioRxivAgent: Computational biology
   - SemanticScholarAgent: Citation analysis
   - OpenAlexAgent: Cross-domain

4. **Uploads** to S3:
   - Posts → `s3://swarmit-nextshift-site/content/reviews/`
   - Reports → `s3://swarmit-nextshift-site/analytics/daily/`

## Full Pipeline (Fetch → Analyze → Website)

To run everything and update the website:

```bash
# Full pipeline: fetch papers → analyze → S3 → git → website rebuild
./scripts/full_pipeline.sh

# Dev mode (doesn't update website)
./scripts/full_pipeline.sh --dev

# Preview only
./scripts/full_pipeline.sh --dry-run
```

## Individual Steps

```bash
# Step 1: Fetch and analyze only (uploads to S3)
./scripts/run_daily.sh

# Step 2: Sync S3 to git (triggers website rebuild)
./scripts/sync_s3_to_git.sh
```

## Check Results

```bash
# List recent posts in S3
aws s3 ls s3://swarmit-nextshift-site/content/reviews/ | tail -10

# View today's analytics
aws s3 cp s3://swarmit-nextshift-site/analytics/daily/$(date +%Y-%m-%d).json - | python3 -m json.tool

# Check git for synced content
ls -la content/reviews/
```

## Troubleshooting

**"Permission denied"**
```bash
chmod +x scripts/run_daily.sh
```

**"Command not found: aws"**
```bash
brew install awscli
```

**"No module named openai"**
```bash
pip install openai httpx numpy
```

## Files

```
scripts/
├── run_daily.sh           # Main runner (use this!)
├── daily_discovery.py     # Python pipeline
└── com.swarmit.discovery.plist  # Mac launchd config

agents/
├── arxiv_agent.py         # arXiv specialist
├── pubmed_agent.py        # PubMed specialist
├── biorxiv_agent.py       # bioRxiv/medRxiv specialist
├── semantic_scholar_agent.py  # Citation specialist
├── openalex_agent.py      # OpenAlex specialist
└── orchestrator.py        # Coordinates all agents
```
