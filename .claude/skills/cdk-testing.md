# CDK Testing Patterns

This skill provides comprehensive patterns and best practices for testing AWS CDK constructs in the da_vinci-cdk package.

## Overview

The da_vinci-cdk package uses AWS CDK's built-in `assertions` module along with pytest to test infrastructure code without deploying to AWS. All tests synthesize CDK stacks to CloudFormation templates and validate their properties.

## Test Structure

### Directory Organization
```
da_vinci-cdk/tests/
├── conftest.py                    # Shared fixtures
├── test_application.py            # Application and CoreStack tests
├── test_stack.py                  # Stack tests
├── constructs/
│   ├── __init__.py
│   ├── test_access_management.py
│   ├── test_base.py
│   ├── test_dns.py
│   ├── test_dynamodb.py
│   ├── test_event_bus.py
│   ├── test_global_setting.py
│   ├── test_lambda_function.py
│   ├── test_resource_discovery.py
│   ├── test_s3.py
│   └── test_service.py
└── framework_stacks/
    ├── __init__.py
    ├── test_service_stacks.py
    └── test_table_stacks.py
```

### Test File Naming
- `test_*.py` - All test files must start with `test_`
- Match source file names: `test_<module_name>.py`

## Shared Fixtures (conftest.py)

### Essential Fixtures

```python
@pytest.fixture
def test_context():
    """Provide standard context values for CDK tests."""
    return {
        "app_name": "test-app",
        "deployment_id": "test-deployment",
        "architecture": Architecture.ARM_64,
        "log_level": "INFO",
        "resource_discovery_storage_solution": "ssm",
        "global_settings_enabled": True,
        "exception_trap_enabled": True,
    }

@pytest.fixture
def app(test_context):
    """Create a CDK App with test context."""
    cdk_app = App(context=test_context)
    return cdk_app

@pytest.fixture
def stack(app):
    """Create a CDK Stack with test context."""
    return Stack(app, "TestStack")

@pytest.fixture
def temp_dockerfile_dir():
    """Create a temporary directory with a Dockerfile for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dockerfile_path = Path(tmpdir) / "Dockerfile"
        dockerfile_path.write_text("""ARG IMAGE
FROM ${IMAGE}
ARG FUNCTION_INDEX
ARG FUNCTION_HANDLER
COPY ${FUNCTION_INDEX}.py ${LAMBDA_TASK_ROOT}
CMD ["${FUNCTION_INDEX}.${FUNCTION_HANDLER}"]
""")
        index_path = Path(tmpdir) / "index.py"
        index_path.write_text("def handler(event, context):\\n    return {'statusCode': 200}\\n")
        yield tmpdir

@pytest.fixture
def library_base_image():
    """Provide a base image string for library Lambda functions."""
    return "public.ecr.aws/lambda/python:3.12"
```

## Testing Patterns

### Pattern 1: Basic Construct Creation

```python
def test_construct_creation(self, stack):
    """Test basic construct creation."""
    construct = MyConstruct(
        scope=stack,
        construct_id="test-construct",
        required_param="value",
    )

    assert construct is not None
    assert construct.some_property is not None

    template = Template.from_stack(stack)
    template.resource_count_is("AWS::ResourceType", 1)
```

### Pattern 2: Resource Properties Validation

```python
def test_construct_with_properties(self, stack):
    """Test construct creates resources with correct properties."""
    MyConstruct(
        scope=stack,
        construct_id="test-construct",
        memory_size=512,
        timeout=Duration.seconds(120),
    )

    template = Template.from_stack(stack)
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "MemorySize": 512,
            "Timeout": 120,
        }
    )
```

### Pattern 3: Multiple Resource Types

```python
def test_construct_creates_multiple_resources(self, stack):
    """Test construct creates all required resources."""
    construct = MyConstruct(scope=stack, construct_id="test")

    template = Template.from_stack(stack)
    template.resource_count_is("AWS::Lambda::Function", 1)
    template.resource_count_is("AWS::IAM::Role", 1)
    template.resource_count_is("AWS::S3::Bucket", 1)
```

### Pattern 4: Lambda Functions with Docker

```python
def test_lambda_function_creation(self, stack, temp_dockerfile_dir):
    """Test Lambda function with Docker build."""
    function = LambdaFunction(
        scope=stack,
        construct_id="test-function",
        entry=temp_dockerfile_dir,
        index="index.py",
        handler="handler",
        disable_image_cache=True,  # Important for tests
    )

    assert function is not None
    assert function.function is not None

    template = Template.from_stack(stack)
    template.resource_count_is("AWS::Lambda::Function", 1)
```

### Pattern 5: Service Constructs

```python
def test_async_service_creation(self, stack, temp_dockerfile_dir):
    """Test AsyncService with all required components."""
    service = AsyncService(
        scope=stack,
        service_name="test-async",
        entry=temp_dockerfile_dir,
        index="index.py",
        handler="handler",
        base_image="public.ecr.aws/lambda/python:3.12",
        memory_size=256,
        timeout=Duration.seconds(60),
    )

    assert service is not None
    assert service.queue is not None
    assert service.handler is not None

    template = Template.from_stack(stack)
    template.resource_count_is("AWS::Lambda::Function", 1)
    template.resource_count_is("AWS::Lambda::EventSourceMapping", 1)
```

### Pattern 6: Framework Stacks

```python
def test_table_stack_creation(self, app):
    """Test framework table stack creation."""
    stack = GlobalSettingsTableStack(
        app_name="test-app",
        deployment_id="test-deployment",
        scope=app,
        stack_name="GlobalSettingsTable",
    )

    assert stack is not None

    template = Template.from_stack(stack)
    template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)
```

### Pattern 7: Application Tests

```python
def test_application_creation(self, mocker):
    """Test Application with mocked Docker builds."""
    # Mock DockerImage.from_build to avoid actual Docker builds
    mock_docker = mocker.patch(
        "aws_cdk.DockerImage.from_build",
        return_value=mocker.MagicMock(image="mocked-image")
    )

    app = Application(
        app_name="test-app",
        deployment_id="test-deployment",
    )

    assert app is not None
    assert app.app_name == "test-app"
    assert app.deployment_id == "test-deployment"
    mock_docker.assert_called()
```

### Pattern 8: Mocking External Dependencies

```python
@patch("da_vinci_cdk.constructs.dns.DiscoverableResource.read_endpoint")
def test_with_external_lookup(self, mock_read_endpoint, stack):
    """Test construct that requires external resource lookup."""
    mock_read_endpoint.return_value = "Z1234567890ABC"

    construct = MyConstruct(
        scope=stack,
        resource_name="external-resource",
    )

    assert construct is not None
    mock_read_endpoint.assert_called_once()
```

### Pattern 9: Custom Resources

```python
def test_custom_resource_creation(self, stack):
    """Test custom CloudFormation resource."""
    resource = DiscoverableResource(
        scope=stack,
        construct_id="discoverable",
        resource_type=ResourceType.TABLE,
        resource_name="test-table",
        resource_arn="arn:aws:dynamodb:us-east-1:123:table/test",
    )

    assert resource is not None
    assert resource.resource is not None

    template = Template.from_stack(stack)
    template.resource_count_is("Custom::DaVinci@ResourceDiscovery", 1)
```

### Pattern 10: Grant Permissions

```python
def test_grant_permissions(self, stack):
    """Test IAM permission grants."""
    from aws_cdk.aws_iam import Role, ServicePrincipal

    role = Role(
        stack,
        "TestRole",
        assumed_by=ServicePrincipal("lambda.amazonaws.com")
    )

    table = DynamoDBTable(
        scope=stack,
        table_name="test-table",
        partition_key=Attribute(name="id", type=AttributeType.STRING),
    )

    table.grant_read_write_access(role)

    # Verify grant was applied
    assert table.table is not None
    assert role is not None

    # Optionally check IAM policy was created
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::IAM::Role", 1)
```

## Important Considerations

### 1. Context Values
Always ensure CDK context contains required values:
- `app_name`
- `deployment_id`
- `architecture`

### 2. Docker Image Handling
For Lambda functions that use Docker:
- Use `temp_dockerfile_dir` fixture for actual builds
- Use `disable_image_cache=True` to avoid caching issues
- Use `base_image` parameter when possible to skip builds
- Mock `DockerImage.from_build` for Application-level tests

### 3. Global Tables
da_vinci uses DynamoDB Global Tables by default:
```python
template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)
```
NOT `AWS::DynamoDB::Table`

### 4. Custom Resource Types
da_vinci uses custom CloudFormation resources:
- `Custom::DaVinci@ResourceDiscovery`
- `Custom::DaVinci@EventBusSubscription`
- `Custom::DaVinci@GlobalSetting`

### 5. Stack Initialization
Always provide required parameters:
```python
stack = Stack(
    app_name="test-app",
    deployment_id="test-deployment",
    scope=app,
    stack_name="TestStack",
)
```

### 6. Fixture Usage
Use fixtures consistently:
```python
def test_something(self, stack, temp_dockerfile_dir, library_base_image):
    # stack, temp_dockerfile_dir, library_base_image from fixtures
    pass
```

### 7. Test Organization
Group tests by class:
```python
class TestMyConstruct:
    """Tests for MyConstruct class."""

    def test_basic_creation(self, stack):
        pass

    def test_with_options(self, stack):
        pass
```

## Coverage Requirements

- **Target**: ≥90% code coverage for da_vinci-cdk package
- Run tests with: `./test.sh cdk --coverage`
- View HTML report: `htmlcov/index.html`

### Coverage Best Practices
1. Test all public methods
2. Test different parameter combinations
3. Test edge cases and error conditions
4. Test integration between constructs
5. Avoid testing private methods unless critical

## Common Assertions

```python
# Resource count
template.resource_count_is("AWS::Lambda::Function", 1)

# Resource properties
template.has_resource_properties("AWS::Lambda::Function", {
    "Runtime": "python3.12",
    "Timeout": 60,
})

# Property existence
template.has_resource_properties("AWS::S3::Bucket", {
    "VersioningConfiguration": {"Status": "Enabled"}
})

# Using Match for flexible assertions
from aws_cdk.assertions import Match

template.has_resource_properties("AWS::IAM::Role", {
    "AssumeRolePolicyDocument": {
        "Statement": Match.array_with([
            Match.object_like({
                "Action": "sts:AssumeRole",
                "Effect": "Allow",
            })
        ])
    }
})
```

## Running Tests

```bash
# Run all CDK tests
./test.sh cdk

# Run with coverage
./test.sh cdk --coverage

# Run specific test file
pytest da_vinci-cdk/tests/constructs/test_lambda_function.py -v

# Run specific test
pytest da_vinci-cdk/tests/constructs/test_lambda_function.py::TestLambdaFunction::test_creation -v
```

## Troubleshooting

### Issue: Import errors
**Solution**: Ensure fixtures are imported from conftest.py automatically

### Issue: Docker build failures
**Solution**: Use `disable_image_cache=True` or mock `DockerImage.from_build`

### Issue: Context value missing
**Solution**: Add required context keys to `test_context` fixture

### Issue: Wrong resource type
**Solution**: Check if da_vinci uses custom or global resources (e.g., GlobalTable vs Table)

### Issue: Typeguard warnings
**Solution**: These are CDK library warnings and can be ignored - they don't affect tests

## Example: Complete Test File

```python
"""Unit tests for da_vinci_cdk.constructs.example module."""

import pytest
from aws_cdk import Duration
from aws_cdk.assertions import Template

from da_vinci_cdk.constructs.example import ExampleConstruct


class TestExampleConstruct:
    """Tests for ExampleConstruct class."""

    def test_basic_creation(self, stack):
        """Test basic ExampleConstruct creation."""
        construct = ExampleConstruct(
            scope=stack,
            construct_id="test-example",
            name="test-name",
        )

        assert construct is not None
        assert construct.resource is not None

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::Example::Resource", 1)

    def test_with_optional_parameters(self, stack):
        """Test ExampleConstruct with optional parameters."""
        ExampleConstruct(
            scope=stack,
            construct_id="test-example",
            name="test-name",
            timeout=Duration.seconds(120),
            memory=512,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::Example::Resource",
            {
                "Timeout": 120,
                "Memory": 512,
            }
        )

    def test_creates_multiple_resources(self, stack):
        """Test ExampleConstruct creates all required resources."""
        ExampleConstruct(
            scope=stack,
            construct_id="test-example",
            name="test-name",
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::Example::Resource", 1)
        template.resource_count_is("AWS::IAM::Role", 1)

    def test_grant_access(self, stack):
        """Test granting access to the resource."""
        from aws_cdk.aws_iam import Role, ServicePrincipal

        role = Role(
            stack,
            "TestRole",
            assumed_by=ServicePrincipal("lambda.amazonaws.com")
        )

        construct = ExampleConstruct(
            scope=stack,
            construct_id="test-example",
            name="test-name",
        )

        construct.grant_access(role)

        assert construct.resource is not None
        assert role is not None
```

## Summary

These patterns ensure comprehensive, maintainable CDK tests that:
1. Validate infrastructure code without deploying
2. Cover all code paths for high coverage
3. Use consistent patterns across the test suite
4. Handle Docker builds appropriately
5. Mock external dependencies when needed
6. Achieve ≥90% code coverage target
