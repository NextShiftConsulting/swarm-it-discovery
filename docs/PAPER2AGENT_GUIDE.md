# Paper2SwarmAgent Guide

Convert research papers into swarm-it agents automatically.

## Quick Start

```bash
# Activate environment
conda activate py31209

# Run the pipeline
python pipeline/run_with_bedrock.py --days 3 --min-score 0.30
```

## What It Does

```
┌─────────────────────────────────────────────────────────────┐
│                    DISCOVERY PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. FETCH      → arXiv, Semantic Scholar, PubMed, bioRxiv   │
│                                                              │
│  2. MATCH      → Bedrock Titan embeddings (real semantic)   │
│                  Matches against your 5 topic areas          │
│                                                              │
│  3. CERTIFY    → api.swarms.network (real R/S/N/kappa)      │
│                                                              │
│  4. CONVERT    → Papers with GitHub → swarm-it agents       │
│                                                              │
│  5. PUBLISH    → MDX reviews + PDF reports                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Commands

### Daily Discovery
```bash
python pipeline/run_with_bedrock.py --days 1 --min-score 0.35
```

### Weekly Deep Scan
```bash
python pipeline/run_with_bedrock.py --days 7 --max-papers 50 --min-score 0.25
```

### Dry Run (no output)
```bash
python pipeline/run_with_bedrock.py --days 1 --dry-run
```

### Skip PDFs (faster)
```bash
python pipeline/run_with_bedrock.py --days 1 --no-pdfs
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--days` | 1 | Days to look back |
| `--max-papers` | 50 | Max papers per source |
| `--min-score` | 0.5 | Topic similarity threshold (0-1) |
| `--min-rsct-score` | 0.3 | RSCT relevance threshold (0-1) |
| `--dry-run` | false | Preview without generating |
| `--no-pdfs` | false | Skip PDF generation |

## Output

### MDX Reviews
```
content/reviews/
├── 2026-03-06-paper-title.mdx     # Blog post format
└── ...
```

Each review includes:
- Title, authors, abstract
- RSCT certification (kappa, R, S, N)
- Matched topics
- arXiv/PDF links

### PDF Reviews (LaTeX)
```
content/pdf-reviews/
├── arxiv-2603.05498v1.tex
└── ...
```

### Converted Agents
```
content/research-agents/
├── paper2agent_arxiv_123_abc.json  # ADK-compatible
└── ...
```

## Topics

Edit `content/topics/topics.json` to customize:

```json
{
  "topics": [
    {
      "id": "rsct-core",
      "title": "RSCT Core Theory",
      "keywords": ["representation", "solver", "kappa", "certification"]
    },
    {
      "id": "multi-agent",
      "title": "Multi-Agent Systems",
      "keywords": ["swarm", "coordination", "distributed"]
    }
  ]
}
```

## Paper2SwarmAgent

Papers with GitHub URLs are automatically converted to agents:

```python
from pipeline.paper2agent import Paper2SwarmAgent, TopicConfig

config = TopicConfig.from_json("content/topics/topics.json")
converter = Paper2SwarmAgent(topics=config)

result = converter.convert(
    paper_id="arxiv:2401.12345",
    paper_title="Multi-Agent Coordination",
    github_url="https://github.com/author/repo",
)

if result.success:
    result.agent.save("agents/my_agent.json")
```

### Agent Output Format

```json
{
  "id": "paper2agent_arxiv_123_abc",
  "name": "Multi-Agent Coordination Agent",
  "tools": [
    {
      "name": "train_model",
      "description": "Train the coordination model",
      "parameters": {...}
    }
  ],
  "config": {
    "solver_type": "llm",
    "system_prompt": "You are a research assistant..."
  }
}
```

## Architecture

```
swarm-it-discovery/
├── pipeline/
│   ├── paper2agent/           # Paper → Agent conversion
│   │   ├── scanner.py         # Find tutorials in repos
│   │   ├── extractor.py       # Extract functions
│   │   ├── converter.py       # Generate agent JSON
│   │   └── orchestrator.py    # Full pipeline
│   │
│   ├── analyzer/
│   │   └── bedrock_matcher.py # Semantic matching
│   │
│   ├── scanner/               # Paper fetching
│   ├── publisher/             # MDX/PDF generation
│   └── run_with_bedrock.py    # Main entry point
│
├── content/
│   ├── topics/                # Research topics config
│   ├── reviews/               # Generated MDX posts
│   ├── pdf-reviews/           # Generated LaTeX
│   └── research-agents/       # Converted agents
│
└── docs/
    └── PAPER2AGENT_GUIDE.md   # This file
```

## Requirements

- Python 3.12+
- AWS credentials (Bedrock access)
- swarm-it-adk (for API client)

## Credentials

Create `keys/aws_credentials.sh`:
```bash
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1
```

## Integration with ADK

The Paper2SwarmAgent module is designed for extraction to swarm-it-adk:

```python
# Future: from swarm_it.paper2agent import Paper2SwarmAgent
from pipeline.paper2agent import Paper2SwarmAgent
```
