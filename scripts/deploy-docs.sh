#!/bin/bash
# Deploy documentation to S3
# This script should be run as part of the release process

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCS_DIR="$PROJECT_ROOT/docs"

S3_BUCKET="${1:-da-vinci-docs}"
CLOUDFRONT_ID="${2:-}"

echo "Deploying documentation to S3..."
echo "S3 Bucket: $S3_BUCKET"

# Build documentation
echo "Building documentation..."
"$SCRIPT_DIR/build-docs.sh"

# Deploy to S3 root
echo "Deploying to S3..."
aws s3 sync "$DOCS_DIR/_build/html/" "s3://$S3_BUCKET/" \
    --delete \
    --cache-control "public, max-age=3600"

# Invalidate CloudFront cache if distribution ID provided
if [ -n "$CLOUDFRONT_ID" ]; then
    echo "Invalidating CloudFront cache..."
    aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_ID" \
        --paths "/*"
fi

echo ""
echo "Documentation deployed successfully!"
echo "S3 Location: s3://$S3_BUCKET/"
echo ""
if [ -n "$CLOUDFRONT_ID" ]; then
    echo "CloudFront distribution invalidation initiated"
else
    echo "Note: No CloudFront distribution ID provided, cache not invalidated"
fi
