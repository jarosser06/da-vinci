# Test Quality Review Guide

This guide helps reviewers assess test quality beyond just coverage percentages.

## Philosophy

**Coverage percentage is necessary but not sufficient.** A test suite can have 90% coverage but still miss critical edge cases, parameter combinations, and real-world scenarios.

## What to Look For

### 1. Parameter Combination Testing

**BAD - Only tests default case:**
```python
def test_create_table(self, stack):
    table = DynamoDBTable(
        scope=stack,
        table_name="test-table",
        partition_key=Attribute(name="id", type=AttributeType.STRING),
    )
    assert table is not None
```

**GOOD - Tests multiple configurations:**
```python
def test_create_table_basic(self, stack):
    """Test basic table creation with required params only."""
    table = DynamoDBTable(
        scope=stack,
        table_name="test-table",
        partition_key=Attribute(name="id", type=AttributeType.STRING),
    )
    assert table is not None
    assert table.table is not None

def test_create_table_with_sort_key(self, stack):
    """Test table with both partition and sort keys."""
    DynamoDBTable(
        scope=stack,
        table_name="test-table",
        partition_key=Attribute(name="pk", type=AttributeType.STRING),
        sort_key=Attribute(name="sk", type=AttributeType.STRING),
    )
    template = Template.from_stack(stack)
    template.has_resource_properties(
        "AWS::DynamoDB::GlobalTable",
        {"KeySchema": [
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ]}
    )

def test_create_table_with_billing_mode(self, stack):
    """Test table with custom billing mode."""
    # ... test PAY_PER_REQUEST vs PROVISIONED

def test_create_table_with_removal_policy(self, stack):
    """Test table with different removal policies."""
    # ... test DESTROY, RETAIN, SNAPSHOT
```

### 2. Edge Case Coverage

**BAD - Only happy path:**
```python
def test_process_items(self):
    items = [1, 2, 3]
    result = process_items(items)
    assert len(result) == 3
```

**GOOD - Covers edge cases:**
```python
def test_process_items_with_data(self):
    """Test processing with valid items."""
    items = [1, 2, 3]
    result = process_items(items)
    assert len(result) == 3

def test_process_items_empty_list(self):
    """Test processing with empty list."""
    result = process_items([])
    assert result == []

def test_process_items_single_item(self):
    """Test processing with single item."""
    result = process_items([1])
    assert len(result) == 1

def test_process_items_large_batch(self):
    """Test processing with large batch (boundary condition)."""
    items = list(range(1000))
    result = process_items(items)
    assert len(result) == 1000

def test_process_items_with_none(self):
    """Test error handling for None input."""
    with pytest.raises(ValueError):
        process_items(None)

def test_process_items_with_invalid_type(self):
    """Test error handling for invalid types."""
    with pytest.raises(TypeError):
        process_items("not a list")
```

### 3. Behavioral Validation (Not Just Existence)

**BAD - Shallow assertions:**
```python
def test_create_lambda_function(self, stack):
    function = LambdaFunction(
        scope=stack,
        construct_id="test-function",
        entry="test/path",
        index="index.py",
        handler="handler",
    )
    assert function is not None  # ❌ Only checks existence
```

**GOOD - Validates actual behavior:**
```python
def test_create_lambda_function(self, stack, temp_dockerfile_dir):
    """Test Lambda function creates with correct configuration."""
    function = LambdaFunction(
        scope=stack,
        construct_id="test-function",
        entry=temp_dockerfile_dir,
        index="index.py",
        handler="handler",
        memory_size=512,
        timeout=Duration.seconds(120),
    )

    # ✓ Validates properties
    assert function.function is not None

    # ✓ Validates synthesized template
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::Lambda::Function", 1)

    # ✓ Validates actual resource properties
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "MemorySize": 512,
            "Timeout": 120,
        }
    )
```

### 4. Error Path Testing

**BAD - Only tests success:**
```python
def test_convert_type(self):
    result = convert_type("STRING")
    assert result == AttributeType.STRING
```

**GOOD - Tests both success and failure:**
```python
def test_convert_type_valid_types(self):
    """Test conversion of all valid types."""
    assert convert_type("STRING") == AttributeType.STRING
    assert convert_type("NUMBER") == AttributeType.NUMBER
    assert convert_type("BINARY") == AttributeType.BINARY

def test_convert_type_invalid_type(self):
    """Test error handling for invalid type."""
    with pytest.raises(ValueError, match="Unknown type"):
        convert_type("INVALID")

def test_convert_type_case_sensitivity(self):
    """Test that conversion is case-sensitive."""
    with pytest.raises(ValueError):
        convert_type("string")  # lowercase should fail
```

### 5. Integration Testing

**BAD - Tests in complete isolation:**
```python
def test_table_exists(self, stack):
    table = DynamoDBTable(scope=stack, table_name="test", ...)
    assert table is not None

def test_role_exists(self, stack):
    role = Role(stack, "role", ...)
    assert role is not None
```

**GOOD - Tests interaction:**
```python
def test_grant_table_access_to_role(self, stack):
    """Test granting table access creates proper IAM policies."""
    role = Role(
        stack, "TestRole",
        assumed_by=ServicePrincipal("lambda.amazonaws.com")
    )

    table = DynamoDBTable(
        scope=stack,
        table_name="test-table",
        partition_key=Attribute(name="id", type=AttributeType.STRING),
    )

    # Test the integration
    table.grant_read_write_access(role)

    # Validate the interaction worked
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::IAM::Policy", 1)
    # Could also validate the policy document contains correct permissions
```

### 6. Conditional Logic Coverage

**Code with conditions:**
```python
def create_resource(name: str, enabled: bool = True, config: dict | None = None):
    resource = BaseResource(name)

    if enabled:
        resource.activate()

    if config:
        resource.configure(config)
    else:
        resource.use_defaults()

    return resource
```

**BAD - Tests only one path:**
```python
def test_create_resource(self):
    result = create_resource("test")
    assert result is not None
```

**GOOD - Tests all branches:**
```python
def test_create_resource_enabled_with_config(self):
    """Test resource creation when enabled with custom config."""
    result = create_resource("test", enabled=True, config={"key": "value"})
    assert result.is_active
    assert result.has_custom_config

def test_create_resource_enabled_without_config(self):
    """Test resource creation when enabled with default config."""
    result = create_resource("test", enabled=True, config=None)
    assert result.is_active
    assert result.has_default_config

def test_create_resource_disabled_with_config(self):
    """Test resource creation when disabled with custom config."""
    result = create_resource("test", enabled=False, config={"key": "value"})
    assert not result.is_active
    assert result.has_custom_config

def test_create_resource_disabled_without_config(self):
    """Test resource creation when disabled with default config."""
    result = create_resource("test", enabled=False, config=None)
    assert not result.is_active
    assert result.has_default_config
```

## Review Questions to Ask

When reviewing tests, ask yourself:

### Coverage Questions
1. ✓ Does the code have ≥90% line coverage?
2. ✓ Are all public methods tested?
3. ✓ Are all conditional branches (if/else) exercised?

### Quality Questions
4. ✓ Are different parameter combinations tested?
   - Required params only?
   - Optional params with different values?
   - All significant combinations?

5. ✓ Are edge cases covered?
   - Empty/null values?
   - Boundary conditions (0, max values)?
   - Invalid inputs?

6. ✓ Are error paths tested?
   - Expected exceptions raised?
   - Error messages meaningful?
   - Recovery/cleanup happens?

7. ✓ Do assertions validate behavior?
   - Not just `is not None`?
   - Actual property values checked?
   - Side effects verified?

8. ✓ Are integrations tested?
   - Components work together?
   - Dependencies handled correctly?
   - Cross-component interactions validated?

9. ✓ Are tests maintainable?
   - Clear test names?
   - Good documentation?
   - Use of shared fixtures?
   - No test interdependencies?

10. ✓ Do tests fail for the right reasons?
    - Would a bug in the code cause the test to fail?
    - Are the assertions specific enough?

## Common Test Quality Issues

### Issue: High coverage but missing edge cases
```python
# Has 100% line coverage but misses empty list edge case
def test_sum_items(self):
    assert sum_items([1, 2, 3]) == 6
    assert sum_items([5]) == 5
    # Missing: sum_items([]) - what should this return?
```

### Issue: Testing implementation details instead of behavior
```python
# BAD - tests internal implementation
def test_cache_is_dict(self):
    obj = MyClass()
    assert isinstance(obj._cache, dict)

# GOOD - tests actual behavior
def test_cached_results_returned_quickly(self):
    obj = MyClass()
    first_call = obj.expensive_operation()
    second_call = obj.expensive_operation()
    assert first_call == second_call
    # Verify caching by checking performance or call counts
```

### Issue: Mocking too much (tests pass but code doesn't work)
```python
# BAD - mocks everything, doesn't test real behavior
@patch('module.function_a')
@patch('module.function_b')
@patch('module.function_c')
def test_process(self, mock_a, mock_b, mock_c):
    mock_a.return_value = "a"
    mock_b.return_value = "b"
    mock_c.return_value = "c"
    result = process()
    assert result is not None  # Test passes but tells us nothing

# GOOD - only mocks external dependencies
def test_process(self, mocker):
    # Only mock external AWS/HTTP calls
    mock_s3 = mocker.patch('boto3.client')
    mock_s3.return_value.get_object.return_value = {...}

    # Test real internal logic
    result = process()
    assert result == expected_transformed_data
```

## CDK-Specific Quality Checks

### Check: Resource types are correct
```python
# ✓ Verify using actual resource type da_vinci creates
template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)  # Not "Table"
template.resource_count_is("Custom::DaVinci@ResourceDiscovery", 1)  # Custom resources
```

### Check: Properties match actual behavior
```python
# ✓ Verify the properties that matter for the feature
template.has_resource_properties(
    "AWS::Lambda::Function",
    {
        "Timeout": 120,  # Actual configured value
        "MemorySize": 512,  # Actual configured value
    }
)
```

### Check: Fixtures are used correctly
```python
# ✓ Use shared fixtures instead of recreating
def test_something(self, stack, temp_dockerfile_dir, library_base_image):
    # Uses fixtures from conftest.py
    pass
```

## Summary

Good test quality means:
- **Coverage + Completeness**: All code paths AND all meaningful scenarios
- **Behavior validation**: Tests verify what code does, not just that it exists
- **Edge case handling**: Boundary conditions, errors, invalid inputs
- **Parameter combinations**: Different ways the code can be called
- **Integration verification**: Components work together correctly
- **Maintainability**: Clear, isolated, well-documented tests

When reviewing, don't just check the coverage percentage—dig into whether the tests actually validate that the code works correctly in all scenarios.
