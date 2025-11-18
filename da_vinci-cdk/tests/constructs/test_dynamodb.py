"""Unit tests for da_vinci_cdk.constructs.dynamodb module."""

from aws_cdk import RemovalPolicy
from aws_cdk.assertions import Template
from aws_cdk.aws_dynamodb import Attribute, AttributeType

from da_vinci.core.orm.table_object import TableObjectAttributeType
from da_vinci_cdk.constructs.dynamodb import DynamoDBTable


class TestDynamoDBTable:
    """Tests for DynamoDBTable construct."""

    def test_table_creation_basic(self, stack):
        """Test basic DynamoDB table creation."""
        table = DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
        )

        assert table is not None
        assert table.table is not None

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)

    def test_table_with_sort_key(self, stack):
        """Test DynamoDB table with sort key."""
        DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="pk", type=AttributeType.STRING),
            sort_key=Attribute(name="sk", type=AttributeType.STRING),
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::DynamoDB::GlobalTable",
            {
                "KeySchema": [
                    {"AttributeName": "pk", "KeyType": "HASH"},
                    {"AttributeName": "sk", "KeyType": "RANGE"},
                ]
            },
        )

    def test_table_with_billing_mode(self, stack):
        """Test DynamoDB table with PAY_PER_REQUEST billing mode (default)."""
        DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::DynamoDB::GlobalTable", {"BillingMode": "PAY_PER_REQUEST"}
        )

    def test_table_with_removal_policy(self, stack):
        """Test DynamoDB table with removal policy."""
        DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY,
        )

        template = Template.from_stack(stack)
        # Verify table was created
        template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)

    def test_grant_read_access(self, stack):
        """Test granting read access to a table."""
        from aws_cdk.aws_iam import Role, ServicePrincipal

        role = Role(stack, "TestRole", assumed_by=ServicePrincipal("lambda.amazonaws.com"))

        table = DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
        )

        table.grant_read_access(role)

        # Verify table was created and role exists
        assert table.table is not None
        assert role is not None

    def test_grant_read_write_access(self, stack):
        """Test granting read/write access to a table."""
        from aws_cdk.aws_iam import Role, ServicePrincipal

        role = Role(stack, "TestRole", assumed_by=ServicePrincipal("lambda.amazonaws.com"))

        table = DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
        )

        table.grant_read_write_access(role)

        # Verify table was created and role exists
        assert table.table is not None
        assert role is not None

    def test_attribute_type_from_orm_type(self):
        """Test attribute type conversion from ORM types."""
        assert (
            DynamoDBTable.attribute_type_from_orm_type(TableObjectAttributeType.STRING)
            == AttributeType.STRING
        )
        assert (
            DynamoDBTable.attribute_type_from_orm_type(TableObjectAttributeType.NUMBER)
            == AttributeType.NUMBER
        )
        assert (
            DynamoDBTable.attribute_type_from_orm_type(TableObjectAttributeType.DATETIME)
            == AttributeType.NUMBER
        )

    def test_attribute_type_from_orm_type_invalid(self):
        """Test attribute type conversion with invalid type."""
        # The function actually returns STRING for unknown types
        # so we test that it doesn't raise an error
        result = DynamoDBTable.attribute_type_from_orm_type("INVALID")
        # Should return STRING as default
        assert result == AttributeType.STRING

    def test_table_with_time_to_live(self, stack):
        """Test DynamoDB table with TTL attribute."""
        DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
            time_to_live_attribute="ttl",
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)

    def test_table_with_custom_construct_id(self, stack):
        """Test DynamoDB table with custom construct ID."""
        table = DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
            construct_id="custom-construct-id",
        )

        assert table is not None

    def test_table_with_tags(self, stack):
        """Test DynamoDB table with custom tags."""
        tags = [{"key": "Environment", "value": "Test"}]

        table = DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
            tags=tags,
        )

        assert table is not None

    def test_table_excluded_from_discovery(self, stack):
        """Test DynamoDB table excluded from discovery."""
        table = DynamoDBTable(
            scope=stack,
            table_name="test-table",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
            exclude_from_discovery=True,
        )

        assert table is not None

    def test_table_from_table_object(self, stack):
        """Test DynamoDBTable.from_orm_table_object static method."""
        from da_vinci.core.tables.resource_registry import ResourceRegistration

        table = DynamoDBTable.from_orm_table_object(
            scope=stack,
            table_object=ResourceRegistration,
        )

        assert table is not None
        assert table.table is not None

    def test_table_full_name_lookup_with_ssm(self, stack):
        """Test table_full_name_lookup with SSM storage."""
        from unittest.mock import patch

        from da_vinci.core.resource_discovery import ResourceDiscoveryStorageSolution

        with patch(
            "da_vinci_cdk.constructs.dynamodb.DiscoverableResource.read_endpoint"
        ) as mock_read:
            mock_read.return_value = "test-table-name"

            name = DynamoDBTable.table_full_name_lookup(
                scope=stack,
                table_name="test-table",
                resource_discovery_storage_solution=ResourceDiscoveryStorageSolution.SSM,
            )

            assert name == "test-table-name"

    def test_table_full_name_lookup_with_dynamodb(self, stack):
        """Test table_full_name_lookup with DynamoDB storage."""
        from aws_cdk import App, Stack

        from da_vinci.core.resource_discovery import ResourceDiscoveryStorageSolution

        app = App(
            context={
                "app_name": "test-app",
                "deployment_id": "test-deployment",
                "resource_discovery_storage_solution": ResourceDiscoveryStorageSolution.DYNAMODB,
                "resource_discovery_table_name": "resource-registry",
            }
        )
        test_stack = Stack(app, "TestStack")

        name = DynamoDBTable.table_full_name_lookup(
            scope=test_stack,
            table_name="test-table",
            resource_discovery_storage_solution=ResourceDiscoveryStorageSolution.DYNAMODB,
        )

        # Should return a token
        assert name is not None
