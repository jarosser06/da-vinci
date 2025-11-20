#!/usr/bin/env bash
#
# validate.sh - Pre-distribution validation
#
# Usage:
#   ./scripts/validate.sh           # Run all validations
#   ./scripts/validate.sh --quick   # Skip slow tests (imports only)
#
# This script validates:
# 1. All tests pass with required coverage (90%)
# 2. All linting checks pass (zero errors)
# 3. Version consistency between packages
# 4. Built wheels exist and are valid
# 5. Package imports work correctly
# 6. No uncommitted changes (unless --allow-dirty)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
QUICK=0
ALLOW_DIRTY=0

for arg in "$@"; do
    case $arg in
        --quick)
            QUICK=1
            ;;
        --allow-dirty)
            ALLOW_DIRTY=1
            ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            echo "Usage: $0 [--quick] [--allow-dirty]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Da Vinci Pre-Distribution Validation║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

FAILED=0

# Check for uncommitted changes
if [ $ALLOW_DIRTY -eq 0 ]; then
    echo -e "${YELLOW}→${NC} Checking git status..."
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${RED}✗ Uncommitted changes detected${NC}"
        echo "  Commit or stash changes before distributing"
        echo "  Or use --allow-dirty to skip this check"
        FAILED=1
    else
        echo -e "${GREEN}✓ Working directory clean${NC}"
    fi
    echo ""
fi

# Check version consistency
echo -e "${YELLOW}→${NC} Checking version consistency..."
CORE_VERSION=$(grep '^version = ' packages/core/pyproject.toml | sed 's/version = "\(.*\)"/\1/')
CDK_VERSION=$(grep '^version = ' packages/cdk/pyproject.toml | sed 's/version = "\(.*\)"/\1/')
CDK_DEP=$(grep '"da-vinci' packages/cdk/pyproject.toml | grep -o '==.*"' | tr -d '="' || echo "not pinned")

if [ "$CORE_VERSION" != "$CDK_VERSION" ]; then
    echo -e "${RED}✗ Version mismatch${NC}"
    echo "  Core: $CORE_VERSION"
    echo "  CDK:  $CDK_VERSION"
    FAILED=1
elif [ "$CDK_DEP" != "==$CORE_VERSION" ]; then
    echo -e "${RED}✗ CDK dependency not pinned correctly${NC}"
    echo "  Expected: da-vinci==$CORE_VERSION"
    echo "  Got: da-vinci$CDK_DEP"
    FAILED=1
else
    echo -e "${GREEN}✓ Versions consistent: $CORE_VERSION${NC}"
fi
echo ""

# Run linting
if [ $QUICK -eq 0 ]; then
    echo -e "${YELLOW}→${NC} Running linting checks..."
    if ./lint.sh >/dev/null 2>&1; then
        echo -e "${GREEN}✓ All linting checks passed${NC}"
    else
        echo -e "${RED}✗ Linting failed${NC}"
        echo "  Run ./lint.sh to see errors"
        FAILED=1
    fi
    echo ""
fi

# Run tests with coverage
if [ $QUICK -eq 0 ]; then
    echo -e "${YELLOW}→${NC} Running tests with coverage..."
    if ./test.sh --coverage >/dev/null 2>&1; then
        # Check coverage percentage
        COVERAGE=$(grep -A 1 "TOTAL" .coverage 2>/dev/null | tail -1 | awk '{print $NF}' | tr -d '%' || echo "0")
        if [ "${COVERAGE%.*}" -ge 90 ]; then
            echo -e "${GREEN}✓ All tests passed (${COVERAGE}% coverage)${NC}"
        else
            echo -e "${RED}✗ Coverage below 90% (${COVERAGE}%)${NC}"
            FAILED=1
        fi
    else
        echo -e "${RED}✗ Tests failed${NC}"
        echo "  Run ./test.sh to see errors"
        FAILED=1
    fi
    echo ""
fi

# Check built wheels exist
echo -e "${YELLOW}→${NC} Checking built packages..."
if [ -f packages/core/dist/*.whl ] && [ -f packages/cdk/dist/*.whl ]; then
    CORE_WHEEL=$(ls packages/core/dist/*.whl | head -1)
    CDK_WHEEL=$(ls packages/cdk/dist/*.whl | head -1)
    echo -e "${GREEN}✓ Built packages found${NC}"
    echo "  Core: $(basename $CORE_WHEEL)"
    echo "  CDK:  $(basename $CDK_WHEEL)"

    # Validate Dockerfile in core package
    if unzip -l "$CORE_WHEEL" | grep -q "Dockerfile"; then
        echo -e "${GREEN}✓ Dockerfile included in core package${NC}"
    else
        echo -e "${RED}✗ Dockerfile NOT found in core package${NC}"
        FAILED=1
    fi
else
    echo -e "${RED}✗ Built packages not found${NC}"
    echo "  Run ./scripts/build.sh first"
    FAILED=1
fi
echo ""

# Test package imports (in isolated venv)
echo -e "${YELLOW}→${NC} Validating package imports..."
TEMP_VENV=$(mktemp -d)
python3 -m venv "$TEMP_VENV" >/dev/null 2>&1

if [ -f packages/core/dist/*.whl ]; then
    CORE_WHEEL=$(ls packages/core/dist/*.whl | head -1)

    if "$TEMP_VENV/bin/pip" install "$CORE_WHEEL" >/dev/null 2>&1; then
        if "$TEMP_VENV/bin/python" -c "import da_vinci; import da_vinci.core" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Core package imports successfully${NC}"
        else
            echo -e "${RED}✗ Core package import failed${NC}"
            FAILED=1
        fi
    else
        echo -e "${RED}✗ Failed to install core package${NC}"
        FAILED=1
    fi
fi

rm -rf "$TEMP_VENV"
echo ""

# Final result
echo -e "${BLUE}════════════════════════════════════════${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All validations passed!${NC}"
    echo ""
    echo "Ready to distribute:"
    echo "  ./scripts/distribute.sh --bucket <your-bucket>"
    exit 0
else
    echo -e "${RED}✗ Validation failed${NC}"
    echo ""
    echo "Fix the issues above before distributing."
    exit 1
fi
