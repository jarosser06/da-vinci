"""Unit tests for da_vinci_cdk.constructs.lambda_function module."""

import tempfile
from pathlib import Path

import pytest
from aws_cdk import Duration
from aws_cdk.assertions import Match, Template

from da_vinci_cdk.constructs.lambda_function import LambdaFunction


class TestLambdaFunction:
    """Tests for LambdaFunction construct."""

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

    def test_lambda_function_creation(self, stack, temp_lambda_dir):
        """Test basic Lambda function creation."""
        function = LambdaFunction(
            scope=stack,
            construct_id="test-function",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            disable_image_cache=True,
        )

        assert function is not None
        assert function.function is not None

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::Lambda::Function", 1)

    def test_lambda_function_with_timeout(self, stack, temp_lambda_dir):
        """Test Lambda function with custom timeout."""
        LambdaFunction(
            scope=stack,
            construct_id="test-function",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            timeout=Duration.seconds(300),
            disable_image_cache=True,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::Lambda::Function", {"Timeout": 300})

    def test_lambda_function_with_memory(self, stack, temp_lambda_dir):
        """Test Lambda function with custom memory size."""
        LambdaFunction(
            scope=stack,
            construct_id="test-function",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            memory_size=2048,
            disable_image_cache=True,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::Lambda::Function", {"MemorySize": 2048})

    def test_lambda_function_with_description(self, stack, temp_lambda_dir):
        """Test Lambda function with description."""
        LambdaFunction(
            scope=stack,
            construct_id="test-function",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            description="Test function description",
            disable_image_cache=True,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::Lambda::Function", {"Description": "Test function description"}
        )

    def test_lambda_function_creates_iam_role(self, stack, temp_lambda_dir):
        """Test Lambda function creates IAM role."""
        LambdaFunction(
            scope=stack,
            construct_id="test-function",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            disable_image_cache=True,
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::IAM::Role", 1)
        template.has_resource_properties(
            "AWS::IAM::Role",
            {
                "AssumeRolePolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Action": "sts:AssumeRole",
                                    "Effect": "Allow",
                                    "Principal": {"Service": "lambda.amazonaws.com"},
                                }
                            )
                        ]
                    )
                }
            },
        )
