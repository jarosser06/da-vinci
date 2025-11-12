# Code Standards

Python coding standards for the Da Vinci project.

## String Quotes
- Always use double quotes for all strings
- Use single quotes only for nested strings within double-quoted strings

## General Style
- Follow PEP 8 guidelines
- Line length: 100 characters
- Use type hints where appropriate
- Add docstrings to all public classes and functions

## Type Hints
- Add type hints to function signatures
- Include parameter types and return types
- Use Optional for nullable values

## Docstrings
- Use Google-style or NumPy-style docstrings
- Include description, Args, Returns, and Raises sections
- Document all public APIs

## Imports
- Standard library imports first
- Third-party imports second
- Local imports third

## File Organization
- Keep files focused and modular
- Group related functionality
- Avoid god classes or modules

## Branching
- Use prefixes: feature/, fix/, docs/
- Examples: feature/add-s3-lifecycle-support, fix/event-bus-timeout-issue

## Commit Messages
- Title: Concise description (under 70 characters)
- Use active voice: "Add" not "Added"
- Include details with bullet points if needed
- Reference related issues

## Documentation
- Update README.md for new features
- Add docstrings to all new functions and classes
- Update CHANGELOG.md following existing format
