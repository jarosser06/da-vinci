"""Pytest configuration and shared fixtures for da_vinci_cdk tests."""

import tempfile
from pathlib import Path

import pytest
from aws_cdk import App, Stack
from aws_cdk.aws_lambda import Architecture


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
        # Skip Docker bundling during tests - bundling is tested in E2E tests
        "aws:cdk:bundling-stacks": [],
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
def library_base_image():
    """Provide a base image string for library Lambda functions."""
    return "public.ecr.aws/lambda/python:3.12"


@pytest.fixture
def temp_dockerfile_dir():
    """Create a temporary directory with a Dockerfile for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a minimal Dockerfile
        dockerfile_path = Path(tmpdir) / "Dockerfile"
        dockerfile_path.write_text(
            """ARG IMAGE
FROM ${IMAGE}
ARG FUNCTION_INDEX
ARG FUNCTION_HANDLER
COPY ${FUNCTION_INDEX}.py ${LAMBDA_TASK_ROOT}
CMD ["${FUNCTION_INDEX}.${FUNCTION_HANDLER}"]
"""
        )
        # Create a minimal Python file
        index_path = Path(tmpdir) / "index.py"
        index_path.write_text("def handler(event, context):\n    return {'statusCode': 200}\n")
        yield tmpdir
