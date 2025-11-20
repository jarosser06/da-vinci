#!/bin/bash
# Build Sphinx documentation
# This script builds the documentation HTML files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCS_DIR="$PROJECT_ROOT/docs"

echo "Building documentation..."
cd "$DOCS_DIR"

# Clean previous build
rm -rf _build/html

# Build HTML documentation
# Note: -W flag treats warnings as errors, but disabled for now due to existing docstring issues
uv run sphinx-build -M html . _build

echo ""
echo "Documentation built successfully!"
echo "Output: $DOCS_DIR/_build/html/index.html"
echo ""
echo "To view locally: open $DOCS_DIR/_build/html/index.html"
