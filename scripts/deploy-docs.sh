#!/bin/bash
# Deploy documentation to S3
# This script should be run as part of the release process

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCS_DIR="$PROJECT_ROOT/docs"

# Get version from argument or package
VERSION="${1:-}"
if [ -z "$VERSION" ]; then
    echo "ERROR: Version must be provided as first argument"
    echo "Usage: $0 <version> [s3-bucket] [cloudfront-distribution-id]"
    echo "Example: $0 3.0.0 docs-bucket E1234567890ABC"
    exit 1
fi

S3_BUCKET="${2:-da-vinci-docs}"
CLOUDFRONT_ID="${3:-}"

echo "Deploying documentation version $VERSION to S3..."
echo "S3 Bucket: $S3_BUCKET"

# Build documentation
echo "Building documentation..."
"$SCRIPT_DIR/build-docs.sh"

# Deploy to S3
echo "Deploying to S3..."
aws s3 sync "$DOCS_DIR/_build/html/" "s3://$S3_BUCKET/v$VERSION/" \
    --delete \
    --cache-control "public, max-age=3600"

# Also deploy as "latest"
echo "Updating 'latest' version..."
aws s3 sync "$DOCS_DIR/_build/html/" "s3://$S3_BUCKET/latest/" \
    --delete \
    --cache-control "public, max-age=300"

# Create version redirect for root
echo "Creating version index..."
cat > /tmp/versions.json <<EOF
{
  "current": "$VERSION",
  "versions": [
    {"version": "$VERSION", "path": "/v$VERSION/"},
    {"version": "latest", "path": "/latest/"}
  ]
}
EOF

aws s3 cp /tmp/versions.json "s3://$S3_BUCKET/versions.json" \
    --content-type "application/json" \
    --cache-control "public, max-age=60"

# Invalidate CloudFront cache if distribution ID provided
if [ -n "$CLOUDFRONT_ID" ]; then
    echo "Invalidating CloudFront cache..."
    aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_ID" \
        --paths "/v$VERSION/*" "/latest/*" "/versions.json"
fi

echo ""
echo "Documentation deployed successfully!"
echo "Version: $VERSION"
echo "S3 Location: s3://$S3_BUCKET/v$VERSION/"
echo ""
if [ -n "$CLOUDFRONT_ID" ]; then
    echo "CloudFront distribution invalidation initiated"
else
    echo "Note: No CloudFront distribution ID provided, cache not invalidated"
fi
