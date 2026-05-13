#!/bin/bash
# Run paper discovery pipeline
#
# Usage:
#   ./scripts/run-pipeline.sh           # Default: 10 papers, 1 day
#   ./scripts/run-pipeline.sh 20        # 20 papers
#   ./scripts/run-pipeline.sh 10 3      # 10 papers, 3 days back
#   ./scripts/run-pipeline.sh --dry-run # Preview only

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Defaults
MAX_PAPERS="${1:-10}"
DAYS="${2:-1}"

# Check for dry-run flag
if [ "$1" = "--dry-run" ]; then
    DRY_RUN="--dry-run"
    MAX_PAPERS="${2:-10}"
    DAYS="${3:-1}"
fi

# Load credentials via swarm-it-auth (P18)
# If running locally, source your credentials first:
#   source ~/github/swarm-it-auth/keys/.env
source ~/github/swarm-it-auth/keys/.env 2>/dev/null || true

# LLM provider configuration
# LLM_PROVIDER: openrouter | openai | anthropic | bedrock | mimo (default: openrouter)
# LLM_MODEL:    model ID for the chosen provider (default: provider default)
export LLM_PROVIDER="${LLM_PROVIDER:-openrouter}"
export LLM_MODEL="${LLM_MODEL:-}"

# Use live API
export SWARMIT_URL="https://api.swarms.network"

echo "=== Paper Discovery Pipeline ==="
echo "API: $SWARMIT_URL"
echo "LLM provider: $LLM_PROVIDER${LLM_MODEL:+ ($LLM_MODEL)}"
echo "Max papers: $MAX_PAPERS"
echo "Days back: $DAYS"
echo ""

cd "$ROOT_DIR"
python3 pipeline/run.py \
    --max-papers "$MAX_PAPERS" \
    --days "$DAYS" \
    --topics-dir site/src/content/topics \
    --output-dir site/src/content/reviews \
    $DRY_RUN

# Commit and push new posts (triggers GitHub Actions deploy)
if [ -z "$DRY_RUN" ]; then
    echo ""
    echo "=== Committing new posts ==="
    cd "$ROOT_DIR"

    # Check if there are new posts
    if git status --porcelain site/src/content/reviews/ | grep -q .; then
        git add site/src/content/reviews/
        git commit -m "Add paper reviews $(date +%Y-%m-%d)"
        git push
        echo "Pushed to GitHub - deploy will trigger automatically"
    else
        echo "No new posts to commit"
    fi
fi
