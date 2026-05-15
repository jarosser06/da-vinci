"""Unit tests for da_vinci_cdk.constructs.service module."""

import tempfile
from pathlib import Path

import pytest
from aws_cdk import Duration
from aws_cdk.assertions import Match, Template

from da_vinci_cdk.constructs.service import (
    APIGatewayRESTService,
    AsyncService,
    SimpleRESTService,
)


def _make_lambda_dir(tmpdir):
    """Populate a directory with a minimal Dockerfile and handler."""
    (Path(tmpdir) / "Dockerfile").write_text("""ARG IMAGE
FROM ${IMAGE}
ARG FUNCTION_INDEX
ARG FUNCTION_HANDLER
COPY ${FUNCTION_INDEX}.py ${LAMBDA_TASK_ROOT}
""")
    (Path(tmpdir) / "index.py").write_text("def handler(event, context):\n    pass\n")
    return tmpdir


class TestAsyncService:
    """Tests for AsyncService construct."""

    @pytest.fixture
    def temp_lambda_dir(self):
        """Create a temporary directory with a Dockerfile for Lambda tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield _make_lambda_dir(tmpdir)

    def test_async_service_wires_queue_to_handler(self, stack, temp_lambda_dir):
        """An AsyncService synthesizes one SQS queue, one Lambda function, and
        one event source mapping connecting them; the queue is named from the
        service name and its visibility timeout matches the handler timeout."""
        AsyncService(
            scope=stack,
            service_name="test-async",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            memory_size=256,
            timeout=Duration.seconds(60),
            base_image="public.ecr.aws/lambda/python:3.12",
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::Lambda::Function", 1)
        template.resource_count_is("AWS::SQS::Queue", 1)
        template.resource_count_is("AWS::Lambda::EventSourceMapping", 1)
        template.has_resource_properties(
            "AWS::SQS::Queue",
            {
                "QueueName": "test-app-test-deployment-test-async",
                "VisibilityTimeout": 60,
            },
        )
        template.has_resource_properties(
            "AWS::Lambda::Function", {"MemorySize": 256, "Timeout": 60}
        )

    def test_async_service_default_timeout_is_thirty_seconds(self, stack, temp_lambda_dir):
        """Without an explicit timeout the handler and the queue visibility
        timeout both default to 30 seconds."""
        AsyncService(
            scope=stack,
            service_name="test-async",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            base_image="public.ecr.aws/lambda/python:3.12",
        )

        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::Lambda::Function", {"Timeout": 30})
        template.has_resource_properties("AWS::SQS::Queue", {"VisibilityTimeout": 30})

    def test_async_service_visibility_timeout_tracks_custom_timeout(self, stack, temp_lambda_dir):
        """The queue visibility timeout is set equal to the custom handler
        timeout so in-flight messages are not redelivered mid-processing."""
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
        template.has_resource_properties("AWS::SQS::Queue", {"VisibilityTimeout": 120})

    def test_async_service_event_source_targets_the_queue(self, stack, temp_lambda_dir):
        """The event source mapping consumes the service's own SQS queue."""
        AsyncService(
            scope=stack,
            service_name="test-async",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            base_image="public.ecr.aws/lambda/python:3.12",
        )

        template = Template.from_stack(stack)
        # The mapping's source ARN is a GetAtt reference to the queue created by
        # this construct, and the function it targets is the handler.
        template.has_resource_properties(
            "AWS::Lambda::EventSourceMapping",
            {
                "EventSourceArn": {"Fn::GetAtt": Match.any_value()},
                "FunctionName": Match.any_value(),
            },
        )

    def test_async_service_handler_tagged_with_purpose(self, stack, temp_lambda_dir):
        """The handler carries the AsyncService function-purpose tag."""
        AsyncService(
            scope=stack,
            service_name="test-async",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            base_image="public.ecr.aws/lambda/python:3.12",
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "Tags": Match.array_with(
                    [
                        {
                            "Key": "DaVinciFramework::FunctionPurpose",
                            "Value": "AsyncService",
                        }
                    ]
                )
            },
        )


class TestSimpleRESTService:
    """Tests for SimpleRESTService construct."""

    @pytest.fixture
    def temp_lambda_dir(self):
        """Create a temporary directory with a Dockerfile for Lambda tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield _make_lambda_dir(tmpdir)

    def test_simple_rest_service_private_url_uses_iam_auth(self, stack, temp_lambda_dir):
        """A non-public SimpleRESTService creates a function with an AWS_IAM
        Function URL and a single resource-based permission scoping invocation
        to the deploying account."""
        SimpleRESTService(
            scope=stack,
            service_name="test-rest",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            base_image="public.ecr.aws/lambda/python:3.12",
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::Lambda::Function", 1)
        template.resource_count_is("AWS::Lambda::Url", 1)
        template.has_resource_properties("AWS::Lambda::Url", {"AuthType": "AWS_IAM"})
        # Exactly one permission, granting the account InvokeFunctionUrl.
        template.resource_count_is("AWS::Lambda::Permission", 1)
        template.has_resource_properties(
            "AWS::Lambda::Permission",
            {
                "Action": "lambda:InvokeFunctionUrl",
                "FunctionUrlAuthType": "AWS_IAM",
                "Principal": {"Ref": "AWS::AccountId"},
            },
        )

    def test_simple_rest_service_public_url_uses_none_auth(self, stack, temp_lambda_dir):
        """A public SimpleRESTService exposes a NONE-auth Function URL and adds
        public invoke permissions (Principal "*") for both InvokeFunctionUrl
        and the InvokedViaFunctionUrl-conditioned InvokeFunction."""
        SimpleRESTService(
            scope=stack,
            service_name="test-rest",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            public=True,
            base_image="public.ecr.aws/lambda/python:3.12",
        )

        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::Lambda::Url", {"AuthType": "NONE"})
        # Public URL adds two permissions, both open to all principals; the
        # account-scoped AWS_IAM permission is NOT added for a public service.
        template.resource_count_is("AWS::Lambda::Permission", 2)
        template.has_resource_properties(
            "AWS::Lambda::Permission",
            {
                "Action": "lambda:InvokeFunctionUrl",
                "FunctionUrlAuthType": "NONE",
                "Principal": "*",
            },
        )
        template.has_resource_properties(
            "AWS::Lambda::Permission",
            {
                "Action": "lambda:InvokeFunction",
                "Principal": "*",
            },
        )

    def test_simple_rest_service_with_memory(self, stack, temp_lambda_dir):
        """A custom memory size is propagated to the handler function."""
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

    def test_simple_rest_service_handler_tagged_with_purpose(self, stack, temp_lambda_dir):
        """The handler carries the SimpleRESTService function-purpose tag."""
        SimpleRESTService(
            scope=stack,
            service_name="test-rest",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            base_image="public.ecr.aws/lambda/python:3.12",
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "Tags": Match.array_with(
                    [
                        {
                            "Key": "DaVinciFramework::FunctionPurpose",
                            "Value": "SimpleRESTService",
                        }
                    ]
                )
            },
        )


class TestAPIGatewayRESTService:
    """Tests for APIGatewayRESTService construct."""

    def test_api_gateway_rest_service_creates_http_api(self, stack):
        """An APIGatewayRESTService synthesizes a single HTTP API named from the
        service name, with a default stage and no Lambda function."""
        APIGatewayRESTService(
            scope=stack,
            service_name="test-api",
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::ApiGatewayV2::Api", 1)
        template.resource_count_is("AWS::Lambda::Function", 0)
        template.has_resource_properties(
            "AWS::ApiGatewayV2::Api",
            {
                "Name": "test-app-test-deployment-test-api",
                "ProtocolType": "HTTP",
            },
        )
        template.resource_count_is("AWS::ApiGatewayV2::Stage", 1)

    def test_api_gateway_rest_service_subdomain_requires_root_domain(self, stack):
        """Requesting a subdomain without a root_domain_name in context raises
        a ValueError rather than silently producing a broken API."""
        with pytest.raises(ValueError, match="Root domain name must be set"):
            APIGatewayRESTService(
                scope=stack,
                service_name="test-api",
                subdomain_name="api",
            )
