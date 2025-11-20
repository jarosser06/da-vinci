# Suggested Commands

## Development Setup
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync workspace dependencies
uv sync
```

## Testing
```bash
# Run all tests
./test.sh

# Test specific package
./test.sh core        # Test da_vinci only
./test.sh cdk         # Test da_vinci-cdk only

# Run with coverage report
./test.sh --coverage
```

## Linting & Formatting
```bash
# Lint all packages
./lint.sh

# Auto-fix lint issues
./lint.sh --fix

# Lint specific package
./lint.sh core        # Lint da_vinci only
./lint.sh cdk         # Lint da_vinci-cdk only
```

## Git Workflow
```bash
# Create feature branch
git checkout -b feature/description

# Create fix branch
git checkout -b fix/description

# Create issue branch
git checkout -b issue/<#>
```

## System Commands (macOS/Darwin)
- Standard Unix commands available: `git`, `ls`, `cd`, `grep`, `find`, etc.
