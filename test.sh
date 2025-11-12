#!/usr/bin/env bash
#
# test.sh - Unified test runner for da_vinci workspace
#
# Usage:
#   ./test.sh              # Run all tests (both packages)
#   ./test.sh core         # Run da_vinci tests only
#   ./test.sh cdk          # Run da_vinci-cdk tests only
#   ./test.sh --coverage   # Run all tests with coverage report
#   ./test.sh core --coverage  # Run core tests with coverage
#   ./test.sh --embedded   # Quieter output for CI/hooks (always exits 0)
#

set -e

# Parse arguments
TARGET="all"
COVERAGE=0
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
        --coverage)
            COVERAGE=1
            ;;
        --embedded)
            EMBEDDED=1
            ;;
        *)
            echo "Unknown argument: $arg"
            echo "Usage: ./test.sh [core|cdk|all] [--coverage] [--embedded]"
            exit 1
            ;;
    esac
done

# Determine test paths based on target
case $TARGET in
    core)
        TEST_PATHS="da_vinci/tests"
        echo "Running tests for da_vinci core..."
        ;;
    cdk)
        TEST_PATHS="da_vinci-cdk/tests"
        echo "Running tests for da_vinci-cdk..."
        ;;
    all)
        TEST_PATHS="da_vinci/tests da_vinci-cdk/tests"
        echo "Running tests for all packages..."
        ;;
esac

# Build pytest command
PYTEST_CMD="uv run pytest"

# Add test paths
PYTEST_CMD="$PYTEST_CMD $TEST_PATHS"

# Add coverage if requested
if [ $COVERAGE -eq 1 ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=da_vinci --cov=da_vinci_cdk --cov-report=term-missing --cov-report=html"
fi

# Adjust verbosity for embedded mode
if [ $EMBEDDED -eq 1 ]; then
    PYTEST_CMD="$PYTEST_CMD -q"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Run tests
echo "Command: $PYTEST_CMD"
echo ""

$PYTEST_CMD

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✓ All tests passed!"
    if [ $COVERAGE -eq 1 ]; then
        echo "  Coverage report generated in htmlcov/index.html"
    fi
else
    echo ""
    echo "✗ Tests failed!"
fi

# In embedded mode, always exit 0 so hooks don't block
if [ $EMBEDDED -eq 1 ]; then
    exit 0
fi

exit $EXIT_CODE
