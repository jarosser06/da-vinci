"""Shared pytest fixtures for da_vinci tests."""

import os
from typing import Any
from unittest.mock import MagicMock

import boto3
import pytest
from moto import mock_aws


@pytest.fixture(scope="function")
def aws_credentials():
    """Mock AWS credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    yield
    # Clean up after test
    for key in [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SECURITY_TOKEN",
        "AWS_SESSION_TOKEN",
    ]:
        os.environ.pop(key, None)


@pytest.fixture(scope="function")
def mock_environment():
    """Mock common Da Vinci environment variables."""
    env_vars = {
        "DA_VINCI_APP_NAME": "test-app",
        "DA_VINCI_DEPLOYMENT_ID": "test-deployment",
        "DA_VINCI_RESOURCE_DISCOVERY_STORAGE": "dynamodb",
        "LOG_LEVEL": "INFO",
    }

    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value

    yield env_vars

    # Clean up
    for key in env_vars:
        os.environ.pop(key, None)


@pytest.fixture(scope="function")
def dynamodb_client(aws_credentials):
    """Create a mocked DynamoDB client."""
    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        yield client


@pytest.fixture(scope="function")
def dynamodb_resource(aws_credentials):
    """Create a mocked DynamoDB resource."""
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="us-east-1")
        yield resource


@pytest.fixture(scope="function")
def dynamodb_table(dynamodb_resource):
    """Create a mocked DynamoDB table with a standard schema."""
    table = dynamodb_resource.create_table(
        TableName="test-table",
        KeySchema=[
            {"AttributeName": "Pk", "KeyType": "HASH"},
            {"AttributeName": "Sk", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "Pk", "AttributeType": "S"},
            {"AttributeName": "Sk", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.meta.client.get_waiter("table_exists").wait(TableName="test-table")
    yield table


@pytest.fixture(scope="function")
def global_settings_table(dynamodb_resource):
    """Create a mocked global settings table."""
    table = dynamodb_resource.create_table(
        TableName="da_vinci_global_settings",
        KeySchema=[
            {"AttributeName": "namespace", "KeyType": "HASH"},
            {"AttributeName": "setting_key", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "namespace", "AttributeType": "S"},
            {"AttributeName": "setting_key", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.meta.client.get_waiter("table_exists").wait(TableName="da_vinci_global_settings")
    yield table


@pytest.fixture(scope="function")
def resource_registry_table(dynamodb_resource):
    """Create a mocked resource registry table with standard naming."""
    # Use standard naming convention: app_name-deployment_id-table_name
    # Note: DynamoDB attribute names are capitalized by the ORM
    table_name = "test-app-test-deployment-da_vinci_resource_registry"
    table = dynamodb_resource.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "ResourceType", "KeyType": "HASH"},
            {"AttributeName": "ResourceName", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "ResourceType", "AttributeType": "S"},
            {"AttributeName": "ResourceName", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.meta.client.get_waiter("table_exists").wait(TableName=table_name)
    yield table


@pytest.fixture(scope="function")
def ssm_client(aws_credentials):
    """Create a mocked SSM client."""
    with mock_aws():
        client = boto3.client("ssm", region_name="us-east-1")
        yield client


@pytest.fixture(scope="function")
def sqs_client(aws_credentials):
    """Create a mocked SQS client."""
    with mock_aws():
        client = boto3.client("sqs", region_name="us-east-1")
        yield client


@pytest.fixture(scope="function")
def logs_client(aws_credentials):
    """Create a mocked CloudWatch Logs client."""
    with mock_aws():
        client = boto3.client("logs", region_name="us-east-1")
        yield client


@pytest.fixture(scope="function")
def mock_logger():
    """Create a mock logger for testing."""
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.critical = MagicMock()
    return logger


@pytest.fixture(scope="function")
def sample_table_items() -> list[dict[str, Any]]:
    """Sample items for testing table operations."""
    return [
        {"pk": "item-1", "sk": "metadata", "value": "test-value-1", "count": 10},
        {"pk": "item-2", "sk": "metadata", "value": "test-value-2", "count": 20},
        {"pk": "item-3", "sk": "metadata", "value": "test-value-3", "count": 30},
    ]


@pytest.fixture(scope="function")
def populated_table(dynamodb_table, sample_table_items):
    """Create a table pre-populated with test data."""
    for item in sample_table_items:
        dynamodb_table.put_item(Item=item)
    yield dynamodb_table


@pytest.fixture(scope="function")
def mock_sqs_queue(sqs_client):
    """Create a mocked SQS queue."""
    queue_name = "test-queue"
    response = sqs_client.create_queue(QueueName=queue_name)
    queue_url = response["QueueUrl"]
    yield {"name": queue_name, "url": queue_url, "client": sqs_client}


@pytest.fixture(scope="function")
def mock_ssm_parameters(ssm_client):
    """Pre-populate SSM with test parameters."""
    parameters = {
        "/da_vinci_framework/service_discovery/test-app/test-deployment/test-service": "test-endpoint",
        "/da_vinci_framework/service_discovery/test-app/test-deployment/test-table": "arn:aws:dynamodb:us-east-1:123456789012:table/test-table",
    }

    for name, value in parameters.items():
        ssm_client.put_parameter(Name=name, Value=value, Type="String")

    yield {"client": ssm_client, "parameters": parameters}
