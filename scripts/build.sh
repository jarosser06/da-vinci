#!/usr/bin/env bash
#
# build.sh - Build wheel files for both packages
#
# Usage:
#   ./scripts/build.sh              # Build all packages
#   ./scripts/build.sh --core       # Build core package only
#   ./scripts/build.sh --cdk        # Build CDK package only
#   ./scripts/build.sh --clean      # Clean before building
#
# This script:
# 1. Cleans previous builds (if --clean)
# 2. Builds wheel files using hatchling
# 3. Validates Dockerfile is included in core package
# 4. Runs basic import validation
# 5. Generates build report
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
TARGET="all"
CLEAN=0

for arg in "$@"; do
    case $arg in
        --core)
            TARGET="core"
            ;;
        --cdk)
            TARGET="cdk"
            ;;
        --all)
            TARGET="all"
            ;;
        --clean)
            CLEAN=1
            ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            echo "Usage: $0 [--core|--cdk|--all] [--clean]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Da Vinci Package Build System       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Clean if requested
if [ $CLEAN -eq 1 ]; then
    echo -e "${YELLOW}→${NC} Cleaning previous builds..."
    rm -rf packages/core/dist packages/core/build
    rm -rf packages/cdk/dist packages/cdk/build
    rm -rf build dist *.egg-info
    echo "  Cleaned build directories"
    echo ""
fi

# Build core package
build_core() {
    echo -e "${GREEN}Building core package...${NC}"
    echo ""

    cd packages/core

    echo -e "${YELLOW}→${NC} Building wheel..."
    uv build

    # Get the built wheel filename (check both locations)
    WHEEL=$(ls dist/*.whl ../../dist/da_vinci-*.whl 2>/dev/null | grep -E 'da_vinci.*\.whl$' | head -1)

    if [ -z "$WHEEL" ]; then
        echo -e "${RED}✗ Failed to build core package${NC}"
        cd ../..
        exit 1
    fi

    # Create local dist directory if doesn't exist and copy wheel there
    mkdir -p dist
    if [ -f "../../dist/da_vinci-"*.whl ]; then
        cp ../../dist/da_vinci-*.whl dist/
        WHEEL=$(ls dist/*.whl | head -1)
    fi

    echo -e "${GREEN}✓ Built: $(basename $WHEEL)${NC}"

    # Validate Dockerfile is included
    echo ""
    echo -e "${YELLOW}→${NC} Validating Dockerfile inclusion..."
    if unzip -l "$WHEEL" | grep -q "Dockerfile"; then
        echo -e "${GREEN}✓ Dockerfile is included in package${NC}"
    else
        echo -e "${RED}✗ ERROR: Dockerfile NOT found in package!${NC}"
        cd ../..
        exit 1
    fi

    cd ../..
    echo ""
}

# Build CDK package
build_cdk() {
    echo -e "${GREEN}Building CDK package...${NC}"
    echo ""

    cd packages/cdk

    echo -e "${YELLOW}→${NC} Building wheel..."
    uv build

    # Get the built wheel filename (check both locations)
    WHEEL=$(ls dist/*.whl ../../dist/da_vinci_cdk-*.whl 2>/dev/null | grep -E 'da_vinci_cdk.*\.whl$' | head -1)

    if [ -z "$WHEEL" ]; then
        echo -e "${RED}✗ Failed to build CDK package${NC}"
        cd ../..
        exit 1
    fi

    # Create local dist directory if doesn't exist and copy wheel there
    mkdir -p dist
    if [ -f "../../dist/da_vinci_cdk-"*.whl ]; then
        cp ../../dist/da_vinci_cdk-*.whl dist/
        WHEEL=$(ls dist/*.whl | head -1)
    fi

    echo -e "${GREEN}✓ Built: $(basename $WHEEL)${NC}"

    cd ../..
    echo ""
}

# Validate builds
validate_builds() {
    echo -e "${GREEN}Validating builds...${NC}"
    echo ""

    # Check core package
    if [ -f packages/core/dist/*.whl ]; then
        CORE_WHEEL=$(ls packages/core/dist/*.whl | head -1)
        CORE_VERSION=$(basename "$CORE_WHEEL" | sed 's/da_vinci-\(.*\)-py3.*/\1/')
        echo -e "${YELLOW}→${NC} Core package: da-vinci $CORE_VERSION"
        echo "  Size: $(ls -lh $CORE_WHEEL | awk '{print $5}')"
    fi

    # Check CDK package
    if [ -f packages/cdk/dist/*.whl ]; then
        CDK_WHEEL=$(ls packages/cdk/dist/*.whl | head -1)
        CDK_VERSION=$(basename "$CDK_WHEEL" | sed 's/da_vinci_cdk-\(.*\)-py3.*/\1/')
        echo -e "${YELLOW}→${NC} CDK package: da-vinci-cdk $CDK_VERSION"
        echo "  Size: $(ls -lh $CDK_WHEEL | awk '{print $5}')"

        # Check CDK's dependency on core
        echo ""
        echo -e "${YELLOW}→${NC} Checking version consistency..."
        if [ "$CORE_VERSION" = "$CDK_VERSION" ]; then
            echo -e "${GREEN}✓ Versions match: $CORE_VERSION${NC}"
        else
            echo -e "${RED}✗ Version mismatch!${NC}"
            echo "  Core: $CORE_VERSION"
            echo "  CDK:  $CDK_VERSION"
            exit 1
        fi
    fi

    echo ""
}

# Build based on target
case $TARGET in
    core)
        build_core
        ;;
    cdk)
        build_cdk
        ;;
    all)
        build_core
        build_cdk
        validate_builds
        ;;
esac

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Build Complete!                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Built packages:"
ls -lh packages/*/dist/*.whl 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo "Next steps:"
echo "  1. Test installation: pip install packages/core/dist/*.whl"
echo "  2. Distribute to S3: ./scripts/distribute.sh"
