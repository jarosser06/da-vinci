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
        # Run each package separately to avoid conftest conflicts
        echo "Running tests for all packages..."
        echo ""

        # Run core tests
        echo "→ Running da_vinci core tests..."
        PYTEST_CMD="uv run pytest da_vinci/tests"
        if [ $COVERAGE -eq 1 ]; then
            PYTEST_CMD="$PYTEST_CMD --cov=da_vinci --cov-append --cov-report="
        fi
        if [ $EMBEDDED -eq 1 ]; then
            PYTEST_CMD="$PYTEST_CMD -q"
        else
            PYTEST_CMD="$PYTEST_CMD -v"
        fi
        echo "Command: $PYTEST_CMD"
        $PYTEST_CMD
        CORE_EXIT=$?

        echo ""
        echo "→ Running da_vinci-cdk tests..."
        PYTEST_CMD="uv run pytest da_vinci-cdk/tests"
        if [ $COVERAGE -eq 1 ]; then
            PYTEST_CMD="$PYTEST_CMD --cov=da_vinci_cdk --cov-append --cov-report=term-missing --cov-report=html"
        fi
        if [ $EMBEDDED -eq 1 ]; then
            PYTEST_CMD="$PYTEST_CMD -q"
        else
            PYTEST_CMD="$PYTEST_CMD -v"
        fi
        echo "Command: $PYTEST_CMD"
        $PYTEST_CMD
        CDK_EXIT=$?

        # Set exit code based on both test runs
        if [ $CORE_EXIT -eq 0 ] && [ $CDK_EXIT -eq 0 ]; then
            EXIT_CODE=0
        else
            EXIT_CODE=1
        fi

        # Skip the normal test run below
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
        ;;
esac

# Build pytest command (for core or cdk only)
PYTEST_CMD="uv run pytest"

# Add test paths
PYTEST_CMD="$PYTEST_CMD $TEST_PATHS"

# Add coverage if requested
if [ $COVERAGE -eq 1 ]; then
    if [ $TARGET = "core" ]; then
        PYTEST_CMD="$PYTEST_CMD --cov=da_vinci --cov-report=term-missing --cov-report=html"
    else
        PYTEST_CMD="$PYTEST_CMD --cov=da_vinci_cdk --cov-report=term-missing --cov-report=html"
    fi
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
