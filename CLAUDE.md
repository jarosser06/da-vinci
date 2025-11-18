# Da Vinci - Claude Code Integration

This document contains global information for AI-assisted development on the Da Vinci framework.

## Project Overview

Da Vinci is a framework for rapidly developing Python-based AWS Cloud Native applications. It consists of two packages:
- **da_vinci**: Core runtime library for application business logic
- **da_vinci-cdk**: CDK library for infrastructure declarations

## Versioning

### Format
- **YYYY.MM.PP** - Date-based versioning
- **YYYY.MM** = API contract version
- **PP** = Patch number for non-breaking changes

### Version Policy
- Same YYYY.MM = Same API contract (backward compatible)
- Different YYYY.MM = Potential breaking changes
- Projects should pin to specific YYYY.MM for stability

### Current Version
- 2025.4.20

## Core Principles

### Additive Convenience
- Framework provides convenience without blocking direct AWS access
- Never prevent boto3 or direct AWS service usage
- Users can mix framework features with direct AWS calls
- Eliminate boilerplate, not control

### Single Source of Truth
- Table definitions centralized
- Configuration in one place
- Avoid duplication

### AWS-Native Development
- Stay close to AWS services
- Framework wraps but doesn't hide
- Leverage AWS managed services

### Operational First
- Built-in error handling
- Service discovery
- Event communication
- Production-ready patterns

### Table Definitions Drive Infrastructure
- DynamoDB table definitions should be centralized
- Infrastructure generated from code
- Consistent naming across environments

## Package Management

### uv Workspace
- Monorepo with two packages
- Root workspace configuration
- Shared development dependencies
- Both packages installed in editable mode

### Dependencies
- Core: Python ≥3.11, boto3, requests
- CDK: Python ≥3.12, aws-cdk-lib, constructs, da-vinci (workspace)
- Dev: pytest, flake8, black, isort, mypy, boto3-stubs

## Testing & Quality

### Coverage Requirement
- **90% minimum** coverage required
- Enforced before PR merge
- Combined coverage across both packages

### Linting
- Line length: 100 characters
- Tools: flake8, black, isort, mypy
- Zero lint errors required for PR

### Test Commands
- `./test.sh` - Run all tests
- `./test.sh core` - Test da_vinci only
- `./test.sh cdk` - Test da_vinci-cdk only
- `./test.sh --coverage` - With coverage report

### Lint Commands
- `./lint.sh` - Lint all packages
- `./lint.sh --fix` - Auto-fix issues
- `./lint.sh core` - Lint da_vinci only
- `./lint.sh cdk` - Lint da_vinci-cdk only

## Development Workflow

### Branch Strategy
- Feature branches: `feature/description`
- Fix branches: `fix/description`
- Issue branches: `issue/{number}-description`

### Commit Message Format
- Title: Under 70 characters, active voice
- Body: Bullet points for multiple changes
- Reference issues when applicable

### Pull Request Process
1. Ensure tests pass (90% coverage)
2. Ensure linting passes (zero errors)
3. Squash commits appropriately
4. Create PR with clear description
5. Respond to review feedback

## MCP Servers

### context7
- Fetch latest da-vinci documentation
- Get up-to-date framework patterns
- Always prefer context7 over outdated assumptions

### serena
- Code navigation and symbol search
- Intelligent code refactoring
- Find references and definitions

### github
- Issue and PR management
- Auto-detect repository from git remote
- Requires GITHUB_PERSONAL_ACCESS_TOKEN

## Key Files

- `pyproject.toml` - Root workspace configuration
- `da_vinci/pyproject.toml` - Core package configuration
- `da_vinci-cdk/pyproject.toml` - CDK package configuration
- `CONTRIBUTING.md` - Contribution guidelines
- `CHANGELOG.md` - Version history
- `README.md` - Project overview

## Development Environment

### Devcontainer
- Python 3.12, Node.js 22
- AWS CLI, AWS CDK
- uv package manager
- All dev tools pre-installed

### Local Development
- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Sync workspace: `uv sync`
- Run tests: `./test.sh`
- Run linting: `./lint.sh --fix`
