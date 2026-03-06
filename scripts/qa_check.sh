#!/bin/bash
#
# Standard QA Check for Swarm-It Website
# Run after deployments to verify site is working
#
# Usage:
#   ./scripts/qa_check.sh
#   ./scripts/qa_check.sh --verbose
#

set -e

SITE_URL="${SITE_URL:-https://swarmit.nextshiftconsulting.com}"
VERBOSE="${1:-}"

echo "=============================================="
echo "  Swarm-It QA Check"
echo "  $(date)"
echo "  URL: $SITE_URL"
echo "=============================================="
echo ""

PASS=0
FAIL=0

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

# Fetch main page
echo "[1/5] Checking main page loads..."
RESPONSE=$(curl -s -o /tmp/qa_page.html -w "%{http_code}" "$SITE_URL" 2>/dev/null)
check "Main page returns 200" "$([ "$RESPONSE" = "200" ] && echo true || echo false)"

# Check for content
echo "[2/5] Checking page has content..."
HAS_CONTENT=$(grep -c "Latest Reviews\|papers reviewed" /tmp/qa_page.html 2>/dev/null || echo "0")
check "Page contains review content" "$([ "$HAS_CONTENT" -gt 0 ] && echo true || echo false)"

# Check for React errors (look for actual error messages, not CSS/JS mentions)
echo "[3/5] Checking for React errors..."
HAS_ERRORS=$(grep -ci "Error boundary\|React error\|Uncaught Error\|Minified React error" /tmp/qa_page.html 2>/dev/null || true)
HAS_ERRORS="${HAS_ERRORS:-0}"
check "No React errors detected" "$([ "${HAS_ERRORS}" -eq 0 ] 2>/dev/null && echo true || echo false)"

# Check review pages are accessible
echo "[4/5] Checking review pages..."
# Get first review link from page
REVIEW_LINK=$(grep -o 'href="/reviews/[^"]*"' /tmp/qa_page.html 2>/dev/null | head -1 | sed 's/href="//;s/"$//')
if [ -n "$REVIEW_LINK" ]; then
    REVIEW_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$SITE_URL$REVIEW_LINK" 2>/dev/null)
    check "Review detail page loads (${REVIEW_LINK})" "$([ "$REVIEW_RESPONSE" = "200" ] && echo true || echo false)"
else
    echo "⚠️  SKIP: No review links found to test"
fi

# Check CloudFront cache
echo "[5/5] Checking CDN headers..."
CF_HEADER=$(curl -s -I "$SITE_URL" 2>/dev/null | grep -i "x-cache" | head -1)
if [ -n "$CF_HEADER" ]; then
    echo "   CDN: $CF_HEADER"
fi

# Summary
echo ""
echo "=============================================="
echo "  QA Summary: $PASS passed, $FAIL failed"
echo "=============================================="

if [ "$FAIL" -gt 0 ]; then
    echo "⚠️  Some checks failed. Review the issues above."
    exit 1
else
    echo "✅ All checks passed!"
    exit 0
fi
