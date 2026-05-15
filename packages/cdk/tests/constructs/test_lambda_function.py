"""Unit tests for da_vinci_cdk.constructs.lambda_function module."""

import tempfile
from pathlib import Path

import pytest
from aws_cdk import Duration
from aws_cdk.assertions import Match, Template
from aws_cdk.aws_lambda import Architecture

from da_vinci_cdk.constructs.lambda_function import LambdaFunction


class TestLambdaFunction:
    """Tests for LambdaFunction construct."""

    @pytest.fixture
    def temp_lambda_dir(self):
        """Create a temporary directory with a Dockerfile for Lambda function tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a minimal Dockerfile
            dockerfile_path = Path(tmpdir) / "Dockerfile"
            dockerfile_path.write_text("""ARG IMAGE
FROM ${IMAGE}
ARG FUNCTION_INDEX
ARG FUNCTION_HANDLER
COPY ${FUNCTION_INDEX}.py ${LAMBDA_TASK_ROOT}
""")
            # Create a minimal Python file
            index_path = Path(tmpdir) / "index.py"
            index_path.write_text("def handler(event, context):\n    pass\n")
            yield tmpdir

    def test_lambda_function_uses_defaults(self, stack, temp_lambda_dir):
        """A LambdaFunction with no overrides synthesizes one image-based
        function with the framework defaults (128 MB, 30s, ARM64)."""
        LambdaFunction(
            scope=stack,
            construct_id="test-function",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            disable_image_cache=True,
        )

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::Lambda::Function", 1)
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "MemorySize": 128,
                "Timeout": 30,
                "PackageType": "Image",
                "Architectures": ["arm64"],
                "ImageConfig": {"Command": ["index.handler"]},
            },
        )

    def test_lambda_function_injects_framework_environment(self, stack, temp_lambda_dir):
        """The function receives the da_vinci runtime environment derived from
        stack context (app name, deployment id, log level, discovery storage,
        and the global-settings / exception-trap toggles)."""
        LambdaFunction(
            scope=stack,
            construct_id="test-function",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            disable_image_cache=True,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "Environment": {
                    "Variables": {
                        "DA_VINCI_APP_NAME": "test-app",
                        "DA_VINCI_DEPLOYMENT_ID": "test-deployment",
                        "DA_VINCI_RESOURCE_DISCOVERY_STORAGE": "ssm",
                        "LOG_LEVEL": "INFO",
                        "DaVinciFramework_GlobalSettingsEnabled": "True",
                        "DaVinciFramework_ExceptionTrapEnabled": "True",
                    }
                }
            },
        )

    def test_lambda_function_with_timeout(self, stack, temp_lambda_dir):
        """A custom timeout is propagated to the function's Timeout property."""
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
        """A custom memory size is propagated to the function's MemorySize."""
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
        """A description is propagated to the function's Description property."""
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

    def test_lambda_function_architecture_override(self, stack, temp_lambda_dir):
        """An explicit architecture overrides the context default of ARM64."""
        LambdaFunction(
            scope=stack,
            construct_id="test-function",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            architecture=Architecture.X86_64,
            disable_image_cache=True,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties("AWS::Lambda::Function", {"Architectures": ["x86_64"]})

    def test_lambda_function_handler_command_derived_from_index(self, stack, temp_lambda_dir):
        """The image command is derived by stripping ``.py`` from index and
        joining it with the handler name."""
        LambdaFunction(
            scope=stack,
            construct_id="test-function",
            entry=temp_lambda_dir,
            index="worker.py",
            handler="process",
            disable_image_cache=True,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::Lambda::Function", {"ImageConfig": {"Command": ["worker.process"]}}
        )

    def test_lambda_function_tagged_as_framework_general_purpose(self, stack, temp_lambda_dir):
        """A bare function is tagged with the framework 'General' purpose tag
        and the managed marker tag."""
        LambdaFunction(
            scope=stack,
            construct_id="test-function",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            disable_image_cache=True,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "Tags": Match.array_with(
                    [
                        {
                            "Key": "DaVinciFramework::FunctionPurpose",
                            "Value": "General",
                        },
                        {"Key": "DaVinciFrameworkManaged", "Value": "True"},
                    ]
                )
            },
        )

    def test_lambda_function_creates_iam_role(self, stack, temp_lambda_dir):
        """The function provisions exactly one execution role assumable by the
        Lambda service principal."""
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

    def test_lambda_function_allow_custom_metrics_grants_putmetricdata(
        self, stack, temp_lambda_dir
    ):
        """When ``allow_custom_metrics`` is set, an inline IAM policy granting
        cloudwatch:PutMetricData on all resources is attached to the role."""
        LambdaFunction(
            scope=stack,
            construct_id="test-function",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            allow_custom_metrics=True,
            disable_image_cache=True,
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Action": "cloudwatch:PutMetricData",
                                    "Effect": "Allow",
                                    "Resource": "*",
                                }
                            )
                        ]
                    )
                }
            },
        )

    def test_lambda_function_without_custom_metrics_has_no_putmetricdata(
        self, stack, temp_lambda_dir
    ):
        """Without ``allow_custom_metrics`` no inline policy granting
        cloudwatch:PutMetricData is created."""
        LambdaFunction(
            scope=stack,
            construct_id="test-function",
            entry=temp_lambda_dir,
            index="index.py",
            handler="handler",
            disable_image_cache=True,
        )

        template = Template.from_stack(stack)
        # No standalone IAM::Policy with PutMetricData should exist. A bare
        # function with framework access disabled produces no inline policies.
        template.resource_count_is("AWS::IAM::Policy", 0)
