# Common Documentation Issues

This guide catalogs common issues found in da_vinci documentation and how to identify and fix them.

## Import Path Issues

### Issue: Incorrect Module Path

**Problem**: Import statements don't match actual package structure

**Examples**

❌ **Wrong**
```python
from da_vinci.orm.table_object import TableObject
from da_vinci_cdk import Application
```

✅ **Correct**
```python
from da_vinci.core.orm.table_object import TableObject
from da_vinci_cdk.application import Application
```

**Detection Method**
- Use serena `find_symbol` to verify module paths
- Check actual file locations in packages/core and packages/cdk

**Fix Process**
1. Identify incorrect import in documentation
2. Use serena to find correct path
3. Update documentation with correct import
4. Verify import works in both packages

### Issue: Missing .core in Import Path

**Problem**: Omitting the `core` submodule

**Examples**

❌ **Wrong**
```python
from da_vinci.orm.client import TableClient
from da_vinci.settings import Settings
```

✅ **Correct**
```python
from da_vinci.core.orm.client import TableClient
from da_vinci.core.settings import Settings
```

### Issue: Missing Imports in Complete Examples

**Problem**: Examples claim to be complete but are missing necessary imports

**Example**

❌ **Incomplete**
```python
# Example: Create a user table

class UserTable(TableObject):
    table_name = "users"
    partition_key_attribute = "user_id"
```

✅ **Complete**
```python
# Example: Create a user table

from da_vinci.core.orm.table_object import (
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
)

class UserTable(TableObject):
    table_name = "users"
    partition_key_attribute = "user_id"

    attributes = [
        TableObjectAttribute(
            name="user_id",
            attribute_type=TableObjectAttributeType.STRING,
        ),
    ]
```

## API Signature Issues

### Issue: Incorrect Method Parameters

**Problem**: Documentation shows method calls with wrong parameters

**Examples**

❌ **Wrong**
```python
client.get(key="user-123")  # get() doesn't use keyword arg
client.put(item=user)       # put() doesn't use keyword arg
```

✅ **Correct**
```python
client.get("user-123")      # Positional argument
client.put(user)            # Positional argument
```

**Detection Method**
- Use serena to read method signatures from actual code
- Compare with documented examples
- Check test files for actual usage

### Issue: Missing Required Parameters

**Problem**: Examples omit required parameters

**Example**

❌ **Wrong**
```python
app = Application()  # Missing required parameters
```

✅ **Correct**
```python
app = Application(
    app_name="my_app",
    install_id="dev"
)
```

### Issue: Using Non-Existent Parameters

**Problem**: Documentation uses parameters that don't exist in actual API

**Detection Method**
- Read actual method signatures
- Compare against documented examples
- Flag any discrepancies

## Table Definition Issues

### Issue: Incorrect Attribute Type Names

**Problem**: Using attribute types that don't exist

**Examples**

❌ **Wrong**
```python
attribute_type=TableObjectAttributeType.DATE      # No DATE type
attribute_type=TableObjectAttributeType.INTEGER   # No INTEGER type
attribute_type=TableObjectAttributeType.FLOAT     # No FLOAT type
attribute_type=TableObjectAttributeType.DICT      # No DICT type
```

✅ **Correct**
```python
attribute_type=TableObjectAttributeType.DATETIME  # Use DATETIME
attribute_type=TableObjectAttributeType.NUMBER    # Use NUMBER
attribute_type=TableObjectAttributeType.NUMBER    # Use NUMBER
attribute_type=TableObjectAttributeType.JSON      # Use JSON or JSON_STRING
```

**Valid Types**
- STRING, NUMBER, BOOLEAN, DATETIME
- JSON, JSON_STRING
- STRING_LIST, NUMBER_LIST, JSON_LIST, JSON_STRING_LIST
- COMPOSITE_STRING
- STRING_SET, NUMBER_SET

### Issue: Partition/Sort Key Not in Attributes

**Problem**: Keys reference attributes that aren't defined

**Example**

❌ **Wrong**
```python
class MyTable(TableObject):
    table_name = "my_table"
    partition_key_attribute = "id"  # Not in attributes!

    attributes = [
        TableObjectAttribute(
            name="user_id",  # Different name
            attribute_type=TableObjectAttributeType.STRING,
        ),
    ]
```

✅ **Correct**
```python
class MyTable(TableObject):
    table_name = "my_table"
    partition_key_attribute = "user_id"  # Matches attribute

    attributes = [
        TableObjectAttribute(
            name="user_id",
            attribute_type=TableObjectAttributeType.STRING,
        ),
    ]
```

### Issue: Incorrect Index Structure

**Problem**: Index definitions don't match expected structure

**Examples**

❌ **Wrong - GSI**
```python
global_secondary_indexes = [
    {
        "name": "email_index",      # Wrong key
        "partition": "email",       # Wrong key
    }
]
```

✅ **Correct - GSI**
```python
global_secondary_indexes = [
    {
        "index_name": "email_index",
        "partition_key": "email",
    }
]
```

❌ **Wrong - LSI**
```python
local_secondary_indexes = [
    {
        "name": "timestamp_index",   # Wrong key
        "key": "timestamp",          # Wrong key
    }
]
```

✅ **Correct - LSI**
```python
local_secondary_indexes = [
    {
        "index_name": "timestamp_index",
        "sort_key": "timestamp",
    }
]
```

## TableClient Usage Issues

### Issue: Incorrect Scan Filter Syntax

**Problem**: Documentation shows wrong syntax for scan filters

**Example**

❌ **Wrong**
```python
client.scan(filter="email == 'test@example.com'")
```

✅ **Correct**
```python
from da_vinci.core.orm.client import TableScanDefinition

scan_def = TableScanDefinition(TableClass)
scan_def.add("email", "==", "test@example.com")
client.scan(scan_definition=scan_def)
```

### Issue: Incorrect Query Syntax

**Problem**: Query examples don't match actual API

**Example**

❌ **Wrong**
```python
client.query(
    partition_key="user_id",           # Wrong parameter name
    partition_value="user-123",         # Wrong parameter name
)
```

✅ **Correct**
```python
client.query(
    partition_key_value="user-123",    # Correct parameter
    index_name="user_index"            # Optional
)
```

## CDK Infrastructure Issues

### Issue: Incorrect CDK Import Paths

**Problem**: CDK examples use wrong import paths

**Examples**

❌ **Wrong**
```python
from da_vinci_cdk import Application, Stack
```

✅ **Correct**
```python
from da_vinci_cdk.application import Application
from da_vinci_cdk.stack import Stack
```

### Issue: Missing CDK Synthesis

**Problem**: Examples don't show how to synthesize CDK app

**Example**

❌ **Incomplete**
```python
app = Application(app_name="my_app", install_id="dev")
app.add_table(UserTable)
# Missing synth!
```

✅ **Complete**
```python
app = Application(app_name="my_app", install_id="dev")
app.add_table(UserTable)
app.synth()  # Required for CDK
```

## Datetime and Type Issues

### Issue: Incorrect datetime Usage

**Problem**: Examples use datetime incorrectly

**Examples**

❌ **Wrong**
```python
from datetime import datetime

created_at = datetime.now()  # Missing timezone
```

✅ **Correct**
```python
from datetime import datetime, UTC

created_at = datetime.now(UTC)  # Timezone-aware
```

### Issue: Mixing Types in Examples

**Problem**: Examples show incorrect Python types for DynamoDB types

**Example**

❌ **Wrong**
```python
# NUMBER attribute with string value
quantity = "5"  # Should be int or float

# STRING_LIST with single string
tags = "python"  # Should be list
```

✅ **Correct**
```python
# NUMBER attribute with numeric value
quantity = 5  # int or float

# STRING_LIST with list
tags = ["python", "aws"]  # list of strings
```

## Composite Key Issues

### Issue: Missing argument_names for Composite Keys

**Problem**: COMPOSITE_STRING attributes missing required argument_names

**Example**

❌ **Wrong**
```python
TableObjectAttribute(
    name="composite_key",
    attribute_type=TableObjectAttributeType.COMPOSITE_STRING,
    # Missing argument_names!
)
```

✅ **Correct**
```python
TableObjectAttribute(
    name="composite_key",
    attribute_type=TableObjectAttributeType.COMPOSITE_STRING,
    argument_names=["order_id", "user_id"],
)
```

### Issue: Incorrect Composite Key Initialization

**Problem**: Examples show wrong way to initialize composite keys

**Example**

❌ **Wrong**
```python
item = MyTable(
    composite_key="order-123|user-456"  # Don't pass combined string
)
```

✅ **Correct**
```python
item = MyTable(
    order_id="order-123",  # Pass argument_names
    user_id="user-456"     # separately
)
```

## Command Line Issues

### Issue: Incorrect CDK Commands

**Problem**: Documentation shows commands that don't work

**Examples**

❌ **Wrong**
```bash
cdk deploy  # Without --all for multiple stacks
npm install aws-cdk  # Missing -g flag
```

✅ **Correct**
```bash
cdk deploy --all  # Deploy all stacks
npm install -g aws-cdk  # Global install
```

## Documentation Structure Issues

### Issue: Missing Prerequisites

**Problem**: Examples assume tools/packages without mentioning them

**Fix**: Always include prerequisites section

```rst
Prerequisites
-------------

Before starting, ensure you have:

- Python 3.11+ installed
- AWS credentials configured
- AWS CDK CLI installed (``npm install -g aws-cdk``)
- Da Vinci packages installed
```

### Issue: Code Examples Without Context

**Problem**: Code snippets lack context about where they should be used

**Fix**: Add context comments or surrounding explanation

```rst
Create a file called ``tables.py`` for your table definitions:

.. code-block:: python

   # tables.py
   from da_vinci.core.orm.table_object import TableObject

   class UserTable(TableObject):
       # ...
```

### Issue: Orphaned References

**Problem**: Documentation references sections or files that don't exist

**Detection**: Check all `:doc:` and `:ref:` links

**Examples**

❌ **Wrong**
```rst
See :doc:`advanced-patterns` for more information.
# But advanced-patterns.rst doesn't exist!
```

## Version-Specific Issues

### Issue: Outdated API Examples

**Problem**: Documentation shows APIs from older versions

**Detection Method**
- Check version mentioned in example
- Verify against current implementation
- Look for deprecated warnings

### Issue: Missing Version Information

**Problem**: Examples don't specify which version they apply to

**Fix**: Add version tags or notes

```rst
.. note::
   This feature is available in da_vinci >= 2.0.0
```

## Testing Examples

### Issue: Examples That Can't Run

**Problem**: "Complete" examples missing critical pieces

**Checklist for Runnable Examples**
- [ ] All imports present
- [ ] All variables defined
- [ ] Correct initialization order
- [ ] No undefined references
- [ ] Proper error handling (or note about omission)

### Issue: Examples Without Expected Output

**Problem**: Code examples don't show what happens when you run them

**Fix**: Include output examples

```rst
.. code-block:: python

   user = client.get("user-123")
   print(user.name)

Output::

   Alice Smith
```

## Best Practices for Avoiding Issues

1. **Validate Against Implementation**
   - Use serena to check actual code
   - Don't rely on memory or assumptions
   - Cross-reference with tests

2. **Complete Examples**
   - Include all imports
   - Define all variables
   - Show initialization to usage

3. **Version Awareness**
   - Note version requirements
   - Keep examples current
   - Mark deprecated features

4. **Test Your Examples**
   - Try to run code examples
   - Verify commands work
   - Check output matches docs

5. **Clear Context**
   - Explain where code goes
   - Show file structure
   - Link to related sections

6. **Regular Audits**
   - Review docs with each release
   - Validate examples still work
   - Update for API changes
