#!/bin/bash
#
# Sync S3 content to Git repo (triggers website rebuild)
#
# Flow:
#   Lambda → S3 (raw MDX)
#   This script → S3 to Git → GitHub Actions → Website
#
# Usage:
#   ./scripts/sync_s3_to_git.sh           # Sync production
#   ./scripts/sync_s3_to_git.sh --dev     # Sync dev content
#   ./scripts/sync_s3_to_git.sh --dry-run # Preview only
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
S3_BUCKET="swarmit-nextshift-site"
S3_PREFIX="content/reviews"
LOCAL_DIR="$ROOT_DIR/content/reviews"
DRY_RUN=""
MODE="prod"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="--dryrun"
            shift
            ;;
        --dev)
            MODE="dev"
            S3_PREFIX="content/reviews-dev"
            LOCAL_DIR="$ROOT_DIR/content/reviews-dev"
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

echo "=============================================="
echo "  S3 → Git Sync"
echo "  $(date)"
echo "=============================================="
echo ""
echo "Mode: $MODE"
echo "S3 Source: s3://$S3_BUCKET/$S3_PREFIX/"
echo "Local Dir: $LOCAL_DIR"
echo "Dry run: ${DRY_RUN:-no}"
echo ""

# Create local directory if needed
mkdir -p "$LOCAL_DIR"

# Sync from S3 to local
echo "[1/3] Syncing from S3..."
aws s3 sync "s3://$S3_BUCKET/$S3_PREFIX/" "$LOCAL_DIR/" \
    --region us-east-1 \
    $DRY_RUN

# Count files
FILE_COUNT=$(find "$LOCAL_DIR" -name "*.mdx" 2>/dev/null | wc -l | tr -d ' ')
echo "  Found $FILE_COUNT MDX files"

if [ -n "$DRY_RUN" ]; then
    echo ""
    echo "[DRY RUN] Would sync these files to git:"
    find "$LOCAL_DIR" -name "*.mdx" -mmin -60 2>/dev/null | head -10
    exit 0
fi

# Check for changes
cd "$ROOT_DIR"
CHANGES=$(git status --porcelain "$LOCAL_DIR" 2>/dev/null | wc -l | tr -d ' ')

if [ "$CHANGES" -eq 0 ]; then
    echo ""
    echo "[2/3] No new content to commit"
    echo "  S3 and Git are in sync"
    exit 0
fi

echo ""
echo "[2/3] Committing $CHANGES changed files..."
git add "$LOCAL_DIR"

# Get list of new files for commit message
NEW_FILES=$(git diff --cached --name-only "$LOCAL_DIR" | head -5)
TODAY=$(date +%Y-%m-%d)

git commit -m "$(cat <<EOF
Sync paper reviews from S3 ($TODAY)

$CHANGES files synced from s3://$S3_BUCKET/$S3_PREFIX/

New/updated:
$NEW_FILES

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"

echo ""
echo "[3/3] Pushing to GitHub..."
git push

echo ""
echo "=============================================="
echo "  Sync complete!"
echo "  GitHub Actions will rebuild the site"
echo "=============================================="
