# Development

**Description**: Da Vinci framework development patterns and standards. Use when implementing features in da_vinci core or da_vinci-cdk packages.

## When to Use This Skill

- Implementing Lambda functions or business logic in da_vinci core
- Creating CDK constructs or stacks in da_vinci-cdk
- Working with DynamoDB ORM, event bus, or exception trap
- Building AWS infrastructure using Da Vinci patterns
- Following project code standards and conventions

## Quick Reference

### Common Commands
- `./lint.sh --fix` - Auto-fix linting issues
- `uv sync` - Sync dependencies

### Package Structure
- **da_vinci** - Core library for application business logic
- **da_vinci_cdk** - CDK library for infrastructure declarations

### Key Concepts
- AWS-native development with minimal boilerplate
- Table definitions drive infrastructure
- Single source of truth for configuration
- Explicit dependencies between stacks
- Date-based versioning (YYYY.MM.PP)
- Line length: 100 characters

## Resource Guides

### 📖 [Da Vinci Core Framework](resources/da-vinci-core.md)
Comprehensive guide to the core da_vinci library including ORM, settings, and service discovery.

**Use when**: Implementing Lambda business logic, working with DynamoDB, or building service layers.

### 📖 [Da Vinci CDK Constructs](resources/da-vinci-cdk.md)
Guide to CDK constructs and framework stacks for infrastructure as code.

**Use when**: Creating infrastructure, defining applications, or working with CDK stacks.

### 📖 [Lambda Patterns](resources/lambda-patterns.md)
Best practices for Lambda functions in Da Vinci applications.

**Use when**: Creating new Lambda functions or refactoring existing ones.

### 📖 [Code Standards](resources/code-standards.md)
Python coding standards and conventions from CONTRIBUTING.md.

**Use when**: Writing any Python code to ensure consistency with project standards.

## Key Principles

1. **Use Context7 for Latest Docs**: Always fetch latest da-vinci documentation via context7 MCP when available
2. **Table Definitions Drive Infrastructure**: DynamoDB table definitions should be centralized
3. **Explicit Dependencies**: Always declare stack dependencies explicitly
4. **Code Standards**: Double quotes for strings, PEP 8, type hints, docstrings required, 100 char line length
5. **Single Source of Truth**: Centralize configuration, avoid duplication
