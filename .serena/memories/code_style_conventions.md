# Code Style and Conventions

## General
- **Line Length**: 100 characters maximum
- **Python Version**: ≥3.11 (core), ≥3.12 (CDK)
- **Type Hints**: Required (enforced by mypy)
- **File Encoding**: UTF-8

## Docstring Format
Use the python-docs skill format with Keyword Arguments:

```python
def method(param1: str, param2: int | None = None) -> bool:
    """
    Brief description in imperative mood

    Detailed explanation if needed.

    Keyword Arguments:
    param1 -- Description of param1
    param2 -- Description of param2 (optional)

    Raises:
        ValueError -- When condition occurs
    """
```

## Linting Tools
- **flake8** - Style checking
- **black** - Code formatting
- **isort** - Import sorting
- **mypy** - Type checking

## Testing
- **Framework**: pytest
- **Coverage Requirement**: 90% minimum
- **Stubs**: boto3-stubs for AWS type hints

## Design Principles
1. **Additive Convenience**: Provide convenience without blocking direct AWS access
2. **Single Source of Truth**: Centralized configurations and table definitions
3. **AWS-Native Development**: Stay close to AWS services
4. **Operational First**: Built-in error handling and production-ready patterns
