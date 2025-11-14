#!/usr/bin/env bash
#
# lint.sh - Unified linting and formatting for da_vinci workspace
#
# Usage:
#   ./lint.sh              # Lint all packages (both)
#   ./lint.sh core         # Lint da_vinci only
#   ./lint.sh cdk          # Lint da_vinci-cdk only
#   ./lint.sh --fix        # Auto-fix issues where possible
#   ./lint.sh core --fix   # Fix issues in core package
#   ./lint.sh --embedded   # Quieter output for CI/hooks (always exits 0)
#

set -e

# Parse arguments
TARGET="all"
FIX=0
EMBEDDED=0

for arg in "$@"; do
    case $arg in
        core)
            TARGET="core"
            ;;
        cdk)
            TARGET="cdk"
            ;;
        all)
            TARGET="all"
            ;;
        --fix)
            FIX=1
            ;;
        --embedded)
            EMBEDDED=1
            ;;
        *)
            echo "Unknown argument: $arg"
            echo "Usage: ./lint.sh [core|cdk|all] [--fix] [--embedded]"
            exit 1
            ;;
    esac
done

# Determine paths based on target
case $TARGET in
    core)
        PATHS="da_vinci/da_vinci"
        echo "Linting da_vinci core..."
        ;;
    cdk)
        PATHS="da_vinci-cdk/da_vinci_cdk"
        echo "Linting da_vinci-cdk..."
        ;;
    all)
        PATHS="da_vinci/da_vinci da_vinci-cdk/da_vinci_cdk"
        echo "Linting all packages..."
        ;;
esac

# Track overall exit code
OVERALL_EXIT_CODE=0

# Run ruff
echo ""
echo "→ Running ruff..."
if [ $FIX -eq 1 ]; then
    uv run ruff check $PATHS --fix || OVERALL_EXIT_CODE=$?
else
    uv run ruff check $PATHS || OVERALL_EXIT_CODE=$?
fi

# Run black
echo ""
echo "→ Running black..."
if [ $FIX -eq 1 ]; then
    uv run black $PATHS || OVERALL_EXIT_CODE=$?
else
    uv run black --check $PATHS || OVERALL_EXIT_CODE=$?
fi

# Run isort
echo ""
echo "→ Running isort..."
if [ $FIX -eq 1 ]; then
    uv run isort $PATHS || OVERALL_EXIT_CODE=$?
else
    uv run isort --check-only $PATHS || OVERALL_EXIT_CODE=$?
fi

# Run mypy
echo ""
echo "→ Running mypy..."
uv run mypy --explicit-package-bases $PATHS || OVERALL_EXIT_CODE=$?

# Summary
if [ $OVERALL_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✓ All linting checks passed!"
else
    echo ""
    if [ $FIX -eq 1 ]; then
        echo "✗ Some linting issues could not be auto-fixed. Please review the errors above."
    else
        echo "✗ Linting failed! Run './lint.sh --fix' to auto-fix some issues."
    fi
fi

# In embedded mode, always exit 0 so hooks don't block
if [ $EMBEDDED -eq 1 ]; then
    exit 0
fi

exit $OVERALL_EXIT_CODE
