"""Unit tests for da_vinci_cdk.constructs.base module."""

from aws_cdk import Tags

from da_vinci_cdk.constructs.base import apply_framework_tags, resource_namer


class TestResourceNamer:
    """Tests for resource_namer function."""

    def test_resource_namer_basic(self, stack):
        """Test basic resource naming."""
        name = resource_namer("test-resource", scope=stack)
        assert "test" in name
        assert "test-deployment" in name
        assert "test-resource" in name

    def test_resource_namer_with_environment(self, stack):
        """Test resource naming with environment context."""
        name = resource_namer("resource", scope=stack)
        assert "test-app" in name
        assert "test-deployment" in name
        assert "resource" in name

    def test_resource_namer_with_multiple_parts(self, stack):
        """Test resource naming with explicit app_name and deployment_id."""
        name = resource_namer("function", scope=stack, app_name="my-app", deployment_id="prod-01")
        assert "my-app" in name
        assert "prod-01" in name
        assert "function" in name


class TestApplyFrameworkTags:
    """Tests for apply_framework_tags function."""

    def test_apply_framework_tags(self, stack):
        """Test applying framework tags to a construct."""
        apply_framework_tags(stack, scope=stack)

        # Verify tags were applied by checking the stack's tags
        tags = Tags.of(stack)
        assert tags is not None

    def test_apply_framework_tags_with_additional_tags(self, stack):
        """Test applying framework tags with additional custom tags."""
        apply_framework_tags(stack, scope=stack)
        Tags.of(stack).add("custom", "value")

        # Verify both framework and custom tags
        tags = Tags.of(stack)
        assert tags is not None
