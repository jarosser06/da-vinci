#!/bin/bash
#
# setup.sh - Post-creation setup script for da_vinci devcontainer
#

set -e

echo "======================================"
echo "Da Vinci Devcontainer Setup"
echo "======================================"

# Install uv (Python package manager)
echo ""
echo "→ Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Verify uv installation
echo "  uv version: $(uv --version)"

# Install Python packages using uv
echo ""
echo "→ Installing Python workspace with uv..."
cd /workspaces/da_vinci
uv sync

# Install Node.js and CDK (globally)
echo ""
echo "→ Installing AWS CDK CLI..."
sudo npm install -g aws-cdk || echo "Warning: CDK installation failed, continuing..."
if command -v cdk &> /dev/null; then
    echo "  CDK version: $(cdk --version)"
fi

# Install Claude Code CLI (optional, continue on failure)
echo ""
echo "→ Installing Claude Code CLI..."
sudo npm install -g @anthropic-ai/claude-code || echo "Warning: Claude Code CLI installation failed, continuing..."

# Configure GitHub CLI if token is available
if [ -n "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
    echo ""
    echo "→ Configuring GitHub CLI..."
    echo "$GITHUB_PERSONAL_ACCESS_TOKEN" | gh auth login --with-token
else
    echo ""
    echo "⚠ GITHUB_PERSONAL_ACCESS_TOKEN not set. Skipping GitHub CLI authentication."
    echo "  Set this environment variable to enable GitHub integration."
fi

# Create convenience alias
echo ""
echo "→ Creating workspace alias..."
echo 'alias ws="cd /workspaces/da_vinci"' >> ~/.bashrc

# Display versions of installed tools
echo ""
echo "======================================"
echo "Installed Tools:"
echo "======================================"
echo "Python: $(python3 --version)"
echo "uv: $(uv --version)"
echo "AWS CLI: $(aws --version 2>&1 | head -n1)"
if command -v cdk &> /dev/null; then
    echo "AWS CDK: $(cdk --version)"
fi
if command -v gh &> /dev/null; then
    echo "GitHub CLI: $(gh --version | head -n1)"
fi
echo ""
echo "======================================"
echo "Setup complete!"
echo "======================================"
echo ""
echo "Quick start:"
echo "  ws               # Navigate to workspace"
echo "  ./test.sh        # Run tests"
echo "  ./lint.sh        # Run linters"
echo "  ./test.sh core   # Test da_vinci core only"
echo "  ./lint.sh --fix  # Auto-fix linting issues"
echo ""
