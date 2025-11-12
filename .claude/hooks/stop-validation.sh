#!/usr/bin/env bash
#
# stop-validation.sh - Run tests and linting when user stops work
#
# This hook runs when the user stops Claude Code. It provides informational
# feedback about test and lint status but always exits with 0 (non-blocking).
#

echo "Running validation checks..."
echo ""

# Run tests
echo "→ Running tests..."
./test.sh --embedded
TEST_EXIT=$?

echo ""

# Run linting
echo "→ Running linters..."
./lint.sh --embedded
LINT_EXIT=$?

echo ""
echo "======================================"
if [ $TEST_EXIT -eq 0 ] && [ $LINT_EXIT -eq 0 ]; then
    echo "✓ All validation checks passed!"
else
    if [ $TEST_EXIT -ne 0 ]; then
        echo "⚠ Tests failed"
    fi
    if [ $LINT_EXIT -ne 0 ]; then
        echo "⚠ Linting failed"
    fi
    echo ""
    echo "Run './test.sh' and './lint.sh' for details"
fi
echo "======================================"

# Always exit 0 (informational only, not blocking)
exit 0
