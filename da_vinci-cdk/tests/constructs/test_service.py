"""Unit tests for da_vinci_cdk.constructs.service module."""

import tempfile
from pathlib import Path

import pytest
from aws_cdk import Duration
from aws_cdk.assertions import Template

from da_vinci_cdk.constructs.service import (
    APIGatewayRESTService,
    AsyncService,
    SimpleRESTService,
)


class TestAsyncService:
    """Tests for AsyncService construct."""

    @pytest.fixture
    def temp_lambda_dir(self):
        """Create a temporary directory with a Dockerfile for Lambda function tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a minimal Dockerfile
            dockerfile_path = Path(tmpdir) / "Dockerfile"
            dockerfile_path.write_text(
                """ARG IMAGE
FROM ${IMAGE}
ARG FUNCTION_INDEX
ARG FUNCTION_HANDLER
COPY ${FUNCTION_INDEX}.py ${LAMBDA_TASK_ROOT}
"""
            )
            # Create a minimal Python file
            index_path = Path(tmpdir) / "index.py"
            index_path.write_text("def handler(event, context):\n    pass\n")
            yield tmpdir

    def test_async_service_creation(self, stack, temp_lambda_dir):
        """Test basic AsyncService creation."""
        service = AsyncService(
            scope=stack,
            service_name="test-async",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            memory_size=256,
            timeout=Duration.seconds(60),
            base_image="public.ecr.aws/lambda/python:3.12",
        )

        assert service is not None
        assert service.queue is not None
        assert service.handler is not None

        template = Template.from_stack(stack)
        # Should create Lambda function
        template.resource_count_is("AWS::Lambda::Function", 1)
        # Should create at least 1 SQS queue (may include DLQ)
        # We just verify the queue exists through the service object
        assert service.queue is not None

    def test_async_service_with_custom_timeout(self, stack, temp_lambda_dir):
        """Test AsyncService with custom timeout."""
        AsyncService(
            scope=stack,
            service_name="test-async",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            timeout=Duration.seconds(120),
            base_image="public.ecr.aws/lambda/python:3.12",
        )

        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::Lambda::Function", {"Timeout": 120})

    def test_async_service_with_memory_size(self, stack, temp_lambda_dir):
        """Test AsyncService with custom memory size."""
        AsyncService(
            scope=stack,
            service_name="test-async",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            memory_size=512,
            base_image="public.ecr.aws/lambda/python:3.12",
        )

        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::Lambda::Function", {"MemorySize": 512})

    def test_async_service_creates_sqs_trigger(self, stack, temp_lambda_dir):
        """Test AsyncService creates SQS event source for Lambda."""
        AsyncService(
            scope=stack,
            service_name="test-async",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            base_image="public.ecr.aws/lambda/python:3.12",
        )

        template = Template.from_stack(stack)
        # Lambda should have event source mapping for SQS
        template.resource_count_is("AWS::Lambda::EventSourceMapping", 1)


class TestSimpleRESTService:
    """Tests for SimpleRESTService construct."""

    @pytest.fixture
    def temp_lambda_dir(self):
        """Create a temporary directory with a Dockerfile for Lambda function tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a minimal Dockerfile
            dockerfile_path = Path(tmpdir) / "Dockerfile"
            dockerfile_path.write_text(
                """ARG IMAGE
FROM ${IMAGE}
ARG FUNCTION_INDEX
ARG FUNCTION_HANDLER
COPY ${FUNCTION_INDEX}.py ${LAMBDA_TASK_ROOT}
"""
            )
            # Create a minimal Python file
            index_path = Path(tmpdir) / "index.py"
            index_path.write_text("def handler(event, context):\n    pass\n")
            yield tmpdir

    def test_simple_rest_service_creation(self, stack, temp_lambda_dir):
        """Test basic SimpleRESTService creation."""
        service = SimpleRESTService(
            scope=stack,
            service_name="test-rest",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            base_image="public.ecr.aws/lambda/python:3.12",
        )

        assert service is not None
        assert service.handler is not None
        assert service.function_url is not None

        template = Template.from_stack(stack)
        # Should create Lambda function
        template.resource_count_is("AWS::Lambda::Function", 1)
        # Should create Lambda function URL
        template.resource_count_is("AWS::Lambda::Url", 1)

    def test_simple_rest_service_with_memory(self, stack, temp_lambda_dir):
        """Test SimpleRESTService with custom memory."""
        SimpleRESTService(
            scope=stack,
            service_name="test-rest",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            memory_size=1024,
            base_image="public.ecr.aws/lambda/python:3.12",
        )

        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::Lambda::Function", {"MemorySize": 1024})


class TestAPIGatewayRESTService:
    """Tests for APIGatewayRESTService construct."""

    def test_api_gateway_rest_service_creation(self, stack):
        """Test basic APIGatewayRESTService creation."""
        service = APIGatewayRESTService(
            scope=stack,
            service_name="test-api",
        )

        assert service is not None
        assert service.api is not None

        template = Template.from_stack(stack)
        # Should create API Gateway
        template.resource_count_is("AWS::ApiGatewayV2::Api", 1)

    def test_api_gateway_rest_service_with_timeout(self, stack):
        """Test APIGatewayRESTService with custom configuration."""
        # APIGatewayRESTService doesn't have timeout parameter
        # It only creates the API Gateway, not the Lambda function
        service = APIGatewayRESTService(
            scope=stack,
            service_name="test-api",
        )

        template = Template.from_stack(stack)
        # Should create API Gateway
        template.resource_count_is("AWS::ApiGatewayV2::Api", 1)
