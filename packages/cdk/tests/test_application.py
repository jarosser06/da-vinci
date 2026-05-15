"""Unit tests for da_vinci_cdk.application module."""

import json
from unittest.mock import MagicMock, patch

import pytest
from aws_cdk.assertions import Match, Template

from da_vinci.core.resource_discovery import ResourceDiscoveryStorageSolution
from da_vinci_cdk.application import Application, CoreStack, SideCarApplication
from da_vinci_cdk.stack import Stack


def _global_settings(template: Template) -> dict[str, dict[str, str]]:
    """Extract the GlobalSetting items written by a CoreStack template.

    Each ``Custom::DaVinci@GlobalSetting`` resource carries its DynamoDB
    ``putItem`` payload in the ``Create`` property as an ``Fn::Join``. The
    only non-literal segment is the table-name ``Ref``; joining the literal
    segments yields valid JSON (the ref position collapses to an empty
    string), which we parse to recover the exact setting key/value/namespace
    that will be written at deploy time.

    Returns a mapping of setting_key -> {"value", "namespace", "type"}.
    """
    settings: dict[str, dict[str, str]] = {}

    for resource in template.to_json()["Resources"].values():
        if resource["Type"] != "Custom::DaVinci@GlobalSetting":
            continue

        join_parts = resource["Properties"]["Create"]["Fn::Join"][1]
        joined = "".join(part for part in join_parts if isinstance(part, str))
        item = json.loads(joined)["parameters"]["Item"]

        settings[item["SettingKey"]["S"]] = {
            "value": item["SettingValue"]["S"],
            "namespace": item["Namespace"]["S"],
            "type": item["SettingType"]["S"],
        }

    return settings


# The eight GlobalSettings written by every CoreStack regardless of options.
_BASE_SETTING_KEYS = {
    "app_name",
    "deployment_id",
    "log_level",
    "global_settings_enabled",
    "event_bus_enabled",
    "exception_trap_enabled",
    "s3_logging_bucket",
    "resource_discovery_storage_solution",
}


class TestCoreStack:
    """Tests for CoreStack class."""

    def _make(self, app, **kwargs) -> CoreStack:
        return CoreStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestCoreStack",
            **kwargs,
        )

    def test_core_stack_is_a_framework_stack(self, app):
        """CoreStack composes the framework Stack naming convention."""
        stack = self._make(app)

        assert isinstance(stack, Stack)
        assert stack.da_vinci_stack_name == "test-app-test-deployment-TestCoreStack"

    def test_default_core_stack_resource_inventory(self, app):
        """A default CoreStack synthesizes exactly its eight settings + provider."""
        template = Template.from_stack(self._make(app))

        # Eight framework settings, each a DynamoDB-item custom resource.
        template.resource_count_is("Custom::DaVinci@GlobalSetting", 8)
        # A single custom-resource provider Lambda + its execution role back
        # all eight items.
        template.resource_count_is("AWS::Lambda::Function", 1)
        template.resource_count_is("AWS::IAM::Role", 1)
        # No bucket / hosted zone / dynamodb table for the default config.
        template.resource_count_is("AWS::S3::Bucket", 0)
        template.resource_count_is("AWS::Route53::HostedZone", 0)

    def test_default_core_stack_setting_values(self, app):
        """Default settings carry the exact framework values."""
        settings = _global_settings(Template.from_stack(self._make(app)))

        assert set(settings) == _BASE_SETTING_KEYS

        # Every framework setting lives in the same namespace and is a STRING.
        for entry in settings.values():
            assert entry["namespace"] == "da_vinci_framework::core"
            assert entry["type"] == "STRING"

        assert settings["app_name"]["value"] == "test-app"
        assert settings["deployment_id"]["value"] == "test-deployment"
        assert settings["log_level"]["value"] == "INFO"
        assert settings["global_settings_enabled"]["value"] == "true"
        # Both flags default to False on CoreStack itself.
        assert settings["event_bus_enabled"]["value"] == "false"
        assert settings["exception_trap_enabled"]["value"] == "false"
        # No logging bucket -> the value is the string "None".
        assert settings["s3_logging_bucket"]["value"] == "None"
        assert settings["resource_discovery_storage_solution"]["value"] == "ssm"

    def test_event_bus_enabled_records_true(self, app):
        """event_bus_enabled=True is persisted as the string 'true'."""
        settings = _global_settings(Template.from_stack(self._make(app, event_bus_enabled=True)))

        assert settings["event_bus_enabled"]["value"] == "true"
        assert settings["exception_trap_enabled"]["value"] == "false"

    def test_exception_trap_enabled_records_true(self, app):
        """exception_trap_enabled=True is persisted as the string 'true'."""
        settings = _global_settings(
            Template.from_stack(self._make(app, exception_trap_enabled=True))
        )

        assert settings["exception_trap_enabled"]["value"] == "true"
        assert settings["event_bus_enabled"]["value"] == "false"

    def test_dynamodb_resource_discovery_adds_table_name_setting(self, app):
        """DynamoDB discovery records the storage solution and table-name setting."""
        template = Template.from_stack(
            self._make(
                app,
                resource_discovery_storage_solution=(ResourceDiscoveryStorageSolution.DYNAMODB),
                resource_discovery_table_name="resource-registry",
            )
        )

        # One extra GlobalSetting compared to the SSM default.
        template.resource_count_is("Custom::DaVinci@GlobalSetting", 9)

        settings = _global_settings(template)
        assert set(settings) == _BASE_SETTING_KEYS | {"resource_discovery_table_name"}
        assert settings["resource_discovery_storage_solution"]["value"] == "dynamodb"
        # The table name setting is the fully-qualified resource name.
        assert (
            settings["resource_discovery_table_name"]["value"]
            == "test-app-test-deployment-resource-registry"
        )

    def test_dynamodb_resource_discovery_without_table_name_raises(self, app):
        """DynamoDB discovery requires an explicit table name."""
        with pytest.raises(ValueError, match="resource_discovery_table_name is required"):
            self._make(
                app,
                resource_discovery_storage_solution=(ResourceDiscoveryStorageSolution.DYNAMODB),
            )

    def test_s3_logging_bucket_creates_bucket_with_expiry(self, app):
        """A managed logging bucket is created with the exact name and lifecycle."""
        template = Template.from_stack(
            self._make(
                app,
                s3_logging_bucket_name="test-logging-bucket",
                s3_logging_bucket_object_retention_days=30,
            )
        )

        template.resource_count_is("AWS::S3::Bucket", 1)
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "BucketName": "test-logging-bucket",
                "LifecycleConfiguration": {
                    "Rules": Match.array_with([{"ExpirationInDays": 30, "Status": "Enabled"}])
                },
            },
        )
        # The bucket name is recorded in the framework settings.
        settings = _global_settings(template)
        assert settings["s3_logging_bucket"]["value"] == "test-logging-bucket"

    def test_external_logging_bucket_grants_access_without_creating_bucket(self, app):
        """An external bucket records the name and grants access but creates no bucket."""
        template = Template.from_stack(
            self._make(
                app,
                s3_logging_bucket_name="external-logging-bucket",
                using_external_logging_bucket=True,
            )
        )

        # The framework must not provision a bucket it does not own.
        template.resource_count_is("AWS::S3::Bucket", 0)
        # Access policies (managed policies) are still provisioned.
        template.resource_count_is("AWS::IAM::ManagedPolicy", 4)

        settings = _global_settings(template)
        assert settings["s3_logging_bucket"]["value"] == "external-logging-bucket"

    def test_root_domain_records_setting_without_hosted_zone(self, app):
        """root_domain_name alone records the setting but creates no hosted zone."""
        template = Template.from_stack(self._make(app, root_domain_name="example.com"))

        template.resource_count_is("AWS::Route53::HostedZone", 0)
        # The extra root_domain_name setting brings the count to nine.
        template.resource_count_is("Custom::DaVinci@GlobalSetting", 9)

        settings = _global_settings(template)
        assert settings["root_domain_name"]["value"] == "example.com"

    def test_hosted_zone_created_with_exact_domain_name(self, app):
        """create_hosted_zone provisions a Route53 zone for the trailing-dot domain."""
        template = Template.from_stack(
            self._make(
                app,
                root_domain_name="example.com",
                create_hosted_zone=True,
            )
        )

        template.resource_count_is("AWS::Route53::HostedZone", 1)
        template.has_resource_properties(
            "AWS::Route53::HostedZone",
            {"Name": "example.com."},
        )


class TestApplication:
    """Tests for Application class."""

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_creation(self, mock_docker):
        """Test Application can be instantiated."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(app_name="test-app", deployment_id="test-deployment")

        assert app.app_name == "test-app"
        assert app.deployment_id == "test-deployment"
        # The core stack is wired with the composed framework name and the
        # default (SSM) dependency stacks: global settings + core itself.
        assert isinstance(app.core_stack, CoreStack)
        assert app.core_stack.da_vinci_stack_name == "test-app-test-deployment-corestack"
        assert {s.da_vinci_stack_name for s in app.dependency_stacks} == {
            "test-app-test-deployment-globalsettingstablestack",
            "test-app-test-deployment-corestack",
        }
        # core_stack depends on the global settings table stack.
        assert any(
            dep.da_vinci_stack_name == "test-app-test-deployment-globalsettingstablestack"
            for dep in app.core_stack.dependencies
        )

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_synth(self, mock_docker):
        """Test Application can synthesize all of its stacks."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(app_name="test-app", deployment_id="test-deployment")
        app.synth()

        # Synthesis produces a cloud assembly containing every stack the
        # application registered (global settings table + core, plus the
        # default exception trap stack).
        synth_stack_names = {
            getattr(child, "stack_name", None) for child in app.cdk_app.node.children
        }
        assert "test-app-test-deployment-corestack" in synth_stack_names
        assert "test-app-test-deployment-globalsettingstablestack" in synth_stack_names
        assert "test-app-test-deployment-exceptionstrapstack" in synth_stack_names

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_environment(self, mock_docker):
        """Test Application with environment settings."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            log_level="DEBUG",
        )

        assert app is not None
        assert app.log_level == "DEBUG"

    def test_generate_stack_name(self):
        """Test generate_stack_name static method."""
        from da_vinci_cdk.stack import Stack

        name = Application.generate_stack_name(Stack)
        assert name == "stack"

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_logging_bucket_prefix(self, mock_docker):
        """Test Application with logging bucket prefix."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            enable_logging_bucket=True,
            s3_logging_bucket_name_prefix="prefix-",
        )

        # The prefix is prepended to app_name-deployment_id and the managed
        # bucket is provisioned with that exact name.
        Template.from_stack(app.core_stack).has_resource_properties(
            "AWS::S3::Bucket",
            {"BucketName": "prefix-test-app-test-deployment"},
        )

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_logging_bucket_postfix(self, mock_docker):
        """Test Application with logging bucket postfix."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            enable_logging_bucket=True,
            s3_logging_bucket_name_postfix="-postfix",
        )

        # The postfix is appended to app_name-deployment_id.
        Template.from_stack(app.core_stack).has_resource_properties(
            "AWS::S3::Bucket",
            {"BucketName": "test-app-test-deployment-postfix"},
        )

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_existing_logging_bucket(self, mock_docker):
        """Test Application with existing logging bucket."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")
        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            enable_logging_bucket=True,
            existing_s3_logging_bucket_name="existing-bucket",
        )

        template = Template.from_stack(app.core_stack)
        # An existing bucket is referenced, not created by the framework.
        template.resource_count_is("AWS::S3::Bucket", 0)
        # Its name is still recorded in the framework settings.
        settings = _global_settings(template)
        assert settings["s3_logging_bucket"]["value"] == "existing-bucket"

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_existing_bucket_and_prefix_raises_error(self, mock_docker):
        """Test Application raises error when both existing bucket and prefix are set."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        with pytest.raises(
            ValueError,
            match="Both existing_s3_logging_bucket_name and s3_logging_bucket_name_prefix cannot be set",
        ):
            Application(
                app_name="test-app",
                deployment_id="test-deployment",
                enable_logging_bucket=True,
                existing_s3_logging_bucket_name="existing-bucket",
                s3_logging_bucket_name_prefix="prefix-",
            )

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_invalid_resource_discovery_storage(self, mock_docker):
        """Test Application raises error with invalid resource discovery storage."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        with pytest.raises(ValueError, match="Invalid resource discovery storage solution"):
            Application(
                app_name="test-app",
                deployment_id="test-deployment",
                resource_discovery_storage_solution="invalid",
            )

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_dynamodb_resource_discovery(self, mock_docker):
        """Test Application with DynamoDB resource discovery."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            resource_discovery_storage_solution=ResourceDiscoveryStorageSolution.DYNAMODB,
        )

        assert app is not None
        assert (
            app.cdk_app.node.get_context("resource_discovery_storage_solution")
            == ResourceDiscoveryStorageSolution.DYNAMODB
        )

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_event_bus(self, mock_docker):
        """Test Application with event bus enabled."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            enable_event_bus=True,
        )

        # The event bus stack is registered under its composed framework name.
        assert app._event_bus_stack.da_vinci_stack_name == "test-app-test-deployment-eventbusstack"
        # The enable flag is recorded in the CDK app context.
        assert app.cdk_app.node.get_context("event_bus_enabled") is True

        # Regression guard: Application must thread enable_event_bus through to
        # CoreStack so the GlobalSetting runtime code reads from DynamoDB matches
        # the enabled feature (previously hardcoded to "false").
        settings = _global_settings(Template.from_stack(app.core_stack))
        assert settings["event_bus_enabled"]["value"] == "true"

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_exception_trap_disabled(self, mock_docker):
        """Test Application with exception trap disabled."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            enable_exception_trap=False,
        )

        # No exception trap stack is created when disabled.
        assert app._exceptions_trap_stack is None
        synth_stack_names = {s.stack_name for s in app.cdk_app.node.children}
        assert "test-app-test-deployment-exceptionstrapstack" not in synth_stack_names

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_custom_context(self, mock_docker):
        """Test Application with custom context."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            custom_context={"custom_key": "custom_value"},
        )

        assert app is not None
        assert app.cdk_app.node.get_context("custom_context") == {"custom_key": "custom_value"}

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_hosted_zone(self, mock_docker):
        """Test Application with hosted zone creation."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            root_domain_name="example.com",
            create_hosted_zone=True,
        )

        assert app.root_domain_name == "example.com"
        assert hasattr(app.core_stack, "root_domain")
        # The hosted zone is synthesized into the core stack with the exact
        # (trailing-dot) domain name.
        Template.from_stack(app.core_stack).has_resource_properties(
            "AWS::Route53::HostedZone",
            {"Name": "example.com."},
        )

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_app_entry(self, mock_docker, temp_dockerfile_dir):
        """Test Application with app_entry specified."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            app_entry=temp_dockerfile_dir,
        )

        assert app.app_entry == temp_dockerfile_dir
        assert app.app_docker_image is not None
        # When app_image_use_lib_base is the default (True), the app image is
        # built FROM the library image, so its IMAGE build arg is the lib image.
        _, build_kwargs = mock_docker.from_build.call_args_list[-1]
        assert build_kwargs["build_args"] == {"IMAGE": "test-image"}

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_app_entry_without_lib_base(self, mock_docker, temp_dockerfile_dir):
        """Test Application with app_entry and custom base image."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            app_entry=temp_dockerfile_dir,
            app_image_use_lib_base=False,
        )

        assert app.app_docker_image is not None
        # Without the lib base, the app image is built with no extra build args.
        _, build_kwargs = mock_docker.from_build.call_args_list[-1]
        assert build_kwargs["build_args"] == {}

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_add_uninitialized_stack(self, mock_docker):
        """Test adding an uninitialized stack to application."""
        from da_vinci_cdk.stack import Stack

        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
        )

        # Add a custom stack
        class TestStack(Stack):
            def __init__(
                self,
                app_name,
                deployment_id,
                scope,
                stack_name,
                library_base_image=None,
                **kwargs,
            ):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                    library_base_image=library_base_image,
                )

        stack = app.add_uninitialized_stack(TestStack)
        assert isinstance(stack, TestStack)
        # Registered under its generated (lower-cased class) name with the
        # composed framework stack name.
        assert app._stacks["teststack"] is stack
        assert stack.da_vinci_stack_name == "test-app-test-deployment-teststack"
        # Standard init args are threaded through from the application.
        assert stack.library_base_image == "test-image"
        # Adding the same stack class again is idempotent.
        assert app.add_uninitialized_stack(TestStack) is stack

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_add_stack_with_event_bus_dependency(self, mock_docker):
        """Test adding stack that requires event bus when enabled."""
        from da_vinci_cdk.stack import Stack

        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            enable_event_bus=True,
        )

        class TestStackWithEventBus(Stack):
            requires_event_bus = True

            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                )

        stack = app.add_uninitialized_stack(TestStackWithEventBus)
        assert stack is not None

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_add_stack_with_event_bus_dependency_when_disabled_raises_error(
        self, mock_docker
    ):
        """Test adding stack that requires event bus when disabled raises error."""
        from da_vinci_cdk.stack import Stack

        mock_docker.from_build.return_value = MagicMock(image="test-image")

        # Enable event bus first so framework initializes properly, then disable
        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            enable_event_bus=False,
        )

        # Set requires_event_bus as a class attribute
        class TestStackWithEventBus(Stack):
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                )
                self.requires_event_bus = True

        with pytest.raises(ValueError, match="Cannot require the event bus"):
            app.add_uninitialized_stack(TestStackWithEventBus)

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_add_stack_with_exception_trap_dependency(self, mock_docker):
        """Test adding stack that requires exception trap when enabled."""
        from da_vinci_cdk.stack import Stack

        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            enable_exception_trap=True,
        )

        class TestStackWithExceptionTrap(Stack):
            requires_exceptions_trap = True

            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                )

        stack = app.add_uninitialized_stack(TestStackWithExceptionTrap)
        assert stack is not None

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_add_stack_with_exception_trap_dependency_when_disabled_raises_error(
        self, mock_docker
    ):
        """Test adding stack that requires exception trap when disabled raises error."""
        from da_vinci_cdk.stack import Stack

        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            enable_exception_trap=False,
        )

        # Set requires_exceptions_trap as an instance attribute
        class TestStackWithExceptionTrap(Stack):
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                )
                self.requires_exceptions_trap = True

        with pytest.raises(ValueError, match="Cannot require the exceptions trap"):
            app.add_uninitialized_stack(TestStackWithExceptionTrap)

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_lib_container_entry(self, mock_docker):
        """Test lib_container_entry property."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
        )

        import os

        import da_vinci

        entry = app.lib_container_entry
        # Resolves to the installed da_vinci package directory.
        assert os.path.isdir(entry)
        assert os.path.basename(entry) == "da_vinci"
        assert entry == os.path.realpath(da_vinci.__spec__.submodule_search_locations[0])

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_required_stacks_basic_dependency(self, mock_docker):
        """Test that required_stacks creates proper CloudFormation dependencies."""
        from da_vinci_cdk.stack import Stack

        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
        )

        # Create two simple stacks with dependency relationship
        class StackB(Stack):
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                )

        class StackA(Stack):
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                    required_stacks=[StackB],
                )

        # Add StackA which should automatically add StackB as dependency
        stack_a = app.add_uninitialized_stack(StackA)

        # Verify both stacks exist
        assert stack_a is not None
        assert "stackb" in app._stacks

        # Verify dependency relationship
        stack_b = app._stacks["stackb"]
        assert stack_b in stack_a.dependencies

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_required_stacks_transitive_dependencies(self, mock_docker):
        """Test that transitive dependencies through required_stacks work correctly."""
        from da_vinci_cdk.stack import Stack

        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
        )

        # Create three stacks with transitive dependency: A -> B -> C
        class StackC(Stack):
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                )

        class StackB(Stack):
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                    required_stacks=[StackC],
                )

        class StackA(Stack):
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                    required_stacks=[StackB],
                )

        # Add StackA which should recursively add StackB and StackC
        stack_a = app.add_uninitialized_stack(StackA)

        # Verify all stacks exist
        assert stack_a is not None
        assert "stackb" in app._stacks
        assert "stackc" in app._stacks

        # Verify dependency relationships
        stack_b = app._stacks["stackb"]
        stack_c = app._stacks["stackc"]

        assert stack_b in stack_a.dependencies
        assert stack_c in stack_b.dependencies

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_required_stacks_with_event_bus(self, mock_docker):
        """Test that required_stacks works alongside event bus dependency."""
        from da_vinci_cdk.stack import Stack

        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            enable_event_bus=True,
        )

        # Create stacks with both required_stacks and requires_event_bus
        class StackB(Stack):
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                )

        class StackA(Stack):
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                    required_stacks=[StackB],
                    requires_event_bus=True,
                )

        # Add StackA
        stack_a = app.add_uninitialized_stack(StackA)

        # Verify both stacks exist
        assert stack_a is not None
        assert "stackb" in app._stacks

        # Verify both dependencies are present
        stack_b = app._stacks["stackb"]
        event_bus_stack = app._event_bus_stack

        assert stack_b in stack_a.dependencies
        assert event_bus_stack in stack_a.dependencies

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_required_stacks_with_exception_trap(self, mock_docker):
        """Test that required_stacks works alongside exception trap dependency."""
        from da_vinci_cdk.stack import Stack

        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            enable_exception_trap=True,
        )

        # Create stacks with both required_stacks and requires_exceptions_trap
        class StackB(Stack):
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                )

        class StackA(Stack):
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                    required_stacks=[StackB],
                    requires_exceptions_trap=True,
                )

        # Add StackA
        stack_a = app.add_uninitialized_stack(StackA)

        # Verify both stacks exist
        assert stack_a is not None
        assert "stackb" in app._stacks

        # Verify both dependencies are present
        stack_b = app._stacks["stackb"]
        exceptions_trap_stack = app._exceptions_trap_stack

        assert stack_b in stack_a.dependencies
        assert exceptions_trap_stack in stack_a.dependencies

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_required_stacks_multiple_dependencies(self, mock_docker):
        """Test that a stack can have multiple required_stacks."""
        from da_vinci_cdk.stack import Stack

        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
        )

        # Create multiple dependency stacks
        class StackB(Stack):
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                )

        class StackC(Stack):
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                )

        class StackA(Stack):
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                    required_stacks=[StackB, StackC],
                )

        # Add StackA
        stack_a = app.add_uninitialized_stack(StackA)

        # Verify all stacks exist
        assert stack_a is not None
        assert "stackb" in app._stacks
        assert "stackc" in app._stacks

        # Verify both dependencies are present
        stack_b = app._stacks["stackb"]
        stack_c = app._stacks["stackc"]

        assert stack_b in stack_a.dependencies
        assert stack_c in stack_a.dependencies


class TestSideCarApplication:
    """Tests for SideCarApplication class."""

    @patch("da_vinci_cdk.application.GlobalSettings")
    @patch("da_vinci_cdk.application.DockerImage")
    def test_sidecar_application_creation(self, mock_docker, mock_global_settings):
        """Test SideCarApplication can be instantiated."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")
        mock_global_settings.return_value.get.return_value = None

        app = SideCarApplication(
            app_name="test-app",
            deployment_id="test-deployment",
            sidecar_app_name="test-sidecar",
        )

        assert app.app_name == "test-app"
        assert app.sidecar_app_name == "test-sidecar"
        # The sidecar's CDK app context carries the parent app name plus its
        # own sidecar identity.
        assert app.cdk_app.node.get_context("app_name") == "test-app"
        assert app.cdk_app.node.get_context("deployment_id") == "test-deployment"
        assert app.cdk_app.node.get_context("sidecar_app_name") == "test-sidecar"

    @patch("da_vinci_cdk.application.GlobalSettings")
    @patch("da_vinci_cdk.application.DockerImage")
    def test_sidecar_application_synth(self, mock_docker, mock_global_settings):
        """Test SideCarApplication synthesizes only the stacks it registered."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")
        mock_global_settings.return_value.get.return_value = None

        app = SideCarApplication(
            app_name="test-app",
            deployment_id="test-deployment",
            sidecar_app_name="test-sidecar",
        )
        app.synth()

        # A sidecar with no added stacks brings in no framework dependency
        # stacks of its own (the only synth child is CDK's tree-metadata
        # construct, which is not a Stack).
        from aws_cdk import Stack as CDKStack

        stack_children = [
            child for child in app.cdk_app.node.children if isinstance(child, CDKStack)
        ]
        assert stack_children == []

    @patch("da_vinci_cdk.application.GlobalSettings")
    @patch("da_vinci_cdk.application.DockerImage")
    def test_sidecar_application_with_app_entry(
        self, mock_docker, mock_global_settings, temp_dockerfile_dir
    ):
        """Test SideCarApplication with app_entry specified."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")
        mock_global_settings.return_value.get.return_value = None

        app = SideCarApplication(
            app_name="test-app",
            deployment_id="test-deployment",
            sidecar_app_name="test-sidecar",
            app_entry=temp_dockerfile_dir,
        )

        assert app.app_entry == temp_dockerfile_dir
        assert app.app_docker_image is not None
        # Default uses the library image as the app image base.
        _, build_kwargs = mock_docker.from_build.call_args_list[-1]
        assert build_kwargs["build_args"] == {"IMAGE": "test-image"}

    @patch("da_vinci_cdk.application.GlobalSettings")
    @patch("da_vinci_cdk.application.DockerImage")
    def test_sidecar_application_with_app_entry_without_lib_base(
        self, mock_docker, mock_global_settings, temp_dockerfile_dir
    ):
        """Test SideCarApplication with app_entry and custom base image."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")
        mock_global_settings.return_value.get.return_value = None

        app = SideCarApplication(
            app_name="test-app",
            deployment_id="test-deployment",
            sidecar_app_name="test-sidecar",
            app_entry=temp_dockerfile_dir,
            app_image_use_lib_base=False,
        )

        assert app.app_docker_image is not None
        # Without the lib base, the app image build passes no extra build args.
        _, build_kwargs = mock_docker.from_build.call_args_list[-1]
        assert build_kwargs["build_args"] == {}

    @patch("da_vinci_cdk.application.GlobalSettings")
    @patch("da_vinci_cdk.application.DockerImage")
    def test_sidecar_application_add_uninitialized_stack(self, mock_docker, mock_global_settings):
        """Test adding an uninitialized stack to SideCarApplication."""
        from da_vinci_cdk.stack import Stack

        mock_docker.from_build.return_value = MagicMock(image="test-image")
        mock_global_settings.return_value.get.return_value = None

        app = SideCarApplication(
            app_name="test-app",
            deployment_id="test-deployment",
            sidecar_app_name="test-sidecar",
        )

        # Add a custom stack
        class TestStack(Stack):
            def __init__(
                self,
                app_name,
                deployment_id,
                scope,
                stack_name,
                library_base_image=None,
                **kwargs,
            ):
                super().__init__(
                    app_name=app_name,
                    deployment_id=deployment_id,
                    scope=scope,
                    stack_name=stack_name,
                    library_base_image=library_base_image,
                )

        stack = app.add_uninitialized_stack(TestStack)
        assert isinstance(stack, TestStack)
        assert app._stacks["teststack"] is stack
        assert stack.da_vinci_stack_name == "test-app-test-deployment-teststack"
        assert stack.library_base_image == "test-image"
        # Idempotent on repeat add.
        assert app.add_uninitialized_stack(TestStack) is stack

    @patch("da_vinci_cdk.application.GlobalSettings")
    @patch("da_vinci_cdk.application.DockerImage")
    def test_sidecar_application_generate_stack_name(self, mock_docker, mock_global_settings):
        """Test SideCarApplication generate_stack_name static method."""
        from da_vinci_cdk.stack import Stack

        mock_docker.from_build.return_value = MagicMock(image="test-image")
        mock_global_settings.return_value.get.return_value = None

        name = SideCarApplication.generate_stack_name(Stack)
        assert name == "stack"

    @patch("da_vinci_cdk.application.GlobalSettings")
    @patch("da_vinci_cdk.application.DockerImage")
    def test_sidecar_application_lib_container_entry(self, mock_docker, mock_global_settings):
        """Test SideCarApplication lib_container_entry property."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")
        mock_global_settings.return_value.get.return_value = None

        app = SideCarApplication(
            app_name="test-app",
            deployment_id="test-deployment",
            sidecar_app_name="test-sidecar",
        )

        import os

        import da_vinci

        entry = app.lib_container_entry
        assert os.path.isdir(entry)
        assert os.path.basename(entry) == "da_vinci"
        assert entry == os.path.realpath(da_vinci.__spec__.submodule_search_locations[0])
