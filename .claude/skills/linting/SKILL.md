# Linting

**Description**: Run linters and formatters for da_vinci packages. Use when checking code quality or auto-fixing issues.

## When to Use This Skill

- Running linters before commit
- Auto-fixing formatting issues
- Checking code quality
- Validating code before PR

## Quick Reference

### Lint Commands
- `./lint.sh` - Lint all packages
- `./lint.sh --fix` - Auto-fix issues
- `./lint.sh core` - Lint da_vinci core only
- `./lint.sh cdk` - Lint da_vinci-cdk only

### Tools Used
- **ruff**: Fast Python linter
- **black**: Code formatter (100 char line length)
- **isort**: Import organizer
- **mypy**: Type checker

## Configuration

All linting configuration in root `pyproject.toml`:
- Line length: 100 characters
- Target Python: 3.12
- Black-compatible isort profile
- Strict mypy type checking

## Key Principles

1. **Zero Lint Errors**: Required for PR approval
2. **Auto-Fix First**: Run `./lint.sh --fix` before manual fixes
3. **Type Hints Required**: All public APIs must have type hints
4. **100 Char Line Length**: Enforced by black
