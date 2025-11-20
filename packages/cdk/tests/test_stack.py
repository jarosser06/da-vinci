"""Unit tests for da_vinci_cdk.stack module."""

from aws_cdk.assertions import Template

from da_vinci_cdk.stack import Stack


class TestStack:
    """Tests for Stack class."""

    def test_stack_creation(self, app):
        """Test Stack can be instantiated."""
        stack = Stack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestStack",
        )

        assert stack is not None
        assert stack.da_vinci_stack_name == "test-app-test-deployment-TestStack"

    def test_stack_synthesizes(self, app):
        """Test Stack synthesizes to CloudFormation template."""
        stack = Stack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestStack",
        )

        template = Template.from_stack(stack)
        assert template is not None

    def test_stack_with_description(self, app):
        """Test Stack with architecture."""
        stack = Stack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestStack",
            architecture="arm64",
        )

        template = Template.from_stack(stack)
        assert template is not None
        assert stack.architecture == "arm64"
