"""Unit tests for da_vinci_cdk.framework_stacks table stacks."""

from aws_cdk.assertions import Template

from da_vinci_cdk.framework_stacks.tables.event_bus_responses.stack import (
    EventBusResponsesTableStack,
)
from da_vinci_cdk.framework_stacks.tables.event_bus_subscriptions.stack import (
    EventBusSubscriptionsTableStack,
)
from da_vinci_cdk.framework_stacks.tables.global_settings.stack import (
    GlobalSettingsTableStack,
)
from da_vinci_cdk.framework_stacks.tables.resource_registry.stack import (
    ResourceRegistrationTableStack,
)
from da_vinci_cdk.framework_stacks.tables.trapped_exceptions.stack import (
    TrappedExceptionsTableStack,
)


class TestEventBusResponsesTableStack:
    """Tests for EventBusResponsesTableStack."""

    def test_stack_creation(self, app):
        """Test EventBusResponsesTableStack creation."""
        stack = EventBusResponsesTableStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="EventBusResponsesTable",
        )

        assert stack is not None

        template = Template.from_stack(stack)
        # Should create a DynamoDB table
        template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)

    def test_stack_synthesizes(self, app):
        """Test EventBusResponsesTableStack synthesizes."""
        stack = EventBusResponsesTableStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="EventBusResponsesTable",
        )

        template = Template.from_stack(stack)
        assert template is not None


class TestEventBusSubscriptionsTableStack:
    """Tests for EventBusSubscriptionsTableStack."""

    def test_stack_creation(self, app):
        """Test EventBusSubscriptionsTableStack creation."""
        stack = EventBusSubscriptionsTableStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="EventBusSubscriptionsTable",
        )

        assert stack is not None

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)

    def test_stack_synthesizes(self, app):
        """Test EventBusSubscriptionsTableStack synthesizes."""
        stack = EventBusSubscriptionsTableStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="EventBusSubscriptionsTable",
        )

        template = Template.from_stack(stack)
        assert template is not None


class TestGlobalSettingsTableStack:
    """Tests for GlobalSettingsTableStack."""

    def test_stack_creation(self, app):
        """Test GlobalSettingsTableStack creation."""
        stack = GlobalSettingsTableStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="GlobalSettingsTable",
        )

        assert stack is not None

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)

    def test_stack_synthesizes(self, app):
        """Test GlobalSettingsTableStack synthesizes."""
        stack = GlobalSettingsTableStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="GlobalSettingsTable",
        )

        template = Template.from_stack(stack)
        assert template is not None


class TestResourceRegistrationTableStack:
    """Tests for ResourceRegistrationTableStack."""

    def test_stack_creation(self, app):
        """Test ResourceRegistrationTableStack creation."""
        stack = ResourceRegistrationTableStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="ResourceRegistrationTable",
        )

        assert stack is not None

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)

    def test_stack_synthesizes(self, app):
        """Test ResourceRegistrationTableStack synthesizes."""
        stack = ResourceRegistrationTableStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="ResourceRegistrationTable",
        )

        template = Template.from_stack(stack)
        assert template is not None


class TestTrappedExceptionsTableStack:
    """Tests for TrappedExceptionsTableStack."""

    def test_stack_creation(self, app):
        """Test TrappedExceptionsTableStack creation."""
        stack = TrappedExceptionsTableStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TrappedExceptionsTable",
        )

        assert stack is not None

        template = Template.from_stack(stack)
        template.resource_count_is("AWS::DynamoDB::GlobalTable", 1)

    def test_stack_synthesizes(self, app):
        """Test TrappedExceptionsTableStack synthesizes."""
        stack = TrappedExceptionsTableStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TrappedExceptionsTable",
        )

        template = Template.from_stack(stack)
        assert template is not None
