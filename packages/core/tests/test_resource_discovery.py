"""Tests for resource discovery functionality."""

import time

import pytest
from moto import mock_aws

from da_vinci.core.exceptions import ResourceNotFoundError
from da_vinci.core.resource_discovery import (
    CACHE_TTL,
    ResourceDiscovery,
    ResourceDiscoveryStorageSolution,
    ResourceType,
    cache,
    cache_timestamps,
)


@pytest.mark.unit
class TestResourceType:
    """Test ResourceType enum."""

    def test_resource_types_exist(self):
        """Test that all expected resource types are defined."""
        assert ResourceType.ASYNC_SERVICE == "async_service"
        assert ResourceType.BUCKET == "bucket"
        assert ResourceType.DOMAIN == "domain"
        assert ResourceType.REST_SERVICE == "rest_service"
        assert ResourceType.TABLE == "table"


@pytest.mark.unit
class TestResourceDiscoveryStorageSolution:
    """Test ResourceDiscoveryStorageSolution enum."""

    def test_storage_solutions_exist(self):
        """Test that all expected storage solutions are defined."""
        assert ResourceDiscoveryStorageSolution.DYNAMODB == "dynamodb"
        assert ResourceDiscoveryStorageSolution.SSM == "ssm"


@pytest.mark.unit
class TestResourceDiscoveryInit:
    """Test ResourceDiscovery initialization."""

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters provided."""
        rd = ResourceDiscovery(
            resource_type=ResourceType.TABLE,
            resource_name="test-table",
            app_name="test-app",
            deployment_id="test-deployment",
            storage_solution=ResourceDiscoveryStorageSolution.DYNAMODB,
        )

        assert rd.resource_type == ResourceType.TABLE
        assert rd.resource_name == "test-table"
        assert rd.app_name == "test-app"
        assert rd.deployment_id == "test-deployment"
        assert rd.storage_solution == ResourceDiscoveryStorageSolution.DYNAMODB

    def test_init_loads_from_environment(self, mock_environment):
        """Test initialization loads missing values from environment."""
        rd = ResourceDiscovery(
            resource_type=ResourceType.REST_SERVICE,
            resource_name="test-service",
        )

        assert rd.resource_type == ResourceType.REST_SERVICE
        assert rd.resource_name == "test-service"
        assert rd.app_name == "test-app"
        assert rd.deployment_id == "test-deployment"
        assert rd.storage_solution == ResourceDiscoveryStorageSolution.DYNAMODB

    def test_init_with_string_resource_type(self):
        """Test initialization with string resource type."""
        rd = ResourceDiscovery(
            resource_type="table",
            resource_name="test-table",
            app_name="test-app",
            deployment_id="test-deployment",
            storage_solution=ResourceDiscoveryStorageSolution.DYNAMODB,
        )

        assert rd.resource_type == "table"
        assert rd.resource_name == "test-table"


@pytest.mark.unit
class TestSSMParameterName:
    """Test SSM parameter name generation."""

    def test_ssm_parameter_name_format(self):
        """Test SSM parameter name format."""
        param_name = ResourceDiscovery.ssm_parameter_name(
            resource_type=ResourceType.TABLE,
            resource_name="test-table",
            app_name="myapp",
            deployment_id="prod",
        )

        expected = "/da_vinci_framework/service_discovery/myapp/prod/table/test-table"
        assert param_name == expected

    def test_ssm_parameter_name_with_different_types(self):
        """Test SSM parameter name with different resource types."""
        types_to_test = [
            (ResourceType.ASYNC_SERVICE, "async_service"),
            (ResourceType.REST_SERVICE, "rest_service"),
            (ResourceType.BUCKET, "bucket"),
        ]

        for resource_type, type_str in types_to_test:
            param_name = ResourceDiscovery.ssm_parameter_name(
                resource_type=resource_type,
                resource_name="test-resource",
                app_name="app",
                deployment_id="deploy",
            )

            assert f"/{type_str}/" in param_name


@pytest.mark.unit
@mock_aws
class TestSSMResourceLookup:
    """Test SSM-based resource discovery."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test."""
        cache.clear()
        cache_timestamps.clear()
        yield
        cache.clear()
        cache_timestamps.clear()

    def test_ssm_lookup_success(self, aws_credentials, ssm_client):
        """Test successful SSM parameter lookup."""
        # Create SSM parameter
        param_name = "/da_vinci_framework/service_discovery/test-app/test-deployment/table/test-table"
        ssm_client.put_parameter(
            Name=param_name,
            Value="arn:aws:dynamodb:us-east-1:123456789012:table/test-table",
            Type="String",
        )

        rd = ResourceDiscovery(
            resource_type=ResourceType.TABLE,
            resource_name="test-table",
            app_name="test-app",
            deployment_id="test-deployment",
            storage_solution=ResourceDiscoveryStorageSolution.SSM,
        )

        endpoint = rd.endpoint_lookup()
        assert endpoint == "arn:aws:dynamodb:us-east-1:123456789012:table/test-table"

    def test_ssm_lookup_not_found(self, aws_credentials, ssm_client):
        """Test SSM parameter lookup when parameter doesn't exist."""
        rd = ResourceDiscovery(
            resource_type=ResourceType.TABLE,
            resource_name="nonexistent-table",
            app_name="test-app",
            deployment_id="test-deployment",
            storage_solution=ResourceDiscoveryStorageSolution.SSM,
        )

        with pytest.raises(ResourceNotFoundError) as exc_info:
            rd.endpoint_lookup()

        assert "nonexistent-table" in str(exc_info.value)

    def test_ssm_lookup_uses_cache(self, aws_credentials, ssm_client):
        """Test that SSM lookup uses cache on second call."""
        # Create SSM parameter
        param_name = "/da_vinci_framework/service_discovery/test-app/test-deployment/table/cached-table"
        ssm_client.put_parameter(
            Name=param_name,
            Value="test-endpoint",
            Type="String",
        )

        rd = ResourceDiscovery(
            resource_type=ResourceType.TABLE,
            resource_name="cached-table",
            app_name="test-app",
            deployment_id="test-deployment",
            storage_solution=ResourceDiscoveryStorageSolution.SSM,
        )

        # First call - cache miss
        endpoint1 = rd.endpoint_lookup()
        assert endpoint1 == "test-endpoint"
        assert param_name in cache

        # Delete the parameter to prove cache is being used
        ssm_client.delete_parameter(Name=param_name)

        # Second call - should use cache
        endpoint2 = rd.endpoint_lookup()
        assert endpoint2 == "test-endpoint"

    def test_ssm_cache_expires(self, aws_credentials, ssm_client, monkeypatch):
        """Test that SSM cache expires after TTL."""
        # Create SSM parameter
        param_name = "/da_vinci_framework/service_discovery/test-app/test-deployment/table/expire-test"
        ssm_client.put_parameter(
            Name=param_name,
            Value="original-endpoint",
            Type="String",
        )

        rd = ResourceDiscovery(
            resource_type=ResourceType.TABLE,
            resource_name="expire-test",
            app_name="test-app",
            deployment_id="test-deployment",
            storage_solution=ResourceDiscoveryStorageSolution.SSM,
        )

        # First call
        endpoint1 = rd.endpoint_lookup()
        assert endpoint1 == "original-endpoint"

        # Update parameter
        ssm_client.put_parameter(
            Name=param_name,
            Value="updated-endpoint",
            Type="String",
            Overwrite=True,
        )

        # Simulate time passing beyond cache TTL
        original_time = time.time
        monkeypatch.setattr(time, "time", lambda: original_time() + CACHE_TTL + 1)

        # Second call should fetch new value
        endpoint2 = rd.endpoint_lookup()
        assert endpoint2 == "updated-endpoint"


@pytest.mark.unit
@mock_aws
class TestDynamoDBResourceLookup:
    """Test DynamoDB-based resource discovery."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test."""
        cache.clear()
        cache_timestamps.clear()
        yield
        cache.clear()
        cache_timestamps.clear()

    def test_dynamodb_lookup_success(
        self, aws_credentials, resource_registry_table, mock_environment
    ):
        """Test successful DynamoDB resource lookup."""
        # Insert resource registration (use capitalized attribute names)
        resource_registry_table.put_item(
            Item={
                "ResourceType": "table",
                "ResourceName": "test-table",
                "Endpoint": "arn:aws:dynamodb:us-east-1:123456789012:table/test-table",
            }
        )

        rd = ResourceDiscovery(
            resource_type=ResourceType.TABLE,
            resource_name="test-table",
            app_name="test-app",
            deployment_id="test-deployment",
            storage_solution=ResourceDiscoveryStorageSolution.DYNAMODB,
        )

        endpoint = rd.endpoint_lookup()
        assert endpoint == "arn:aws:dynamodb:us-east-1:123456789012:table/test-table"

    def test_dynamodb_lookup_not_found(
        self, aws_credentials, resource_registry_table, mock_environment
    ):
        """Test DynamoDB resource lookup when resource doesn't exist."""
        rd = ResourceDiscovery(
            resource_type=ResourceType.TABLE,
            resource_name="nonexistent-table",
            app_name="test-app",
            deployment_id="test-deployment",
            storage_solution=ResourceDiscoveryStorageSolution.DYNAMODB,
        )

        with pytest.raises(ResourceNotFoundError) as exc_info:
            rd.endpoint_lookup()

        assert "nonexistent-table" in str(exc_info.value)

    def test_dynamodb_lookup_uses_cache(
        self, aws_credentials, resource_registry_table, mock_environment
    ):
        """Test that DynamoDB lookup uses cache on second call."""
        # Insert resource registration (use capitalized attribute names)
        resource_registry_table.put_item(
            Item={
                "ResourceType": "table",
                "ResourceName": "cached-table",
                "Endpoint": "test-endpoint",
            }
        )

        rd = ResourceDiscovery(
            resource_type=ResourceType.TABLE,
            resource_name="cached-table",
            app_name="test-app",
            deployment_id="test-deployment",
            storage_solution=ResourceDiscoveryStorageSolution.DYNAMODB,
        )

        # First call - cache miss
        endpoint1 = rd.endpoint_lookup()
        assert endpoint1 == "test-endpoint"

        cache_key = "dynamodb:table:cached-table"
        assert cache_key in cache

        # Delete the item to prove cache is being used
        resource_registry_table.delete_item(
            Key={"ResourceType": "table", "ResourceName": "cached-table"}
        )

        # Second call - should use cache
        endpoint2 = rd.endpoint_lookup()
        assert endpoint2 == "test-endpoint"

    def test_dynamodb_cache_expires(
        self, aws_credentials, resource_registry_table, mock_environment, monkeypatch
    ):
        """Test that DynamoDB cache expires after TTL."""
        # Insert resource registration (use capitalized attribute names)
        resource_registry_table.put_item(
            Item={
                "ResourceType": "table",
                "ResourceName": "expire-test",
                "Endpoint": "original-endpoint",
            }
        )

        rd = ResourceDiscovery(
            resource_type=ResourceType.TABLE,
            resource_name="expire-test",
            app_name="test-app",
            deployment_id="test-deployment",
            storage_solution=ResourceDiscoveryStorageSolution.DYNAMODB,
        )

        # First call
        endpoint1 = rd.endpoint_lookup()
        assert endpoint1 == "original-endpoint"

        # Update item (use capitalized attribute names)
        resource_registry_table.put_item(
            Item={
                "ResourceType": "table",
                "ResourceName": "expire-test",
                "Endpoint": "updated-endpoint",
            }
        )

        # Simulate time passing beyond cache TTL
        original_time = time.time
        monkeypatch.setattr(time, "time", lambda: original_time() + CACHE_TTL + 1)

        # Second call should fetch new value
        endpoint2 = rd.endpoint_lookup()
        assert endpoint2 == "updated-endpoint"


@pytest.mark.integration
@mock_aws
class TestResourceDiscoveryIntegration:
    """Integration tests for resource discovery with multiple scenarios."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test."""
        cache.clear()
        cache_timestamps.clear()
        yield
        cache.clear()
        cache_timestamps.clear()

    def test_multiple_resources_different_types(
        self, aws_credentials, resource_registry_table, mock_environment
    ):
        """Test discovering multiple resources of different types."""
        # Insert multiple resources (use capitalized attribute names)
        resources = [
            ("table", "users-table", "arn:aws:dynamodb:table/users"),
            ("rest_service", "api-gateway", "https://api.example.com"),
            ("bucket", "data-bucket", "s3://my-data-bucket"),
        ]

        for resource_type, resource_name, endpoint in resources:
            resource_registry_table.put_item(
                Item={
                    "ResourceType": resource_type,
                    "ResourceName": resource_name,
                    "Endpoint": endpoint,
                }
            )

        # Lookup each resource
        for resource_type, resource_name, expected_endpoint in resources:
            rd = ResourceDiscovery(
                resource_type=resource_type,
                resource_name=resource_name,
                app_name="test-app",
                deployment_id="test-deployment",
                storage_solution=ResourceDiscoveryStorageSolution.DYNAMODB,
            )

            endpoint = rd.endpoint_lookup()
            assert endpoint == expected_endpoint

    def test_mixed_storage_solutions(
        self, aws_credentials, ssm_client, resource_registry_table, mock_environment
    ):
        """Test using both SSM and DynamoDB storage solutions."""
        # Create SSM parameter
        ssm_param_name = "/da_vinci_framework/service_discovery/test-app/test-deployment/table/ssm-table"
        ssm_client.put_parameter(
            Name=ssm_param_name,
            Value="ssm-endpoint",
            Type="String",
        )

        # Create DynamoDB item (use capitalized attribute names)
        resource_registry_table.put_item(
            Item={
                "ResourceType": "table",
                "ResourceName": "dynamodb-table",
                "Endpoint": "dynamodb-endpoint",
            }
        )

        # Lookup from SSM
        rd_ssm = ResourceDiscovery(
            resource_type=ResourceType.TABLE,
            resource_name="ssm-table",
            app_name="test-app",
            deployment_id="test-deployment",
            storage_solution=ResourceDiscoveryStorageSolution.SSM,
        )
        assert rd_ssm.endpoint_lookup() == "ssm-endpoint"

        # Lookup from DynamoDB
        rd_dynamodb = ResourceDiscovery(
            resource_type=ResourceType.TABLE,
            resource_name="dynamodb-table",
            app_name="test-app",
            deployment_id="test-deployment",
            storage_solution=ResourceDiscoveryStorageSolution.DYNAMODB,
        )
        assert rd_dynamodb.endpoint_lookup() == "dynamodb-endpoint"
