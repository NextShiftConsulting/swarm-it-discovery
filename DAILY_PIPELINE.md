# Daily Discovery Pipeline

Simple daily paper discovery with source-specific SWARM agents.

## Quick Start

### 1. Run Manually (Local)

```bash
cd /Users/rudy/GitHub/swarm-it-discovery
./scripts/run_daily.sh
```

That's it! The script handles:
- Loading AWS credentials
- Setting up OpenAI API key
- Running all 6 source agents
- Uploading posts to S3

### 2. Run with Options

```bash
# Preview only (no uploads)
./scripts/run_daily.sh --dry-run

# More papers
./scripts/run_daily.sh 100

# Look back 3 days
./scripts/run_daily.sh 50 3
```

### 3. Set Up Daily Cron

Add to your crontab (`crontab -e`):

```cron
# Run daily at 6am
0 6 * * * /Users/rudy/GitHub/swarm-it-discovery/scripts/run_daily.sh >> /tmp/discovery.log 2>&1
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

## Check Results

```bash
# List recent posts
aws s3 ls s3://swarmit-nextshift-site/content/reviews/ | tail -10

# View today's analytics
aws s3 cp s3://swarmit-nextshift-site/analytics/daily/$(date +%Y-%m-%d).json - | python3 -m json.tool
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
