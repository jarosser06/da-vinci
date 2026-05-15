"""Unit tests for da_vinci_cdk.constructs.base module."""

from aws_cdk import aws_sqs as sqs
from aws_cdk.assertions import Match, Template

from da_vinci_cdk.constructs.base import (
    apply_framework_tags,
    custom_type_name,
    resource_namer,
)


class TestCustomTypeName:
    """Tests for custom_type_name function."""

    def test_default_prefix_and_separator(self):
        """Defaults produce Custom::DaVinci@<name>."""
        assert custom_type_name("GlobalSetting") == "Custom::DaVinci@GlobalSetting"

    def test_custom_prefix_and_separator(self):
        """Explicit prefix/separator are used verbatim."""
        assert custom_type_name("Thing", prefix="Acme", separator="::") == "Custom::Acme::Thing"


class TestResourceNamer:
    """Tests for resource_namer function."""

    def test_uses_scope_context(self, stack):
        """Name is exactly app_name-deployment_id-name from scope context."""
        assert (
            resource_namer("test-resource", scope=stack) == "test-app-test-deployment-test-resource"
        )

    def test_explicit_app_and_deployment_override_scope(self, stack):
        """Explicit app_name/deployment_id take precedence over scope context."""
        assert (
            resource_namer("function", scope=stack, app_name="my-app", deployment_id="prod-01")
            == "my-app-prod-01-function"
        )

    def test_explicit_args_without_scope(self):
        """No scope is required when app_name and deployment_id are explicit."""
        assert resource_namer("queue", app_name="a", deployment_id="b") == "a-b-queue"

    def test_missing_app_name_without_scope_raises(self):
        """Omitting both scope and app_name is an error."""
        try:
            resource_namer("x", deployment_id="b")
        except ValueError as exc:
            assert "app_name" in str(exc)
        else:
            raise AssertionError("expected ValueError")

    def test_missing_deployment_id_without_scope_raises(self):
        """Omitting both scope and deployment_id is an error."""
        try:
            resource_namer("x", app_name="a")
        except ValueError as exc:
            assert "deployment_id" in str(exc)
        else:
            raise AssertionError("expected ValueError")


class TestApplyFrameworkTags:
    """Tests for apply_framework_tags function."""

    def test_applies_exact_framework_tags(self, stack):
        """The three framework tags appear with exact keys/values on a resource."""
        queue = sqs.Queue(stack, "TaggedQueue")

        apply_framework_tags(queue, scope=stack)

        Template.from_stack(stack).has_resource_properties(
            "AWS::SQS::Queue",
            {
                "Tags": Match.array_with(
                    [
                        {
                            "Key": "DaVinciFramework::ApplicationName",
                            "Value": "test-app",
                        },
                        {
                            "Key": "DaVinciFramework::DeploymentId",
                            "Value": "test-deployment",
                        },
                        {"Key": "DaVinciFrameworkManaged", "Value": "True"},
                    ]
                )
            },
        )

    def test_additional_tags_coexist_with_framework_tags(self, stack):
        """Custom tags are applied alongside (not instead of) framework tags."""
        from aws_cdk import Tags

        queue = sqs.Queue(stack, "TaggedQueue")
        apply_framework_tags(queue, scope=stack)
        Tags.of(queue).add("custom", "value")

        template = Template.from_stack(stack)
        # CDK renders tags sorted by key, so the custom tag and the framework
        # tags are not contiguous; assert each is present independently.
        template.has_resource_properties(
            "AWS::SQS::Queue",
            {"Tags": Match.array_with([{"Key": "custom", "Value": "value"}])},
        )
        template.has_resource_properties(
            "AWS::SQS::Queue",
            {"Tags": Match.array_with([{"Key": "DaVinciFrameworkManaged", "Value": "True"}])},
        )
