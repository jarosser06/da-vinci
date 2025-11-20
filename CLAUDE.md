# Da Vinci - Claude Code Integration

This document contains global information for AI-assisted development on the Da Vinci framework.

## Project Overview

Da Vinci is a framework for rapidly developing Python-based AWS Cloud Native applications. It consists of two packages:
- **da_vinci** (`packages/core`): Core runtime library for application business logic
- **da_vinci-cdk** (`packages/cdk`): CDK library for infrastructure declarations

## Versioning

### Format
- **MAJOR.MINOR.PATCH** - [Semantic Versioning](https://semver.org/)
- **MAJOR** = Incompatible API changes
- **MINOR** = Backward-compatible functionality additions
- **PATCH** = Backward-compatible bug fixes

### Version Policy
- Same MAJOR version = API compatibility (MINOR and PATCH are backward compatible)
- Different MAJOR version = Breaking changes
- Projects should pin to specific MAJOR.MINOR for stability

### Current Version
- 2.0.0

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
- Monorepo with two packages in `packages/` directory
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

### CRITICAL: Use Project Scripts

**ALWAYS use the provided scripts. DO NOT run tools directly or make up your own commands.**

### Test Commands
- `./test.sh` - Run all tests
- `./test.sh core` - Test da_vinci only
- `./test.sh cdk` - Test da_vinci-cdk only
- `./test.sh --coverage` - With coverage report

**NEVER run pytest directly. ALWAYS use ./test.sh**

### Lint Commands
- `./lint.sh` - Lint all packages
- `./lint.sh --fix` - Auto-fix issues
- `./lint.sh core` - Lint da_vinci only
- `./lint.sh cdk` - Lint da_vinci-cdk only

**NEVER run flake8, black, isort, or mypy directly. ALWAYS use ./lint.sh**

### Documentation Commands
- `./scripts/build-docs.sh` - Build Sphinx documentation
- `./scripts/deploy-docs.sh <version> <bucket> <distribution-id>` - Deploy docs to S3

**NEVER run sphinx-build or make directly. ALWAYS use ./scripts/build-docs.sh**

## Development Workflow

### Skills and Commands

**CRITICAL: Skill Activation is Mandatory**

When executing any slash command (e.g., `/create-pr`, `/work-on-issue`), you MUST:
1. Activate ALL skills listed in the command's frontmatter using the Skill tool
2. Skills are activated using: `Skill(skill-name)`
3. Skills MUST be activated BEFORE executing any other steps in the command

**Example**:
```
Command frontmatter lists: skills: [pr-writing, testing, linting]
You MUST call: Skill(pr-writing), Skill(testing), Skill(linting)
BEFORE running any tests, linting, or creating PRs
```

**Available Skills**:
- `development` - Development patterns and implementation guidance
- `testing` - Test execution and coverage validation
- `linting` - Code quality and formatting
- `code-review` - Comprehensive code review
- `github-operations` - GitHub issue and PR management
- `pr-writing` - Pull request description formatting
- `issue-writing` - GitHub issue creation standards
- `doc-audit` - Documentation validation
- `definition-of-done` - Work completion validation
- `python-docs` - Da Vinci framework documentation queries

### Branch Strategy
- Feature branches: `feature/description`
- Fix branches: `fix/description`
- Issue branches: `issue/<#>`

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
- `packages/core/pyproject.toml` - Core package configuration
- `packages/cdk/pyproject.toml` - CDK package configuration
- `scripts/` - Build and distribution automation
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
