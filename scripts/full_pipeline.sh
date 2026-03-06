#!/bin/bash
#
# Full Discovery Pipeline: Fetch → Analyze → S3 → Git → Website
#
# This runs the complete flow:
#   1. Fetch papers from 6 sources
#   2. Analyze with SWARM agents
#   3. Upload to S3
#   4. Sync S3 to Git
#   5. Push to GitHub (triggers site rebuild)
#
# Usage:
#   ./scripts/full_pipeline.sh           # Full pipeline (prod)
#   ./scripts/full_pipeline.sh --dev     # Dev mode (no site rebuild)
#   ./scripts/full_pipeline.sh --dry-run # Preview only
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

MODE="prod"
DRY_RUN=""
MAX_PAPERS="50"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --dev)
            MODE="dev"
            shift
            ;;
        [0-9]*)
            MAX_PAPERS="$1"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

echo "╔══════════════════════════════════════════════════════════╗"
echo "║           FULL DISCOVERY PIPELINE                        ║"
echo "║           $(date)                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Mode: $MODE"
echo "Papers: $MAX_PAPERS per source"
echo "Dry run: ${DRY_RUN:-no}"
echo ""

cd "$ROOT_DIR"

# Step 1: Run discovery pipeline
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1/2: Running discovery pipeline..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$MODE" = "dev" ]; then
    ./scripts/run_daily.sh $DRY_RUN $MAX_PAPERS
else
    ./scripts/run_daily.sh --prod $DRY_RUN $MAX_PAPERS
fi

if [ -n "$DRY_RUN" ]; then
    echo ""
    echo "[DRY RUN] Pipeline preview complete. No files uploaded."
    exit 0
fi

# Step 2: Sync to Git (triggers website rebuild)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2/2: Syncing to Git (triggers website rebuild)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$MODE" = "dev" ]; then
    ./scripts/sync_s3_to_git.sh --dev
    echo ""
    echo "📝 DEV MODE: Content synced to content/reviews-dev/"
    echo "   Website NOT rebuilt (dev content not published)"
else
    ./scripts/sync_s3_to_git.sh
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    PIPELINE COMPLETE                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
if [ "$MODE" = "prod" ]; then
    echo "✅ Posts uploaded to S3"
    echo "✅ Git repo updated"
    echo "✅ GitHub Actions triggered → Website rebuilding"
    echo ""
    echo "Check: https://swarmit.nextshiftconsulting.com"
else
    echo "✅ Dev posts uploaded to S3 (reviews-dev/)"
    echo "✅ Dev content synced to git"
    echo "ℹ️  Website NOT updated (dev mode)"
fi
