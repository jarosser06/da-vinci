"""Unit tests for da_vinci_cdk.framework_stacks service stacks."""

from aws_cdk.assertions import Template
from aws_cdk.aws_lambda import Architecture

from da_vinci_cdk.framework_stacks.services.event_bus.stack import EventBusStack
from da_vinci_cdk.framework_stacks.services.exceptions_trap.stack import (
    ExceptionsTrapStack,
)


class TestEventBusStack:
    """Tests for EventBusStack."""

    def test_stack_creation(self, app, library_base_image):
        """Test EventBusStack creation."""
        stack = EventBusStack(
            app_name="test-app",
            architecture=Architecture.ARM_64,
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestEventBusStack",
            library_base_image=library_base_image,
        )

        assert stack is not None

        template = Template.from_stack(stack)
        # Should create Lambda functions for event bus functionality
        assert template is not None

    def test_stack_synthesizes(self, app, library_base_image):
        """Test EventBusStack synthesizes."""
        stack = EventBusStack(
            app_name="test-app",
            architecture=Architecture.ARM_64,
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestEventBusStack",
            library_base_image=library_base_image,
        )

        template = Template.from_stack(stack)
        assert template is not None


class TestExceptionsTrapStack:
    """Tests for ExceptionsTrapStack."""

    def test_stack_creation(self, app, library_base_image):
        """Test ExceptionsTrapStack creation."""
        stack = ExceptionsTrapStack(
            app_name="test-app",
            architecture=Architecture.ARM_64,
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestExceptionsTrapStack",
            library_base_image=library_base_image,
        )

        assert stack is not None

        template = Template.from_stack(stack)
        # Should create Lambda function for exception trapping
        assert template is not None

    def test_stack_synthesizes(self, app, library_base_image):
        """Test ExceptionsTrapStack synthesizes."""
        stack = ExceptionsTrapStack(
            app_name="test-app",
            architecture=Architecture.ARM_64,
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestExceptionsTrapStack",
            library_base_image=library_base_image,
        )

        template = Template.from_stack(stack)
        assert template is not None
