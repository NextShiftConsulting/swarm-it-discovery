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

# Load credentials
source ~/GitHub/yrsn/keys/set_aws_env.sh 2>/dev/null || true

# Get OpenAI key from Secrets Manager
if [ -z "$OPENAI_API_KEY" ]; then
    export OPENAI_API_KEY=$(aws secretsmanager get-secret-value \
        --secret-id swarmit/openai-api-key \
        --region us-east-1 \
        --query SecretString \
        --output text 2>/dev/null)
fi

# Use live API
export SWARMIT_URL="https://api.swarms.network"

echo "=== Paper Discovery Pipeline ==="
echo "API: $SWARMIT_URL"
echo "Max papers: $MAX_PAPERS"
echo "Days back: $DAYS"
echo ""

cd "$ROOT_DIR"
python3 pipeline/run.py \
    --max-papers "$MAX_PAPERS" \
    --days "$DAYS" \
    --topics-dir site/content/topics \
    --output-dir site/content/reviews \
    $DRY_RUN

# Commit and push new posts (triggers GitHub Actions deploy)
if [ -z "$DRY_RUN" ]; then
    echo ""
    echo "=== Committing new posts ==="
    cd "$ROOT_DIR"

    # Check if there are new posts
    if git status --porcelain site/content/reviews/ | grep -q .; then
        git add site/content/reviews/
        git commit -m "Add paper reviews $(date +%Y-%m-%d)"
        git push
        echo "Pushed to GitHub - deploy will trigger automatically"
    else
        echo "No new posts to commit"
    fi
fi
