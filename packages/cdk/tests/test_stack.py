"""Unit tests for da_vinci_cdk.stack module."""

from aws_cdk.assertions import Template

from da_vinci_cdk.stack import Stack


class TestStack:
    """Tests for Stack class."""

    def test_stack_name_is_app_deployment_stack(self, app):
        """da_vinci_stack_name is exactly app_name-deployment_id-stack_name."""
        stack = Stack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestStack",
        )

        assert stack.da_vinci_stack_name == "test-app-test-deployment-TestStack"
        # The CDK construct id (and therefore the stack's logical name) is the
        # same composed string.
        assert stack.node.id == "test-app-test-deployment-TestStack"

    def test_stack_attributes_default(self, app):
        """A bare Stack stores the values it was given and sensible defaults."""
        stack = Stack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestStack",
        )

        assert stack.app_name == "test-app"
        assert stack.deployment_id == "test-deployment"
        assert stack.architecture is None
        assert stack.app_base_image is None
        assert stack.library_base_image is None
        assert stack.required_stacks == []
        assert stack.requires_event_bus is False
        assert stack.requires_exceptions_trap is False

    def test_bare_stack_synthesizes_no_resources(self, app):
        """A bare Stack adds nothing to the template - it is just a container."""
        stack = Stack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestStack",
        )

        template = Template.from_stack(stack)

        # No constructs were added, so the synthesized template has no resources
        # at all.
        assert template.to_json().get("Resources", {}) == {}
        template.resource_count_is("AWS::Lambda::Function", 0)
        template.resource_count_is("AWS::IAM::Role", 0)
        template.resource_count_is("AWS::DynamoDB::GlobalTable", 0)

    def test_stack_with_architecture_is_stored(self, app):
        """The architecture argument is stored verbatim on the instance."""
        stack = Stack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestStack",
            architecture="arm64",
        )

        assert stack.architecture == "arm64"
        # Architecture is metadata on the wrapper; it does not by itself add
        # resources to the synthesized template.
        assert Template.from_stack(stack).to_json().get("Resources", {}) == {}

    def test_add_required_stack_appends(self, app):
        """add_required_stack appends to the required_stacks list."""
        stack = Stack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestStack",
        )
        other = Stack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="OtherStack",
        )

        stack.add_required_stack(other)

        assert stack.required_stacks == [other]
