#!/bin/bash
# Deploy Swarmit Site to AWS S3 + CloudFront
# Usage: ./scripts/deploy.sh [prod|staging]

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ENV=${1:-prod}
S3_BUCKET="swarmit-nextshift-site"
CLOUDFRONT_DIST_ID="${CLOUDFRONT_DISTRIBUTION_ID:-}"

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}Swarmit Site - AWS Deployment${NC}"
echo -e "${GREEN}======================================================================${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI not found${NC}"
    exit 1
fi

# Check AWS credentials
echo -e "\n${YELLOW}Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured. Run: aws configure${NC}"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS Account:${NC} $ACCOUNT_ID"

# Build site
echo -e "\n${YELLOW}Building site...${NC}"
cd "$(dirname "$0")/../site"

npm run clean
npm run build

echo -e "${GREEN}✓ Build complete${NC}"

# Sync to S3
echo -e "\n${YELLOW}Syncing to S3...${NC}"
aws s3 sync public/ "s3://${S3_BUCKET}" \
    --delete \
    --cache-control "max-age=31536000,public" \
    --exclude "*.html" \
    --exclude "page-data/*" \
    --exclude "chunk-map.json" \
    --exclude "webpack.stats.json"

# HTML files with shorter cache
aws s3 sync public/ "s3://${S3_BUCKET}" \
    --delete \
    --cache-control "max-age=0,no-cache,no-store,must-revalidate" \
    --include "*.html" \
    --include "page-data/*" \
    --content-type "text/html"

echo -e "${GREEN}✓ S3 sync complete${NC}"

# Invalidate CloudFront cache
if [ -n "$CLOUDFRONT_DIST_ID" ]; then
    echo -e "\n${YELLOW}Invalidating CloudFront cache...${NC}"
    aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_DIST_ID" \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text
    echo -e "${GREEN}✓ CloudFront invalidation started${NC}"
else
    echo -e "\n${YELLOW}No CLOUDFRONT_DISTRIBUTION_ID set, skipping invalidation${NC}"
fi

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}DEPLOYMENT SUCCESSFUL!${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo -e "\n${YELLOW}Site URL:${NC} https://swarmit.nextshiftconsulting.com"
echo -e "${GREEN}======================================================================${NC}"
