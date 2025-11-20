# Python Documentation Standards

Ensure Python code follows PEP 257 docstring conventions and project-specific standards.

## Docstring Format

The da_vinci project uses a Sphinx-compatible docstring format with these conventions:

### Structure
- Use `"""triple double quotes"""` for all docstrings
- First line: Brief one-line summary (imperative mood, no period)
- Blank line after summary (for multi-line docstrings)
- Detailed description if needed
- Sections for parameters, returns, raises

### Sections Format
```python
"""
Brief summary in imperative mood

Detailed description explaining the purpose, behavior, and any important
context. Multiple paragraphs are allowed.

Keyword Arguments:
    param_name: Description of parameter
    another_param: Description (type information comes from type hints)

Returns:
    Description of return value

Raises:
    ExceptionType: When this exception is raised
"""
```

### Rules
1. **No "Notes from Claude" or similar commentary** - documentation must be production-ready
2. **No TODO comments** - flag incomplete work immediately for user action
3. **Accuracy over marketing** - avoid subjective language ("easily", "simply", "just")
4. **Type hints required** - all public functions must have complete type hints
5. **Consistency** - follow existing patterns in the codebase
6. **Completeness** - document all public APIs (classes, methods, functions)

### Examples

**Class:**
```python
class TableObject:
    """
    Base class for DynamoDB table objects with ORM capabilities

    Provides attribute definition, validation, and serialization for
    DynamoDB table records. Supports custom types, indexed attributes,
    and schema generation.

    Keyword Arguments:
        table_name: DynamoDB table name
        partition_key: Name of partition key attribute
        sort_key: Name of sort key attribute (optional)
    """
```

**Method:**
```python
def to_dict(
    self, exclude_attribute_names: list[str] | None = None, json_compatible: bool | None = False
) -> dict:
    """
    Convert the object to a dict representation

    Keyword Arguments:
    exclude_attribute_names -- List of attribute names to exclude from the resulting dict
    json_compatible -- Convert datetime objects to strings and sets to lists for JSON compatibility
    """
```

**Note:** The codebase uses `-- ` (double dash space) instead of `: ` (colon) for parameter descriptions. Parameters are NOT indented. No "Returns" section is used - return type comes from type hints.

**Function with Raises:**
```python
def get_deployment_id() -> str:
    """
    Get current deployment identifier from environment

    Raises:
        EnvironmentError -- When DEPLOYMENT_ID not set
    """
```

## Validation Checklist

When reviewing or writing documentation:

- [ ] All public classes have docstrings
- [ ] All public methods/functions have docstrings
- [ ] Type hints present for all parameters and returns
- [ ] No TODO comments (flag for immediate action)
- [ ] No "Notes from Claude" or placeholder text
- [ ] No subjective language ("easily", "simply", "just", "seamlessly")
- [ ] Accurate code examples (validated against actual implementation)
- [ ] Consistent format with existing codebase
- [ ] Complete parameter descriptions
- [ ] Return value documented
- [ ] Exceptions documented

## Common Mistakes to Avoid

1. **Signature duplication** - Don't repeat parameter names/types already in signature
2. **Obvious descriptions** - "Returns bool" adds no value, explain WHAT the bool means
3. **Implementation details** - Focus on WHAT and WHY, not HOW (unless critical)
4. **Outdated examples** - Always validate examples against current code
5. **Incomplete coverage** - Private methods can skip docs, public APIs cannot
