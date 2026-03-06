#!/bin/bash
#
# Standard QA Check for Swarm-It Website
# Run before/after deployments to verify code quality and site health
#
# Usage:
#   ./scripts/qa_check.sh              # Post-deploy checks only
#   ./scripts/qa_check.sh --preflight  # Pre-deploy code quality checks
#   ./scripts/qa_check.sh --full       # Both preflight + post-deploy
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SITE_DIR="$ROOT_DIR/site"

SITE_URL="${SITE_URL:-https://swarmit.nextshiftconsulting.com}"
MODE="${1:-postdeploy}"

echo "=============================================="
echo "  Swarm-It QA Check"
echo "  $(date)"
echo "  Mode: $MODE"
echo "=============================================="
echo ""

PASS=0
FAIL=0
WARN=0

check() {
    local name="$1"
    local result="$2"
    if [ "$result" = "true" ]; then
        echo "✅ PASS: $name"
        PASS=$((PASS + 1))
    else
        echo "❌ FAIL: $name"
        FAIL=$((FAIL + 1))
    fi
}

warn() {
    local name="$1"
    echo "⚠️  WARN: $name"
    WARN=$((WARN + 1))
}

# ============================================
# PRE-FLIGHT CODE QUALITY CHECKS
# ============================================
run_preflight() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  PRE-FLIGHT CODE QUALITY CHECKS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    cd "$SITE_DIR"

    # TypeScript check
    echo "[P1] TypeScript type checking..."
    if yarn typecheck 2>/dev/null; then
        check "TypeScript compiles without errors" "true"
    else
        check "TypeScript compiles without errors" "false"
    fi

    # ESLint check
    echo "[P2] ESLint code quality..."
    if yarn lint 2>/dev/null; then
        check "ESLint passes (no errors/warnings)" "true"
    else
        # Check if it's just warnings
        LINT_EXIT=$?
        if [ "$LINT_EXIT" -eq 1 ]; then
            warn "ESLint has warnings (review recommended)"
        else
            check "ESLint passes" "false"
        fi
    fi

    # Build check
    echo "[P3] Gatsby build test..."
    if yarn build 2>/dev/null; then
        check "Gatsby builds successfully" "true"
    else
        check "Gatsby builds successfully" "false"
    fi

    # MDX frontmatter validation
    echo "[P4] MDX frontmatter validation..."
    INVALID_MDX=$(find "$ROOT_DIR/content/reviews" -name "*.mdx" -exec grep -L "^kappa:" {} \; 2>/dev/null | wc -l | tr -d ' ')
    if [ "$INVALID_MDX" -eq 0 ]; then
        check "All MDX files have valid frontmatter" "true"
    else
        warn "$INVALID_MDX MDX files may have incomplete frontmatter"
    fi

    cd "$ROOT_DIR"
    echo ""
}

# ============================================
# POST-DEPLOY SITE HEALTH CHECKS
# ============================================
run_postdeploy() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  POST-DEPLOY SITE HEALTH CHECKS"
    echo "  URL: $SITE_URL"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Fetch main page
    echo "[D1] Checking main page loads..."
    RESPONSE=$(curl -s -o /tmp/qa_page.html -w "%{http_code}" "$SITE_URL" 2>/dev/null)
    check "Main page returns 200" "$([ "$RESPONSE" = "200" ] && echo true || echo false)"

    # Check for content
    echo "[D2] Checking page has content..."
    HAS_CONTENT=$(grep -c "Latest Reviews\|papers reviewed" /tmp/qa_page.html 2>/dev/null || echo "0")
    check "Page contains review content" "$([ "$HAS_CONTENT" -gt 0 ] && echo true || echo false)"

    # Check for React errors
    echo "[D3] Checking for React errors..."
    HAS_ERRORS=$(grep -ci "Error boundary\|React error\|Uncaught Error\|Minified React error" /tmp/qa_page.html 2>/dev/null || true)
    HAS_ERRORS="${HAS_ERRORS:-0}"
    check "No React errors detected" "$([ "${HAS_ERRORS}" -eq 0 ] 2>/dev/null && echo true || echo false)"

    # Check review pages are accessible
    echo "[D4] Checking review pages..."
    REVIEW_LINK=$(grep -o 'href="/reviews/[^"]*"' /tmp/qa_page.html 2>/dev/null | head -1 | sed 's/href="//;s/"$//')
    if [ -n "$REVIEW_LINK" ]; then
        REVIEW_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$SITE_URL$REVIEW_LINK" 2>/dev/null)
        check "Review detail page loads (${REVIEW_LINK})" "$([ "$REVIEW_RESPONSE" = "200" ] && echo true || echo false)"
    else
        warn "No review links found to test"
    fi

    # Check CloudFront cache
    echo "[D5] Checking CDN headers..."
    CF_HEADER=$(curl -s -I "$SITE_URL" 2>/dev/null | grep -i "x-cache" | head -1)
    if [ -n "$CF_HEADER" ]; then
        echo "   CDN: $CF_HEADER"
    fi

    echo ""
}

# ============================================
# MAIN EXECUTION
# ============================================

case "$MODE" in
    --preflight|-p)
        run_preflight
        ;;
    --full|-f)
        run_preflight
        run_postdeploy
        ;;
    --postdeploy|*)
        run_postdeploy
        ;;
esac

# Summary
echo "=============================================="
echo "  QA Summary: $PASS passed, $FAIL failed, $WARN warnings"
echo "=============================================="

if [ "$FAIL" -gt 0 ]; then
    echo "❌ Some checks failed. Review the issues above."
    exit 1
elif [ "$WARN" -gt 0 ]; then
    echo "⚠️  Passed with warnings. Review recommended."
    exit 0
else
    echo "✅ All checks passed!"
    exit 0
fi
