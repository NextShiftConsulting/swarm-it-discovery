#!/bin/bash
#
# Deploy Team - Monitor deployment and verify site is ready
#
# Usage:
#   ./scripts/deploy_check.sh              # Check latest deploy status
#   ./scripts/deploy_check.sh --wait       # Wait for deploy + run QA
#   ./scripts/deploy_check.sh --trigger    # Trigger new deploy + wait + QA
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
MODE="${1:-status}"

# GitHub settings
REPO="NextShiftConsulting/swarm-it-discovery"
SITE_URL="https://swarmit.nextshiftconsulting.com"

echo "=============================================="
echo "  Swarm-It Deploy Team"
echo "  $(date)"
echo "=============================================="
echo ""

# Check for gh CLI
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) not found. Install with: brew install gh"
    exit 1
fi

# Get latest run status
get_latest_run() {
    gh run list --repo "$REPO" --limit 1 --json status,conclusion,name,databaseId,createdAt 2>/dev/null
}

# Wait for run to complete
wait_for_deploy() {
    local run_id="$1"
    local max_wait=300  # 5 minutes
    local waited=0
    local interval=10

    echo "⏳ Waiting for deploy to complete (max ${max_wait}s)..."

    while [ $waited -lt $max_wait ]; do
        local status=$(gh run view "$run_id" --repo "$REPO" --json status -q '.status' 2>/dev/null)

        if [ "$status" = "completed" ]; then
            local conclusion=$(gh run view "$run_id" --repo "$REPO" --json conclusion -q '.conclusion' 2>/dev/null)
            echo ""
            if [ "$conclusion" = "success" ]; then
                echo "✅ Deploy completed successfully!"
                return 0
            else
                echo "❌ Deploy failed with conclusion: $conclusion"
                return 1
            fi
        fi

        printf "."
        sleep $interval
        waited=$((waited + interval))
    done

    echo ""
    echo "⚠️ Timeout waiting for deploy"
    return 1
}

# Run post-deploy QA
run_qa() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Running Post-Deploy QA..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Wait for CloudFront cache invalidation (usually ~30s)
    echo "⏳ Waiting 30s for CDN cache invalidation..."
    sleep 30

    "$SCRIPT_DIR/qa_check.sh"
    return $?
}

case "$MODE" in
    --status|-s|status)
        echo "[1/1] Checking latest deploy status..."
        LATEST=$(get_latest_run)

        if [ -z "$LATEST" ]; then
            echo "❌ Could not get deploy status. Check gh auth."
            exit 1
        fi

        STATUS=$(echo "$LATEST" | jq -r '.[0].status')
        CONCLUSION=$(echo "$LATEST" | jq -r '.[0].conclusion')
        NAME=$(echo "$LATEST" | jq -r '.[0].name')

        echo "Latest: $NAME"
        echo "Status: $STATUS"

        if [ "$STATUS" = "completed" ]; then
            if [ "$CONCLUSION" = "success" ]; then
                echo "Result: ✅ SUCCESS"
                echo ""
                echo "🌐 Site ready: $SITE_URL"
            else
                echo "Result: ❌ $CONCLUSION"
            fi
        else
            echo "Result: ⏳ In progress..."
        fi
        ;;

    --wait|-w)
        echo "[1/2] Getting latest deploy..."
        LATEST=$(get_latest_run)
        RUN_ID=$(echo "$LATEST" | jq -r '.[0].databaseId')
        STATUS=$(echo "$LATEST" | jq -r '.[0].status')

        if [ "$STATUS" = "completed" ]; then
            echo "Latest deploy already completed."
        else
            wait_for_deploy "$RUN_ID" || exit 1
        fi

        echo ""
        echo "[2/2] Running QA verification..."
        run_qa
        ;;

    --trigger|-t)
        echo "[1/3] Triggering new deploy..."
        gh workflow run "Build and Deploy" --repo "$REPO" 2>/dev/null

        if [ $? -ne 0 ]; then
            echo "❌ Failed to trigger workflow"
            exit 1
        fi

        echo "✅ Workflow triggered"
        sleep 5  # Wait for run to appear

        echo ""
        echo "[2/3] Waiting for deploy..."
        LATEST=$(get_latest_run)
        RUN_ID=$(echo "$LATEST" | jq -r '.[0].databaseId')
        wait_for_deploy "$RUN_ID" || exit 1

        echo ""
        echo "[3/3] Running QA verification..."
        run_qa
        ;;

    *)
        echo "Usage: $0 [--status|--wait|--trigger]"
        echo ""
        echo "  --status   Check latest deploy status (default)"
        echo "  --wait     Wait for current deploy + run QA"
        echo "  --trigger  Trigger new deploy + wait + run QA"
        exit 1
        ;;
esac

echo ""
echo "=============================================="
echo "  Deploy Team Complete"
echo "=============================================="
