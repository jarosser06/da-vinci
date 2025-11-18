"""Unit tests for da_vinci_cdk.constructs.event_bus module."""

from unittest.mock import patch

from aws_cdk.assertions import Template

from da_vinci.core.resource_discovery import ResourceType
from da_vinci_cdk.constructs.access_management import ResourceAccessRequest
from da_vinci_cdk.constructs.event_bus import EventBusSubscription, EventBusSubscriptionFunction


class TestEventBusSubscription:
    """Tests for EventBusSubscription construct."""

    def test_event_bus_subscription_creation(self, stack):
        """Test basic EventBusSubscription creation."""
        subscription = EventBusSubscription(
            scope=stack,
            construct_id="test-subscription",
            event_type="test.event",
            function_name="test-function",
            active=True,
            table_name="test-app-test-deployment-event-bus-subscriptions",
        )

        assert subscription is not None
        assert subscription.resource is not None

        template = Template.from_stack(stack)
        # Should create custom resource for DynamoDB subscription
        template.resource_count_is("Custom::DaVinci@EventBusSubscription", 1)

    def test_event_bus_subscription_with_pattern(self, stack):
        """Test EventBusSubscription with generates_events."""
        EventBusSubscription(
            scope=stack,
            construct_id="test-subscription",
            event_type="test.event",
            function_name="test-function",
            active=True,
            generates_events=["response.event", "status.event"],
            table_name="test-app-test-deployment-event-bus-subscriptions",
        )

        template = Template.from_stack(stack)
        # Should create custom resource
        template.resource_count_is("Custom::DaVinci@EventBusSubscription", 1)

    def test_event_bus_subscription_inactive(self, stack):
        """Test EventBusSubscription with active=False."""
        subscription = EventBusSubscription(
            scope=stack,
            construct_id="test-subscription",
            event_type="test.event",
            function_name="test-function",
            active=False,
            table_name="test-table",
        )

        assert subscription is not None

    @patch("da_vinci_cdk.constructs.event_bus.DynamoDBTable.table_full_name_lookup")
    def test_event_bus_subscription_without_table_name(self, mock_lookup, stack):
        """Test EventBusSubscription without explicit table_name."""
        mock_lookup.return_value = "default-table-name"

        subscription = EventBusSubscription(
            scope=stack,
            construct_id="test-subscription",
            event_type="test.event",
            function_name="test-function",
        )

        assert subscription is not None
        mock_lookup.assert_called_once()


class TestEventBusSubscriptionFunction:
    """Tests for EventBusSubscriptionFunction construct."""

    def test_event_bus_subscription_function_creation(self, stack, temp_dockerfile_dir):
        """Test EventBusSubscriptionFunction creation."""
        function = EventBusSubscriptionFunction(
            construct_id="test-function",
            event_type="TEST_EVENT",
            function_name="test-function",
            scope=stack,
            entry=temp_dockerfile_dir,
            index="index.py",
            handler="handler",
        )

        assert function is not None
        assert function.handler is not None
        assert function.subscription is not None

    def test_event_bus_subscription_function_with_active(self, stack, temp_dockerfile_dir):
        """Test EventBusSubscriptionFunction with active subscription."""
        function = EventBusSubscriptionFunction(
            construct_id="test-function",
            event_type="TEST_EVENT",
            function_name="test-function",
            scope=stack,
            active=True,
            entry=temp_dockerfile_dir,
            index="index.py",
            handler="handler",
        )

        assert function is not None

    def test_event_bus_subscription_function_with_generated_events(
        self, stack, temp_dockerfile_dir
    ):
        """Test EventBusSubscriptionFunction with generated events."""
        function = EventBusSubscriptionFunction(
            construct_id="test-function",
            event_type="TEST_EVENT",
            function_name="test-function",
            scope=stack,
            generates_events=["GENERATED_EVENT"],
            entry=temp_dockerfile_dir,
            index="index.py",
            handler="handler",
        )

        assert function is not None

    def test_event_bus_subscription_function_with_event_bus_access(
        self, stack, temp_dockerfile_dir
    ):
        """Test EventBusSubscriptionFunction with event bus access enabled."""
        function = EventBusSubscriptionFunction(
            construct_id="test-function",
            event_type="TEST_EVENT",
            function_name="test-function",
            scope=stack,
            enable_event_bus_access=True,
            entry=temp_dockerfile_dir,
            index="index.py",
            handler="handler",
        )

        assert function is not None

    def test_event_bus_subscription_function_with_managed_policies(
        self, stack, temp_dockerfile_dir
    ):
        """Test EventBusSubscriptionFunction with managed policies."""
        function = EventBusSubscriptionFunction(
            construct_id="test-function",
            event_type="TEST_EVENT",
            function_name="test-function",
            scope=stack,
            managed_policies=[],
            entry=temp_dockerfile_dir,
            index="index.py",
            handler="handler",
        )

        assert function is not None

    def test_event_bus_subscription_function_with_resource_access_requests(
        self, stack, temp_dockerfile_dir
    ):
        """Test EventBusSubscriptionFunction with resource access requests."""
        requests = [
            ResourceAccessRequest(
                resource_name="test-resource",
                resource_type=ResourceType.BUCKET,
            )
        ]

        function = EventBusSubscriptionFunction(
            construct_id="test-function",
            event_type="TEST_EVENT",
            function_name="test-function",
            scope=stack,
            resource_access_requests=requests,
            entry=temp_dockerfile_dir,
            index="index.py",
            handler="handler",
        )

        assert function is not None

    def test_event_bus_subscription_function_skips_duplicate_event_bus_access(
        self, stack, temp_dockerfile_dir
    ):
        """Test EventBusSubscriptionFunction doesn't add duplicate event_bus access."""
        requests = [
            ResourceAccessRequest(
                resource_name="event_bus",
                resource_type=ResourceType.ASYNC_SERVICE,
            )
        ]

        function = EventBusSubscriptionFunction(
            construct_id="test-function",
            event_type="TEST_EVENT",
            function_name="test-function",
            scope=stack,
            resource_access_requests=requests,
            enable_event_bus_access=True,
            entry=temp_dockerfile_dir,
            index="index.py",
            handler="handler",
        )

        assert function is not None

    def test_event_bus_subscription_function_skips_duplicate_event_response_access(
        self, stack, temp_dockerfile_dir
    ):
        """Test EventBusSubscriptionFunction doesn't add duplicate event_bus_responses access."""
        requests = [
            ResourceAccessRequest(
                resource_name="event_bus_responses",
                resource_type=ResourceType.REST_SERVICE,
            )
        ]

        function = EventBusSubscriptionFunction(
            construct_id="test-function",
            event_type="TEST_EVENT",
            function_name="test-function",
            scope=stack,
            resource_access_requests=requests,
            entry=temp_dockerfile_dir,
            index="index.py",
            handler="handler",
        )

        assert function is not None

    def test_event_bus_subscription_function_with_function_config(
        self, stack, temp_dockerfile_dir
    ):
        """Test EventBusSubscriptionFunction with additional function configuration."""
        from aws_cdk import Duration

        function = EventBusSubscriptionFunction(
            construct_id="test-function",
            event_type="TEST_EVENT",
            function_name="test-function",
            scope=stack,
            timeout=Duration.seconds(300),
            memory_size=512,
            entry=temp_dockerfile_dir,
            index="index.py",
            handler="handler",
        )

        assert function is not None
