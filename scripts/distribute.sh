#!/usr/bin/env bash
#
# distribute.sh - Publish packages to S3 PyPI
#
# Usage:
#   ./scripts/distribute.sh --bucket <bucket-name>              # Distribute all
#   ./scripts/distribute.sh --bucket <bucket-name> --core       # Core only
#   ./scripts/distribute.sh --bucket <bucket-name> --cdk        # CDK only
#   ./scripts/distribute.sh --bucket <bucket-name> --dry-run    # Show what would be uploaded
#
# Environment Variables:
#   S3_PYPI_BUCKET - Default S3 bucket name (can be overridden with --bucket)
#   AWS_PROFILE    - AWS CLI profile to use
#   AWS_REGION     - AWS region (default: us-east-1)
#
# This script:
# 1. Validates built wheel files exist
# 2. Uploads wheels to S3 simple index structure
# 3. Generates/updates index.html for each package
# 4. Sets correct content-type headers
# 5. Verifies upload success
# 6. Prints installation instructions
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get bucket name from parameters.json if not set
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARAMETERS_FILE="$SCRIPT_DIR/../infrastructure/parameters.json"

if [ -f "$PARAMETERS_FILE" ]; then
    PROJECT_NAME=$(jq -r '.[] | select(.ParameterKey=="ProjectName") | .ParameterValue' "$PARAMETERS_FILE" 2>/dev/null || echo "")
    ENVIRONMENT=$(jq -r '.[] | select(.ParameterKey=="Environment") | .ParameterValue' "$PARAMETERS_FILE" 2>/dev/null || echo "production")
    DOMAIN_NAME=$(jq -r '.[] | select(.ParameterKey=="DomainName") | .ParameterValue' "$PARAMETERS_FILE" 2>/dev/null || echo "")
    if [ -n "$PROJECT_NAME" ] && [ "$PROJECT_NAME" != "null" ]; then
        DEFAULT_BUCKET="${PROJECT_NAME}-pypi-${ENVIRONMENT}"
    else
        DEFAULT_BUCKET=""
    fi
else
    DEFAULT_BUCKET=""
    DOMAIN_NAME=""
fi

# Parse arguments
TARGET="all"
BUCKET="${S3_PYPI_BUCKET:-$DEFAULT_BUCKET}"
DRY_RUN=0
AWS_REGION="${AWS_REGION:-us-west-2}"

while [[ $# -gt 0 ]]; do
    case $1 in
        --bucket)
            BUCKET="$2"
            shift 2
            ;;
        --core)
            TARGET="core"
            shift
            ;;
        --cdk)
            TARGET="cdk"
            shift
            ;;
        --all)
            TARGET="all"
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        *)
            echo -e "${RED}Unknown argument: $1${NC}"
            echo "Usage: $0 --bucket <bucket-name> [--core|--cdk|--all] [--dry-run]"
            exit 1
            ;;
    esac
done

# Validate bucket name provided
if [ -z "$BUCKET" ]; then
    echo -e "${RED}Error: S3 bucket name required${NC}"
    echo ""
    echo "Options:"
    echo "  1. Create infrastructure/parameters.json (automatic)"
    echo "  2. Set S3_PYPI_BUCKET: export S3_PYPI_BUCKET=your-bucket"
    echo "  3. Pass --bucket: $0 --bucket your-bucket"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Da Vinci S3 PyPI Distribution       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Target: $TARGET"
echo "Bucket: s3://$BUCKET"
echo "Region: $AWS_REGION"
if [ $DRY_RUN -eq 1 ]; then
    echo -e "${YELLOW}Mode: DRY RUN (no changes will be made)${NC}"
fi
echo ""

# Generate simple PyPI index.html
generate_index() {
    local package_name=$1
    local package_dir=$2
    local s3_prefix="s3://$BUCKET/simple/$package_name"

    echo -e "${YELLOW}→${NC} Generating index.html for $package_name..."

    # List all wheels in S3 for this package
    local wheels=$(aws s3 ls "$s3_prefix/" --region "$AWS_REGION" 2>/dev/null | grep '\.whl$' | awk '{print $4}' || echo "")

    # Generate HTML
    local html="<!DOCTYPE html>
<html>
<head>
    <title>Links for $package_name</title>
</head>
<body>
    <h1>Links for $package_name</h1>
"

    # Add links for each wheel
    for wheel in $wheels; do
        html+="    <a href=\"$wheel\">$wheel</a><br/>\n"
    done

    html+="</body>
</html>"

    # Write to temp file
    local temp_file=$(mktemp)
    echo -e "$html" > "$temp_file"

    if [ $DRY_RUN -eq 0 ]; then
        # Upload index.html
        aws s3 cp "$temp_file" "$s3_prefix/index.html" \
            --region "$AWS_REGION" \
            --content-type "text/html" \
            --metadata-directive REPLACE
        echo -e "${GREEN}✓ Updated index.html${NC}"
    else
        echo -e "${YELLOW}  Would upload index.html${NC}"
    fi

    rm "$temp_file"
}

# Generate root simple index.html
generate_root_index() {
    echo -e "${YELLOW}→${NC} Generating root simple/index.html..."

    # Discover all packages in S3
    local packages=$(aws s3 ls "s3://$BUCKET/simple/" --region "$AWS_REGION" 2>/dev/null | grep "PRE" | awk '{print $2}' | sed 's#/##g' | sort || echo "")

    # Generate HTML
    local html="<!DOCTYPE html>
<html>
<head>
    <title>Simple Index</title>
</head>
<body>
    <h1>Simple Index</h1>
"

    # Add links for each package
    for package in $packages; do
        html+="    <a href=\"$package/\">$package</a><br/>\n"
    done

    html+="</body>
</html>"

    # Write to temp file
    local temp_file=$(mktemp)
    echo -e "$html" > "$temp_file"

    if [ $DRY_RUN -eq 0 ]; then
        # Upload root index.html
        aws s3 cp "$temp_file" "s3://$BUCKET/simple/index.html" \
            --region "$AWS_REGION" \
            --content-type "text/html" \
            --metadata-directive REPLACE
        echo -e "${GREEN}✓ Updated root simple/index.html${NC}"
    else
        echo -e "${YELLOW}  Would upload root simple/index.html${NC}"
        echo -e "${YELLOW}  Discovered packages: $packages${NC}"
    fi

    rm "$temp_file"
    echo ""
}

# Upload package to S3
upload_package() {
    local package_name=$1
    local wheel_path=$2

    if [ ! -f "$wheel_path" ]; then
        echo -e "${RED}✗ Wheel file not found: $wheel_path${NC}"
        echo "  Run ./scripts/build.sh first"
        exit 1
    fi

    local wheel_file=$(basename "$wheel_path")
    local s3_path="s3://$BUCKET/simple/$package_name/$wheel_file"

    echo -e "${GREEN}Uploading $package_name...${NC}"
    echo "  Local:  $wheel_path"
    echo "  Remote: $s3_path"

    if [ $DRY_RUN -eq 0 ]; then
        # Upload wheel
        aws s3 cp "$wheel_path" "$s3_path" \
            --region "$AWS_REGION" \
            --content-type "application/octet-stream"

        echo -e "${GREEN}✓ Uploaded $(basename $wheel_path)${NC}"

        # Generate index
        generate_index "$package_name" "$(dirname $wheel_path)"
    else
        echo -e "${YELLOW}  Would upload wheel file${NC}"
        echo -e "${YELLOW}  Would update index.html${NC}"
    fi

    echo ""
}

# Verify S3 bucket exists and is accessible
verify_bucket() {
    echo -e "${YELLOW}→${NC} Verifying S3 bucket access..."

    if aws s3 ls "s3://$BUCKET" --region "$AWS_REGION" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Bucket accessible${NC}"
    else
        echo -e "${RED}✗ Cannot access bucket: s3://$BUCKET${NC}"
        echo "  Make sure:"
        echo "  1. Bucket exists"
        echo "  2. AWS credentials are configured"
        echo "  3. You have permissions to read/write"
        exit 1
    fi
    echo ""
}

# Upload based on target
if [ $DRY_RUN -eq 0 ]; then
    verify_bucket
fi

case $TARGET in
    core)
        CORE_WHEEL=$(ls packages/core/dist/*.whl 2>/dev/null | head -1)
        upload_package "da-vinci" "$CORE_WHEEL"
        ;;
    cdk)
        CDK_WHEEL=$(ls packages/cdk/dist/*.whl 2>/dev/null | head -1)
        upload_package "da-vinci-cdk" "$CDK_WHEEL"
        ;;
    all)
        CORE_WHEEL=$(ls packages/core/dist/*.whl 2>/dev/null | head -1)
        CDK_WHEEL=$(ls packages/cdk/dist/*.whl 2>/dev/null | head -1)

        upload_package "da-vinci" "$CORE_WHEEL"
        upload_package "da-vinci-cdk" "$CDK_WHEEL"
        ;;
esac

# Generate root index after all packages are uploaded
generate_root_index

# Invalidate CloudFront cache if using CloudFront
invalidate_cloudfront_cache() {
    echo -e "${YELLOW}→${NC} Invalidating CloudFront cache..."

    # Try multiple possible stack name patterns
    local stack_names=(
        "${PROJECT_NAME}-pypi-infrastructure"
        "${PROJECT_NAME}-pypi-${ENVIRONMENT}"
        "${PROJECT_NAME}-pypi"
    )

    local distribution_id=""
    for stack_name in "${stack_names[@]}"; do
        distribution_id=$(aws cloudformation describe-stacks \
            --stack-name "$stack_name" \
            --region "$AWS_REGION" \
            --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" \
            --output text 2>/dev/null || echo "")

        if [ -n "$distribution_id" ] && [ "$distribution_id" != "None" ]; then
            break
        fi
    done

    if [ -z "$distribution_id" ] || [ "$distribution_id" == "None" ]; then
        echo -e "${YELLOW}  No CloudFront distribution found, skipping cache invalidation${NC}"
        return
    fi

    echo "  Distribution ID: $distribution_id"

    # Create invalidation for all index.html files
    aws cloudfront create-invalidation \
        --distribution-id "$distribution_id" \
        --paths "/simple/*/index.html" "/simple/index.html" \
        --region us-east-1 >/dev/null

    echo -e "${GREEN}✓ CloudFront cache invalidation initiated${NC}"
    echo ""
}

if [ $DRY_RUN -eq 0 ]; then
    # Invalidate CloudFront cache
    invalidate_cloudfront_cache

    # Determine PyPI URL (CloudFront domain or S3 URL)
    if [ -n "$DOMAIN_NAME" ] && [ "$DOMAIN_NAME" != "null" ]; then
        PYPI_URL="https://$DOMAIN_NAME/simple/"
    else
        PYPI_URL="https://$BUCKET.s3.$AWS_REGION.amazonaws.com/simple/"
    fi

    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   Distribution Complete!               ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo "Installation Instructions:"
    echo ""
    echo "  # Install from private index (with PyPI fallback for dependencies)"
    echo "  pip install --index-url ${PYPI_URL} --extra-index-url https://pypi.org/simple/ da-vinci"
    echo ""
    echo "  # Or add to requirements.txt:"
    echo "  --index-url ${PYPI_URL}"
    echo "  --extra-index-url https://pypi.org/simple/"
    echo "  da-vinci"
    echo "  da-vinci-cdk"
    echo ""
    echo "PyPI Index URLs:"
    echo "  Root:  ${PYPI_URL}"
    echo "  Core:  ${PYPI_URL}da-vinci/"
    echo "  CDK:   ${PYPI_URL}da-vinci-cdk/"
else
    echo -e "${YELLOW}Dry run complete. No changes were made.${NC}"
    echo "Remove --dry-run to actually upload packages."
fi
