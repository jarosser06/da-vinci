#!/usr/bin/env bash
#
# bump-version.sh - Bump version for both da_vinci packages
#
# Usage:
#   ./scripts/bump-version.sh [major|minor|patch] [--no-changelog]
#
# This script:
# 1. Reads current version from packages/core/pyproject.toml
# 2. Calculates new version based on SemVer bump type
# 3. Updates version in both packages/core and packages/cdk
# 4. Updates CDK dependency on core to exact version
# 5. Optionally updates CHANGELOG.md via update-changelog.sh
# 6. Regenerates uv.lock
# 7. Outputs new version to stdout
#
# Note: This script does NOT create git commits or tags.
# The release skill handles git operations.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
BUMP_TYPE=""
UPDATE_CHANGELOG=true

while [[ $# -gt 0 ]]; do
    case $1 in
        major|minor|patch)
            BUMP_TYPE="$1"
            shift
            ;;
        --no-changelog)
            UPDATE_CHANGELOG=false
            shift
            ;;
        *)
            echo -e "${RED}Unknown argument: $1${NC}" >&2
            echo "Usage: $0 [major|minor|patch] [--no-changelog]" >&2
            exit 1
            ;;
    esac
done

# Validate bump type
if [[ -z "$BUMP_TYPE" ]]; then
    echo -e "${RED}Error: Bump type required${NC}" >&2
    echo "Usage: $0 [major|minor|patch] [--no-changelog]" >&2
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Read current version from core package
CORE_PYPROJECT="$PROJECT_ROOT/packages/core/pyproject.toml"
CDK_PYPROJECT="$PROJECT_ROOT/packages/cdk/pyproject.toml"

if [ ! -f "$CORE_PYPROJECT" ]; then
    echo -e "${RED}Error: Core pyproject.toml not found${NC}" >&2
    exit 1
fi

if [ ! -f "$CDK_PYPROJECT" ]; then
    echo -e "${RED}Error: CDK pyproject.toml not found${NC}" >&2
    exit 1
fi

# Extract current version
CURRENT_VERSION=$(grep '^version = ' "$CORE_PYPROJECT" | sed 's/version = "\(.*\)"/\1/')

if [[ -z "$CURRENT_VERSION" ]]; then
    echo -e "${RED}Error: Could not read current version${NC}" >&2
    exit 1
fi

# Parse version components
if [[ ! "$CURRENT_VERSION" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    echo -e "${RED}Error: Invalid version format '$CURRENT_VERSION'${NC}" >&2
    echo "Expected: MAJOR.MINOR.PATCH" >&2
    exit 1
fi

MAJOR="${BASH_REMATCH[1]}"
MINOR="${BASH_REMATCH[2]}"
PATCH="${BASH_REMATCH[3]}"

# Calculate new version
case $BUMP_TYPE in
    major)
        NEW_MAJOR=$((MAJOR + 1))
        NEW_MINOR=0
        NEW_PATCH=0
        ;;
    minor)
        NEW_MAJOR=$MAJOR
        NEW_MINOR=$((MINOR + 1))
        NEW_PATCH=0
        ;;
    patch)
        NEW_MAJOR=$MAJOR
        NEW_MINOR=$MINOR
        NEW_PATCH=$((PATCH + 1))
        ;;
esac

NEW_VERSION="${NEW_MAJOR}.${NEW_MINOR}.${NEW_PATCH}"

echo -e "${BLUE}Bumping version: ${CURRENT_VERSION} → ${NEW_VERSION}${NC}" >&2
echo "" >&2

# Update core package version
echo -e "${YELLOW}→${NC} Updating packages/core/pyproject.toml..." >&2
sed -i.bak "s/^version = \".*\"/version = \"$NEW_VERSION\"/" "$CORE_PYPROJECT"
rm "${CORE_PYPROJECT}.bak"
echo -e "${GREEN}✓ Updated core package${NC}" >&2

# Update __version__ in __init__.py
CORE_INIT="$PROJECT_ROOT/packages/core/da_vinci/__init__.py"
echo -e "${YELLOW}→${NC} Updating packages/core/da_vinci/__init__.py..." >&2
sed -i.bak "s/^__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" "$CORE_INIT"
rm "${CORE_INIT}.bak"
echo -e "${GREEN}✓ Updated __version__${NC}" >&2

# Update CDK package version
echo -e "${YELLOW}→${NC} Updating packages/cdk/pyproject.toml..." >&2
sed -i.bak "s/^version = \".*\"/version = \"$NEW_VERSION\"/" "$CDK_PYPROJECT"

# Update CDK dependency on core to minimum version
# Match only in dependencies array, not the name field
sed -i.bak "/dependencies = \[/,/\]/s/\"da-vinci[^\"]*\"/\"da-vinci>=$NEW_VERSION\"/" "$CDK_PYPROJECT"
rm "${CDK_PYPROJECT}.bak"
echo -e "${GREEN}✓ Updated CDK package and dependency${NC}" >&2

# Update uv.lock
echo "" >&2
echo -e "${YELLOW}→${NC} Updating uv.lock..." >&2
cd "$PROJECT_ROOT"
uv lock --quiet
echo -e "${GREEN}✓ Updated lockfile${NC}" >&2

# Update changelog if requested
if [ "$UPDATE_CHANGELOG" = true ]; then
    echo "" >&2
    echo -e "${YELLOW}Note: Run ./scripts/update-changelog.sh to update CHANGELOG.md${NC}" >&2
fi

echo "" >&2
echo -e "${GREEN}✓ Version bumped successfully!${NC}" >&2
echo "" >&2

# Output new version to stdout for capture
echo "$NEW_VERSION"
