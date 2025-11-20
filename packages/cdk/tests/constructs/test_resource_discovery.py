"""Unit tests for da_vinci_cdk.constructs.resource_discovery module."""

from unittest.mock import patch

import pytest
from aws_cdk import App, Stack

from da_vinci.core.resource_discovery import ResourceDiscoveryStorageSolution, ResourceType
from da_vinci_cdk.constructs.resource_discovery import (
    DiscoverableResource,
    DiscoverableResourceDynamoDBItem,
    DiscoverableResourceDynamoDBLookup,
)


class TestDiscoverableResourceDynamoDBItem:
    """Tests for DiscoverableResourceDynamoDBItem construct."""

    def test_dynamodb_item_creation(self):
        """Test DiscoverableResourceDynamoDBItem creation."""
        app = App(
            context={
                "app_name": "test-app",
                "deployment_id": "test-deployment",
                "resource_discovery_table_name": "resource-registry",
            }
        )
        stack = Stack(app, "TestStack")

        item = DiscoverableResourceDynamoDBItem(
            construct_id="test-item",
            scope=stack,
            endpoint="test-endpoint",
            registration_name="test-resource",
            registration_type="TEST_TYPE",
        )

        assert item is not None
        assert item.registration_obj is not None

    def test_dynamodb_item_physical_resource_id(self):
        """Test physical_resource_id static method."""
        from da_vinci.core.tables.resource_registry import ResourceRegistration

        registration = ResourceRegistration(
            endpoint="test-endpoint",
            resource_name="test-resource",
            resource_type="TEST_TYPE",
        )

        physical_id = DiscoverableResourceDynamoDBItem.physical_resource_id(registration)
        assert physical_id is not None

    def test_dynamodb_item_is_attribute_changed(self):
        """Test is_attribute_changed static method."""
        # Test when attribute is changed
        old_item_call = {"Item": {"test_attr": {"S": "old_value"}}}
        assert DiscoverableResourceDynamoDBItem.is_attribute_changed(
            "test_attr", {"S": "new_value"}, old_item_call
        )

        # Test when attribute is not changed
        old_item_call = {"Item": {"test_attr": {"S": "same_value"}}}
        assert not DiscoverableResourceDynamoDBItem.is_attribute_changed(
            "test_attr", {"S": "same_value"}, old_item_call
        )

        # Test when attribute is missing in old item
        old_item_call = {"Item": {}}
        assert DiscoverableResourceDynamoDBItem.is_attribute_changed(
            "test_attr", {"S": "new_value"}, old_item_call
        )

        # Test exception handling
        assert DiscoverableResourceDynamoDBItem.is_attribute_changed(
            "test_attr", {"S": "new_value"}, None
        )

    def test_dynamodb_item_access_statement(self):
        """Test access_statement method."""
        app = App(
            context={
                "app_name": "test-app",
                "deployment_id": "test-deployment",
                "resource_discovery_table_name": "resource-registry",
            }
        )
        stack = Stack(app, "TestStack")

        item = DiscoverableResourceDynamoDBItem(
            construct_id="test-item",
            scope=stack,
            endpoint="test-endpoint",
            registration_name="test-resource",
            registration_type="TEST_TYPE",
        )

        statement = item.access_statement()
        assert statement is not None
        assert statement.to_json()["Action"] == "dynamodb:GetItem"


class TestDiscoverableResourceDynamoDBLookup:
    """Tests for DiscoverableResourceDynamoDBLookup construct."""

    def test_dynamodb_lookup_creation(self):
        """Test DiscoverableResourceDynamoDBLookup creation."""
        app = App(
            context={
                "app_name": "test-app",
                "deployment_id": "test-deployment",
            }
        )
        stack = Stack(app, "TestStack")

        lookup = DiscoverableResourceDynamoDBLookup(
            scope=stack,
            construct_id="test-lookup",
            resource_name="test-resource",
            resource_type="TEST_TYPE",
            table_name="test-table",
        )

        assert lookup is not None
        assert lookup.resource_name == "test-resource"
        assert lookup.resource_type == "TEST_TYPE"

    def test_dynamodb_lookup_get_endpoint(self):
        """Test get_endpoint method."""
        app = App(
            context={
                "app_name": "test-app",
                "deployment_id": "test-deployment",
            }
        )
        stack = Stack(app, "TestStack")

        lookup = DiscoverableResourceDynamoDBLookup(
            scope=stack,
            construct_id="test-lookup",
            resource_name="test-resource",
            resource_type="TEST_TYPE",
            table_name="test-table",
        )

        # The method returns a token, so we just verify it doesn't raise
        endpoint = lookup.get_endpoint()
        assert endpoint is not None


class TestDiscoverableResource:
    """Tests for DiscoverableResource construct."""

    def test_discoverable_resource_with_ssm(self, stack):
        """Test DiscoverableResource with SSM storage."""
        resource = DiscoverableResource(
            construct_id="test-resource",
            scope=stack,
            resource_endpoint="test-endpoint",
            resource_name="test-resource",
            resource_type=ResourceType.BUCKET,
        )

        assert resource is not None
        assert resource.resource_name == "test-resource"
        assert resource.resource_endpoint == "test-endpoint"

    def test_discoverable_resource_with_dynamodb(self):
        """Test DiscoverableResource with DynamoDB storage."""
        app = App(
            context={
                "app_name": "test-app",
                "deployment_id": "test-deployment",
                "resource_discovery_storage_solution": ResourceDiscoveryStorageSolution.DYNAMODB,
                "resource_discovery_table_name": "resource-registry",
            }
        )
        stack = Stack(app, "TestStack")

        resource = DiscoverableResource(
            construct_id="test-resource",
            scope=stack,
            resource_endpoint="test-endpoint",
            resource_name="test-resource",
            resource_type=ResourceType.BUCKET,
        )

        assert resource is not None
        assert hasattr(resource, "dynamodb_item")

    def test_discoverable_resource_with_explicit_params(self, stack):
        """Test DiscoverableResource with explicit app_name and deployment_id."""
        resource = DiscoverableResource(
            construct_id="test-resource",
            scope=stack,
            resource_endpoint="test-endpoint",
            resource_name="test-resource",
            resource_type=ResourceType.BUCKET,
            app_name="explicit-app",
            deployment_id="explicit-deployment",
        )

        assert resource is not None
        assert resource.app_name == "explicit-app"
        assert resource.deployment_id == "explicit-deployment"

    def test_discoverable_resource_with_explicit_storage_solution(self, stack):
        """Test DiscoverableResource with explicit storage solution."""
        resource = DiscoverableResource(
            construct_id="test-resource",
            scope=stack,
            resource_endpoint="test-endpoint",
            resource_name="test-resource",
            resource_type=ResourceType.BUCKET,
            resource_discovery_storage_solution=ResourceDiscoveryStorageSolution.SSM,
        )

        assert resource is not None
        assert resource.storage_solution == ResourceDiscoveryStorageSolution.SSM

    def test_gen_ssm_parameter_name(self):
        """Test _gen_ssm_parameter_name static method."""
        param_name = DiscoverableResource._gen_ssm_parameter_name(
            app_name="test-app",
            deployment_id="test-deployment",
            resource_name="test-resource",
            resource_type="TEST_TYPE",
        )

        assert param_name is not None
        assert "test-app" in param_name
        assert "test-deployment" in param_name

    @patch("da_vinci_cdk.constructs.resource_discovery.GlobalVariable.load_variable")
    def test_read_endpoint_with_ssm(self, mock_load_variable, stack):
        """Test read_endpoint with SSM storage."""
        mock_load_variable.return_value = "test-endpoint"

        endpoint = DiscoverableResource.read_endpoint(
            resource_name="test-resource",
            resource_type=ResourceType.BUCKET,
            scope=stack,
            storage_solution=ResourceDiscoveryStorageSolution.SSM,
        )

        assert endpoint == "test-endpoint"
        mock_load_variable.assert_called_once()

    def test_read_endpoint_with_dynamodb(self):
        """Test read_endpoint with DynamoDB storage."""
        app = App(
            context={
                "app_name": "test-app",
                "deployment_id": "test-deployment",
                "resource_discovery_storage_solution": ResourceDiscoveryStorageSolution.DYNAMODB,
                "resource_discovery_table_name": "resource-registry",
            }
        )
        stack = Stack(app, "TestStack")

        # This should create a lookup construct
        endpoint = DiscoverableResource.read_endpoint(
            resource_name="test-resource",
            resource_type=ResourceType.BUCKET,
            scope=stack,
            storage_solution=ResourceDiscoveryStorageSolution.DYNAMODB,
        )

        # Endpoint should be a token
        assert endpoint is not None

    def test_read_endpoint_missing_table_name_raises_error(self):
        """Test read_endpoint raises error when table_name is missing for DynamoDB."""
        app = App(
            context={
                "app_name": "test-app",
                "deployment_id": "test-deployment",
                "resource_discovery_storage_solution": ResourceDiscoveryStorageSolution.DYNAMODB,
            }
        )
        stack = Stack(app, "TestStack")

        with pytest.raises(RuntimeError, match="Failed to look up resource"):
            DiscoverableResource.read_endpoint(
                resource_name="test-resource",
                resource_type=ResourceType.BUCKET,
                scope=stack,
                storage_solution=ResourceDiscoveryStorageSolution.DYNAMODB,
            )

    def test_read_endpoint_missing_required_args_raises_error(self):
        """Test read_endpoint raises error when required args are missing."""
        # Create a stack without context values
        app = App()
        stack = Stack(app, "TestStack")

        # This now raises RuntimeError due to context lookup failure
        with pytest.raises((ValueError, RuntimeError)):
            DiscoverableResource.read_endpoint(
                resource_name="test-resource",
                resource_type=ResourceType.BUCKET,
                scope=stack,
                app_name=None,
            )

    def test_grant_read_with_ssm(self, stack):
        """Test grant_read with SSM storage."""
        from aws_cdk.aws_iam import Role, ServicePrincipal

        role = Role(stack, "TestRole", assumed_by=ServicePrincipal("lambda.amazonaws.com"))

        resource = DiscoverableResource(
            construct_id="test-resource",
            scope=stack,
            resource_endpoint="test-endpoint",
            resource_name="test-resource",
            resource_type=ResourceType.BUCKET,
        )

        resource.grant_read(role)
        # Just verify it doesn't raise an error

    def test_grant_read_with_dynamodb(self):
        """Test grant_read with DynamoDB storage."""
        from aws_cdk.aws_iam import Role, ServicePrincipal

        app = App(
            context={
                "app_name": "test-app",
                "deployment_id": "test-deployment",
                "resource_discovery_storage_solution": ResourceDiscoveryStorageSolution.DYNAMODB,
                "resource_discovery_table_name": "resource-registry",
            }
        )
        stack = Stack(app, "TestStack")

        role = Role(stack, "TestRole", assumed_by=ServicePrincipal("lambda.amazonaws.com"))

        resource = DiscoverableResource(
            construct_id="test-resource",
            scope=stack,
            resource_endpoint="test-endpoint",
            resource_name="test-resource",
            resource_type=ResourceType.BUCKET,
        )

        resource.grant_read(role)
        # Just verify it doesn't raise an error
