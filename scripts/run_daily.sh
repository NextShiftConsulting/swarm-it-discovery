#!/bin/bash
#
# Daily Discovery Pipeline Runner
#
# This script runs the complete daily discovery pipeline:
# 1. Fetches papers from 6 sources
# 2. Matches against research topics
# 3. Runs SWARM source agents
# 4. Uploads posts to S3
#
# Usage:
#   ./scripts/run_daily.sh              # Default: 50 papers, 1 day
#   ./scripts/run_daily.sh 100          # 100 papers
#   ./scripts/run_daily.sh 50 3         # 50 papers, 3 days back
#   ./scripts/run_daily.sh --dry-run    # Preview only
#
# For cron (daily at 6am):
#   0 6 * * * /path/to/swarm-it-discovery/scripts/run_daily.sh >> /var/log/discovery.log 2>&1
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Defaults
MAX_PAPERS="${1:-50}"
DAYS="${2:-1}"
DRY_RUN=""

# Check for dry-run flag
if [ "$1" = "--dry-run" ]; then
    DRY_RUN="--dry-run"
    MAX_PAPERS="${2:-50}"
    DAYS="${3:-1}"
fi

# Load AWS credentials
if [ -f ~/GitHub/yrsn/keys/set_aws_env.sh ]; then
    source ~/GitHub/yrsn/keys/set_aws_env.sh 2>/dev/null
fi

# Get OpenAI key from Secrets Manager if not set
if [ -z "$OPENAI_API_KEY" ]; then
    export OPENAI_API_KEY=$(aws secretsmanager get-secret-value \
        --secret-id swarmit/openai-api-key \
        --region us-east-1 \
        --query SecretString \
        --output text 2>/dev/null)
fi

# Configuration
export S3_BUCKET="${S3_BUCKET:-swarmit-nextshift-site}"
export SWARMIT_URL="${SWARMIT_URL:-https://api.swarms.network}"

echo "=============================================="
echo "  Daily Discovery Pipeline"
echo "  $(date)"
echo "=============================================="
echo ""
echo "Configuration:"
echo "  Max papers per source: $MAX_PAPERS"
echo "  Days to look back: $DAYS"
echo "  S3 bucket: $S3_BUCKET"
echo "  Dry run: ${DRY_RUN:-no}"
echo ""

cd "$ROOT_DIR"

# Activate conda if available
if [ -f ~/opt/anaconda3/etc/profile.d/conda.sh ]; then
    source ~/opt/anaconda3/etc/profile.d/conda.sh
    conda activate py31209 2>/dev/null || true
fi

# Run the pipeline
python3 scripts/daily_discovery.py \
    --max-papers "$MAX_PAPERS" \
    --days "$DAYS" \
    --topics-dir "$ROOT_DIR/content/topics" \
    --whitepaper "$ROOT_DIR/pipeline/rsct_whitepaper.pdf" \
    --s3-bucket "$S3_BUCKET" \
    $DRY_RUN

echo ""
echo "=============================================="
echo "  Pipeline complete: $(date)"
echo "=============================================="
