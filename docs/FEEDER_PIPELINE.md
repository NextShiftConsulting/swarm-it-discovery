# SWARM Discovery Feeder Pipeline

## Architecture Overview

The discovery pipeline aggregates ML/AI research papers from multiple sources, analyzes them, and publishes daily digests.

```
┌─────────────────────────────────────────────────────────────────┐
│                        FEEDER SOURCES                           │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   Academic      │    YouTube      │   X/Twitter     │ HuggingFace│
│  ScannerAgent   │  YouTubeAgent   │    XAgent       │ HFPapersAgent│
│                 │                 │                 │           │
│  • arXiv        │  • @code4AI     │  • @_akhaliq    │ Daily API │
│  • PubMed       │  • @YannicK     │  • @HuggingPapers│ 50 papers │
│  • BioRxiv      │  • @TwoMinPapers│  • @DrJimFan    │ No auth   │
│  • SemanticScholar│ • Research talks│ • @AnthropicAI │           │
│  • OpenAlex     │                 │  • @OpenAI      │           │
└────────┬────────┴────────┬────────┴────────┬────────┴─────┬─────┘
         │                 │                 │              │
         └─────────────────┴────────┬────────┴──────────────┘
                                    │
                                    ▼
                          ┌─────────────────┐
                          │  ArchiveAgent   │
                          │                 │
                          │ • Deduplication │
                          │ • Scoring       │
                          │ • Thresholds    │
                          └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │ PublisherAgent  │
                          │                 │
                          │ • Markdown gen  │
                          │ • Categories    │
                          │ • Daily digest  │
                          └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │    Output       │
                          │                 │
                          │ • data/archive/ │
                          │ • data/daily/   │
                          │ • data/reports/ │
                          └─────────────────┘
```

## Feeder Agents

### 1. Academic Sources (ScannerAgent)

Fetches papers from academic APIs using source-specific agents:

| Source | Agent | API | Rate Limit |
|--------|-------|-----|------------|
| arXiv | ArXivAgent | OAI-PMH | 3 req/s |
| PubMed | PubMedAgent | E-utilities | 3 req/s |
| BioRxiv | BioRxivAgent | REST API | 100/min |
| Semantic Scholar | SemanticScholarAgent | REST API | 100/5min |
| OpenAlex | OpenAlexAgent | REST API | 100K/day |

```python
from agents import ScannerAgent

scanner = ScannerAgent()
papers = scanner.fetch_papers(query="transformers", max_results=100)
```

### 2. YouTube (YouTubeAgent)

Extracts research papers mentioned in ML/AI video channels.

**Priority Channels:**
- @code4AI - Daily paper reviews
- @YannicKilcher - Deep dives
- @TwoMinutePapers - Research highlights
- @AlexaAI, @GoogleAI - Industry research

```python
from agents import YouTubeAgent

yt = YouTubeAgent()
result = yt.scan_channel("code4AI", days=1)
print(f"Found {len(result.arxiv_ids)} papers")
```

### 3. X/Twitter (XAgent)

Scans priority ML accounts for paper links and arXiv IDs.

**Priority Accounts:**
| Account | Level | Focus |
|---------|-------|-------|
| @_akhaliq | mandatory | Daily paper summaries |
| @HuggingPapers | high | HuggingFace papers |
| @DrJimFan | high | NVIDIA AI research |
| @AnthropicAI | high | Anthropic research |
| @OpenAI | high | OpenAI research |
| @GoogleDeepMind | high | DeepMind research |

```python
from agents import XAgent

x = XAgent()
result = x.scan_priority_accounts(days=1)
arxiv_ids = result.unique_arxiv_ids
```

**Authentication:**
Requires X API v2 Bearer Token in `SWARM_X_BEARER_TOKEN` environment variable.

### 4. HuggingFace (HuggingFacePapersAgent)

Direct access to HuggingFace's daily curated papers API.

**Features:**
- No authentication required
- ~50 papers/day
- Includes upvote counts
- Same feed as @_akhaliq

```python
from agents import HuggingFacePapersAgent

hf = HuggingFacePapersAgent()
result = hf.fetch_daily_papers()
print(f"Top paper: {result.papers[0].title} ({result.papers[0].upvotes} upvotes)")
```

## Processing Pipeline

### ArchiveAgent

Deduplicates and scores papers from all feeders:

```python
from agents import ArchiveAgent, ArchiveThresholds

archive = ArchiveAgent(
    thresholds=ArchiveThresholds(
        min_relevance=0.6,
        min_citations=0,
        max_age_days=7
    )
)

# Add papers from all sources
archive.add_papers(scanner_papers)
archive.add_papers(youtube_papers)
archive.add_papers(x_papers)
archive.add_papers(hf_papers)

# Get deduplicated, scored results
result = archive.process()
```

### PublisherAgent

Generates markdown reports:

```python
from agents import PublisherAgent

publisher = PublisherAgent(output_dir="data/daily")
result = publisher.publish_daily(
    papers=archive_result.papers,
    date="2026-03-15"
)
```

## Daily Pipeline Script

```bash
# Run full discovery pipeline
./scripts/run_daily.sh

# Or run individual components
python -m agents.huggingface_agent --output data/hf_papers.json
python -m agents.x_agent --priority --output data/x_papers.json
python -m agents.youtube_agent --channels code4AI YannicKilcher
```

## Data Output

```
data/
├── archive/           # Deduplicated paper archive
│   └── papers.json
├── daily/             # Daily markdown digests
│   └── 2026-03-15.md
├── reports/           # Analysis reports
│   └── weekly_summary.md
└── raw/               # Raw feeder outputs
    ├── hf_papers.json
    ├── x_papers.json
    └── youtube_papers.json
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| SWARM_X_BEARER_TOKEN | For XAgent | X API v2 Bearer Token |
| MIMO_KEY | For analysis | MiMo API key |

## Integration with swarm-it-auth

All agents use swarm-it-auth for credential management:

```python
from swarm_auth.adapters import MiMoClient, EnvCredentialAdapter

# MiMo for LLM analysis
mimo = MiMoClient()

# Environment credentials
creds = EnvCredentialAdapter(prefix="SWARM_")
token = creds.retrieve("X_BEARER_TOKEN")
```
