#!/bin/bash
#
# Daily Discovery Pipeline Runner (LOCAL/DEV)
#
# This is the LOCAL development version. For production, use AWS Lambda.
#
# Usage:
#   ./scripts/run_daily.sh              # Dev mode (uploads to reviews-dev/)
#   ./scripts/run_daily.sh --prod       # Prod mode (uploads to reviews/) - USE WITH CAUTION
#   ./scripts/run_daily.sh --dry-run    # Preview only (no uploads)
#   ./scripts/run_daily.sh 100          # 100 papers (dev mode)
#   ./scripts/run_daily.sh 50 3         # 50 papers, 3 days back
#
# Coordination with Lambda:
#   - Lambda runs daily at 6am UTC → uploads to content/reviews/
#   - Local runs → uploads to content/reviews-dev/ (default)
#   - Use --prod flag to upload to production (same as Lambda)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Defaults
MAX_PAPERS="50"
DAYS="1"
DRY_RUN=""
MODE="dev"  # dev or prod
S3_PREFIX="content/reviews-dev"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --prod)
            MODE="prod"
            S3_PREFIX="content/reviews"
            echo "⚠️  PRODUCTION MODE - uploads to same location as Lambda"
            shift
            ;;
        --dev)
            MODE="dev"
            S3_PREFIX="content/reviews-dev"
            shift
            ;;
        [0-9]*)
            if [ -z "$FIRST_NUM" ]; then
                MAX_PAPERS="$1"
                FIRST_NUM="set"
            else
                DAYS="$1"
            fi
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Load AWS credentials
if [ -f ~/GitHub/yrsn/keys/set_aws_env.sh ]; then
    source ~/GitHub/yrsn/keys/set_aws_env.sh 2>/dev/null
fi

# Get OpenAI key from local file or Secrets Manager
if [ -z "$OPENAI_API_KEY" ]; then
    if [ -f ~/GitHub/yrsn/keys/OPENAI_API_KEY.txt ]; then
        # Local file format: OPENAI_API_KEY="sk-..."
        export OPENAI_API_KEY=$(grep -o 'sk-[^"]*' ~/GitHub/yrsn/keys/OPENAI_API_KEY.txt)
    else
        export OPENAI_API_KEY=$(aws secretsmanager get-secret-value \
            --secret-id swarmit/openai-api-key \
            --region us-east-1 \
            --query SecretString \
            --output text 2>/dev/null)
    fi
fi

# Configuration
export S3_BUCKET="${S3_BUCKET:-swarmit-nextshift-site}"
export SWARMIT_URL="${SWARMIT_URL:-https://api.swarms.network}"
export S3_PREFIX="$S3_PREFIX"

# Install ADK client if not present
pip install -q -e ~/GitHub/swarm-it-adk/clients/python 2>/dev/null || true

echo "=============================================="
echo "  Daily Discovery Pipeline (LOCAL)"
echo "  $(date)"
echo "=============================================="
echo ""
echo "Mode: $MODE"
echo "  Max papers: $MAX_PAPERS"
echo "  Days back: $DAYS"
echo "  S3 bucket: $S3_BUCKET"
echo "  S3 prefix: $S3_PREFIX"
echo "  Dry run: ${DRY_RUN:-no}"
echo ""
if [ "$MODE" = "dev" ]; then
    echo "📝 DEV MODE: Results go to $S3_PREFIX/"
    echo "   (Lambda production goes to content/reviews/)"
    echo ""
fi

cd "$ROOT_DIR"

# Activate conda if available
if [ -f ~/opt/anaconda3/etc/profile.d/conda.sh ]; then
    source ~/opt/anaconda3/etc/profile.d/conda.sh
    conda activate py31209 2>/dev/null || true
fi

# Run the ADK pipeline (uses Swarm-It API for real RSCT scoring)
python3 pipeline/run_adk.py \
    --max-papers "$MAX_PAPERS" \
    --days "$DAYS" \
    --min-score 0.2 \
    --min-rsct-score 0.1 \
    --topics-dir "$ROOT_DIR/site/src/content/topics" \
    --output-dir "$ROOT_DIR/site/src/content/reviews" \
    $DRY_RUN

echo ""
echo "=============================================="
echo "  Pipeline complete: $(date)"
echo "=============================================="
