#!/usr/bin/env bash
#
# update-changelog.sh - Update CHANGELOG.md with new version entry
#
# Usage:
#   ./scripts/update-changelog.sh <version> <description>
#
# Example:
#   ./scripts/update-changelog.sh 2.1.0 "Added new feature X, Fixed bug Y"
#
# This script:
# 1. Adds a new version entry to CHANGELOG.md
# 2. Formats entry with version, date, and description
# 3. Preserves existing changelog entries
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
VERSION="$1"
DESCRIPTION="$2"

if [[ -z "$VERSION" ]]; then
    echo -e "${RED}Error: Version required${NC}" >&2
    echo "Usage: $0 <version> <description>" >&2
    echo "" >&2
    echo "Example:" >&2
    echo "  $0 2.1.0 \"Added new feature X, Fixed bug Y\"" >&2
    exit 1
fi

if [[ -z "$DESCRIPTION" ]]; then
    echo -e "${RED}Error: Description required${NC}" >&2
    echo "Usage: $0 <version> <description>" >&2
    exit 1
fi

# Validate version format
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}Error: Invalid version format '$VERSION'${NC}" >&2
    echo "Expected: MAJOR.MINOR.PATCH (e.g., 2.1.0)" >&2
    exit 1
fi

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CHANGELOG="$PROJECT_ROOT/CHANGELOG.md"

if [ ! -f "$CHANGELOG" ]; then
    echo -e "${RED}Error: CHANGELOG.md not found${NC}" >&2
    exit 1
fi

# Get current date
DATE=$(date +"%Y-%m-%d")

# Create new entry
NEW_ENTRY="## [$VERSION] - $DATE

$DESCRIPTION
"

echo -e "${YELLOW}→${NC} Updating CHANGELOG.md..." >&2
echo "" >&2
echo "Version: $VERSION" >&2
echo "Date:    $DATE" >&2
echo "Changes: $DESCRIPTION" >&2
echo "" >&2

# Create temp file with new entry
TEMP_FILE=$(mktemp)

# Read changelog and insert new entry after the title
{
    # First line (title)
    head -n 1 "$CHANGELOG"
    echo ""
    # New entry
    echo "$NEW_ENTRY"
    # Rest of the file (skip first line)
    tail -n +2 "$CHANGELOG"
} > "$TEMP_FILE"

# Replace original file
mv "$TEMP_FILE" "$CHANGELOG"

echo -e "${GREEN}✓ CHANGELOG.md updated successfully!${NC}" >&2
echo "" >&2
