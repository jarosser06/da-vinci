# Code Example Validation Guide

This guide provides detailed instructions for validating code examples in da_vinci documentation against the actual implementation.

## Validation Workflow

### Step 1: Extract Code Examples

Look for code blocks in Sphinx RST documentation:

```rst
.. code-block:: python

   from da_vinci.core.orm.table_object import TableObject

   class MyTable(TableObject):
       table_name = "my_table"
```

### Step 2: Categorize Examples

**Complete Examples**
- Can be executed standalone
- Include all necessary imports
- Define all required variables
- Should be validated for correctness

**Code Snippets**
- Show partial implementation
- May reference undefined variables
- Still need import path validation
- Method signatures must be correct

**Shell Commands**
```rst
.. code-block:: bash

   cdk deploy --all
```
- Validate command syntax
- Check flags and options are valid

### Step 3: Validate Imports

#### Using Serena MCP

For each import statement, use serena to verify:

```python
# Example import to validate:
# from da_vinci.core.orm.table_object import TableObject

# Use serena:
mcp__serena__find_symbol(
    name_path_pattern="TableObject",
    relative_path="packages/core/da_vinci/core/orm/table_object.py"
)
```

#### Common Import Patterns to Check

**Core Package Imports**
```python
from da_vinci.core.orm.table_object import (
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
)

from da_vinci.core.orm.client import (
    TableClient,
    TableScanDefinition,
    PaginatedResults,
)

from da_vinci.core.settings import Settings
from da_vinci.core.logging import Logger
```

**CDK Package Imports**
```python
from da_vinci_cdk.application import Application
from da_vinci_cdk.stack import Stack
```

### Step 4: Validate Class Definitions

#### TableObject Validation

Check that all documented `TableObject` examples follow the correct pattern:

**Required Attributes**
- `table_name`: string
- `partition_key_attribute`: string (must match an attribute name)
- `sort_key_attribute`: string (optional, must match an attribute name)
- `attributes`: list of `TableObjectAttribute`

**Validation Checklist**
- [ ] `table_name` is a string
- [ ] `partition_key_attribute` references an attribute in `attributes` list
- [ ] If `sort_key_attribute` is set, it references an attribute in `attributes` list
- [ ] All attributes use valid `TableObjectAttributeType` values
- [ ] Attribute names are strings
- [ ] No duplicate attribute names

**Example to Validate**
```python
class UserTable(TableObject):
    table_name = "users"
    partition_key_attribute = "user_id"  # Must exist in attributes

    attributes = [
        TableObjectAttribute(
            name="user_id",  # Matches partition_key_attribute ✓
            attribute_type=TableObjectAttributeType.STRING,  # Valid type ✓
        ),
    ]
```

### Step 5: Validate TableObjectAttributeType Values

Use serena to get all valid attribute types:

```python
mcp__serena__find_symbol(
    name_path_pattern="TableObjectAttributeType",
    relative_path="packages/core/da_vinci/core/orm/table_object.py",
    include_body=True
)
```

**Valid Types (as of v2.0.0)**
- `STRING`
- `NUMBER`
- `BOOLEAN`
- `DATETIME`
- `JSON`
- `JSON_STRING`
- `STRING_LIST`
- `NUMBER_LIST`
- `JSON_LIST`
- `JSON_STRING_LIST`
- `COMPOSITE_STRING`
- `STRING_SET`
- `NUMBER_SET`

### Step 6: Validate TableClient Methods

#### Method Signature Validation

Use serena to check actual method signatures:

```python
mcp__serena__find_symbol(
    name_path_pattern="TableClient",
    relative_path="packages/core/da_vinci/core/orm/client.py",
    depth=1,  # Include methods
    include_body=False
)
```

#### Common Methods to Verify

**get()**
```python
# Documentation should show:
table_client.get(partition_key_value)
# OR with sort key:
table_client.get(partition_key_value, sort_key_value)
```

**put()**
```python
# Documentation should show:
table_client.put(table_object_instance)
```

**delete()**
```python
# Documentation should show:
table_client.delete(partition_key_value)
# OR with sort key:
table_client.delete(partition_key_value, sort_key_value)
```

**scan()**
```python
# Documentation should show:
table_client.scan()
# OR with definition:
table_client.scan(scan_definition=scan_def)
# OR with limit:
table_client.scan(limit=100)
```

**query()**
```python
# Documentation should show:
table_client.query(
    partition_key_value=value,
    index_name="index_name"  # Optional
)
# OR with sort key condition:
table_client.query(
    partition_key_value=value,
    sort_key_condition="attribute > :val",
    expression_values={":val": value}
)
```

### Step 7: Validate Index Definitions

#### Global Secondary Indexes

Check structure matches implementation:

```python
global_secondary_indexes = [
    {
        "index_name": "email_index",  # Required: string
        "partition_key": "email",      # Required: string (attribute name)
        "sort_key": "created_at",      # Optional: string (attribute name)
    }
]
```

**Validation Points**
- [ ] `index_name` is a string
- [ ] `partition_key` references an attribute
- [ ] `sort_key` (if present) references an attribute
- [ ] Referenced attributes exist in `attributes` list

#### Local Secondary Indexes

Check structure matches implementation:

```python
local_secondary_indexes = [
    {
        "index_name": "timestamp_index",  # Required: string
        "sort_key": "timestamp",          # Required: string (attribute name)
    }
]
```

**Validation Points**
- [ ] `index_name` is a string
- [ ] `sort_key` references an attribute
- [ ] Table has a `sort_key_attribute` defined (LSI requirement)
- [ ] Referenced attribute exists in `attributes` list

### Step 8: Validate CDK Examples

#### Application Construct

```python
mcp__serena__find_symbol(
    name_path_pattern="Application",
    relative_path="packages/cdk/da_vinci_cdk/application.py",
    depth=1
)
```

**Check Parameters**
- `app_name`: string
- `install_id`: string
- Other parameters match constructor signature

#### Common CDK Patterns

```python
# Application creation
app = Application(
    app_name="my_app",
    install_id="dev"
)

# Adding tables
app.add_table(TableObject)

# Synthesis
app.synth()
```

### Step 9: Cross-Reference with Tests

Find test files that use the same APIs:

```python
mcp__serena__search_for_pattern(
    substring_pattern="TableClient",
    relative_path="packages/core/tests",
    restrict_search_to_code_files=True
)
```

**Test files show correct usage**
- Test imports reveal correct paths
- Test setup shows proper initialization
- Test assertions reveal expected behavior
- Tests are the source of truth

### Step 10: Validate Complete Examples

For complete examples that claim to be runnable:

1. **Check all imports are present**
2. **Verify no undefined variables**
3. **Ensure proper initialization order**
4. **Validate return values are used correctly**

**Example Analysis**

```python
# Documentation example:
from da_vinci.core.orm.client import TableClient
from tables import UserTable

client = TableClient(UserTable)
user = client.get("user-123")
```

**Validation Checklist**
- [x] Imports are correct
- [x] `UserTable` is defined elsewhere (imported from tables)
- [x] `TableClient` constructor accepts TableObject class
- [x] `get()` method accepts partition key value
- [ ] ❌ Missing error handling (might return None)
- [ ] ⚠️ Consider noting that `user` could be None

## Common Issues Found in Documentation

### Import Path Issues

**Wrong**
```python
from da_vinci.orm.table_object import TableObject
```

**Correct**
```python
from da_vinci.core.orm.table_object import TableObject
```

### Method Signature Issues

**Wrong**
```python
table_client.get(key="value")  # No key parameter
```

**Correct**
```python
table_client.get("value")  # Positional argument
```

### Attribute Type Issues

**Wrong**
```python
attribute_type=TableObjectAttributeType.DATE  # No DATE type
```

**Correct**
```python
attribute_type=TableObjectAttributeType.DATETIME
```

### Index Structure Issues

**Wrong**
```python
global_secondary_indexes = [
    {
        "name": "email_index",  # Wrong key
        "partition": "email",   # Wrong key
    }
]
```

**Correct**
```python
global_secondary_indexes = [
    {
        "index_name": "email_index",
        "partition_key": "email",
    }
]
```

## Validation Tools

### Automated Validation Script (Future)

```python
# Extract code blocks from RST
# Parse Python code with AST
# Validate imports against package structure
# Check method calls against actual signatures
# Report issues with line numbers
```

### Manual Validation Process

1. Open documentation file
2. For each code example:
   - Copy code to temporary file
   - Use serena to validate each import
   - Use serena to validate each class/method
   - Check against test files for usage patterns
3. Document findings
4. Create fix recommendations

## Best Practices

1. **Always validate against actual code, not memory**
2. **Use serena MCP tools for symbol lookup**
3. **Cross-reference with test files**
4. **Check both import paths and usage patterns**
5. **Verify parameter names and types**
6. **Test examples should be runnable (or clearly marked as snippets)**
7. **Keep validation notes for future audits**
