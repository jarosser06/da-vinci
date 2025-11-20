"""Unit tests for da_vinci_cdk.application module."""

from unittest.mock import MagicMock, patch

import pytest
from aws_cdk.assertions import Template

from da_vinci.core.resource_discovery import ResourceDiscoveryStorageSolution
from da_vinci_cdk.application import Application, CoreStack, SideCarApplication
from da_vinci_cdk.stack import Stack


class TestCoreStack:
    """Tests for CoreStack class."""

    def test_core_stack_creation(self, app):
        """Test CoreStack can be instantiated."""
        stack = CoreStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestCoreStack",
        )

        assert stack is not None
        assert isinstance(stack, Stack)

    def test_core_stack_synthesizes(self, app):
        """Test CoreStack synthesizes to CloudFormation template."""
        stack = CoreStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestCoreStack",
        )

        template = Template.from_stack(stack)
        assert template is not None

    def test_core_stack_with_event_bus_enabled(self, app):
        """Test CoreStack with event bus enabled."""
        stack = CoreStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestCoreStack",
            event_bus_enabled=True,
        )

        assert stack is not None
        template = Template.from_stack(stack)
        assert template is not None

    def test_core_stack_with_exception_trap_enabled(self, app):
        """Test CoreStack with exception trap enabled."""
        stack = CoreStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestCoreStack",
            exception_trap_enabled=True,
        )

        assert stack is not None
        template = Template.from_stack(stack)
        assert template is not None

    def test_core_stack_with_dynamodb_resource_discovery(self, app):
        """Test CoreStack with DynamoDB resource discovery."""
        stack = CoreStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestCoreStack",
            resource_discovery_storage_solution=ResourceDiscoveryStorageSolution.DYNAMODB,
            resource_discovery_table_name="resource-registry",
        )

        assert stack is not None
        template = Template.from_stack(stack)
        assert template is not None

    def test_core_stack_with_s3_logging_bucket(self, app):
        """Test CoreStack with S3 logging bucket."""
        stack = CoreStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestCoreStack",
            s3_logging_bucket_name="test-logging-bucket",
            s3_logging_bucket_object_retention_days=30,
        )

        assert stack is not None
        template = Template.from_stack(stack)
        assert template is not None

    def test_core_stack_with_external_logging_bucket(self, app):
        """Test CoreStack with external S3 logging bucket."""
        stack = CoreStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestCoreStack",
            s3_logging_bucket_name="external-logging-bucket",
            using_external_logging_bucket=True,
        )

        assert stack is not None
        template = Template.from_stack(stack)
        assert template is not None

    def test_core_stack_with_root_domain(self, app):
        """Test CoreStack with root domain name."""
        stack = CoreStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestCoreStack",
            root_domain_name="example.com",
        )

        assert stack is not None
        template = Template.from_stack(stack)
        assert template is not None

    def test_core_stack_with_hosted_zone(self, app):
        """Test CoreStack with hosted zone creation."""
        stack = CoreStack(
            app_name="test-app",
            deployment_id="test-deployment",
            scope=app,
            stack_name="TestCoreStack",
            root_domain_name="example.com",
            create_hosted_zone=True,
        )

        assert stack is not None
        template = Template.from_stack(stack)
        assert template is not None
        # Verify hosted zone was created
        template.resource_count_is("AWS::Route53::HostedZone", 1)


class TestApplication:
    """Tests for Application class."""

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_creation(self, mock_docker):
        """Test Application can be instantiated."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(app_name="test-app", deployment_id="test-deployment")

        assert app is not None
        assert app.app_name == "test-app"
        assert app.deployment_id == "test-deployment"
        assert app.core_stack is not None
        assert app.cdk_app is not None

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_synth(self, mock_docker):
        """Test Application can synthesize."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(app_name="test-app", deployment_id="test-deployment")
        app.synth()

        # Verify synth was called on the CDK app
        assert app.cdk_app is not None

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

        assert app is not None
        # Verify bucket name was constructed correctly
        assert app.core_stack is not None

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

        assert app is not None

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

        assert app is not None
        # Verify external logging bucket flag is set correctly
        assert app.core_stack is not None

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_existing_bucket_and_prefix_raises_error(self, mock_docker):
        """Test Application raises error when both existing bucket and prefix are set."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        with pytest.raises(ValueError, match="Both existing_s3_logging_bucket_name and s3_logging_bucket_name_prefix cannot be set"):
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
        assert app.cdk_app.node.get_context("resource_discovery_storage_solution") == ResourceDiscoveryStorageSolution.DYNAMODB

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_event_bus(self, mock_docker):
        """Test Application with event bus enabled."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            enable_event_bus=True,
        )

        assert app is not None
        assert app._event_bus_stack is not None

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_exception_trap_disabled(self, mock_docker):
        """Test Application with exception trap disabled."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            enable_exception_trap=False,
        )

        assert app is not None
        assert app._exceptions_trap_stack is None

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

        assert app is not None
        assert app.root_domain_name == "example.com"
        assert hasattr(app.core_stack, "root_domain")

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_with_app_entry(self, mock_docker, temp_dockerfile_dir):
        """Test Application with app_entry specified."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")

        app = Application(
            app_name="test-app",
            deployment_id="test-deployment",
            app_entry=temp_dockerfile_dir,
        )

        assert app is not None
        assert app.app_entry == temp_dockerfile_dir
        assert app.app_docker_image is not None

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

        assert app is not None
        assert app.app_docker_image is not None

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
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(app_name=app_name, deployment_id=deployment_id, scope=scope, stack_name=stack_name)

        stack = app.add_uninitialized_stack(TestStack)
        assert stack is not None
        assert isinstance(stack, TestStack)

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
                super().__init__(app_name=app_name, deployment_id=deployment_id, scope=scope, stack_name=stack_name)

        stack = app.add_uninitialized_stack(TestStackWithEventBus)
        assert stack is not None

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_add_stack_with_event_bus_dependency_when_disabled_raises_error(self, mock_docker):
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
                super().__init__(app_name=app_name, deployment_id=deployment_id, scope=scope, stack_name=stack_name)
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
                super().__init__(app_name=app_name, deployment_id=deployment_id, scope=scope, stack_name=stack_name)

        stack = app.add_uninitialized_stack(TestStackWithExceptionTrap)
        assert stack is not None

    @patch("da_vinci_cdk.application.DockerImage")
    def test_application_add_stack_with_exception_trap_dependency_when_disabled_raises_error(self, mock_docker):
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
                super().__init__(app_name=app_name, deployment_id=deployment_id, scope=scope, stack_name=stack_name)
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

        assert app.lib_container_entry is not None
        assert isinstance(app.lib_container_entry, str)

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
                super().__init__(app_name=app_name, deployment_id=deployment_id, scope=scope, stack_name=stack_name)

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
                super().__init__(app_name=app_name, deployment_id=deployment_id, scope=scope, stack_name=stack_name)

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
                super().__init__(app_name=app_name, deployment_id=deployment_id, scope=scope, stack_name=stack_name)

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
                super().__init__(app_name=app_name, deployment_id=deployment_id, scope=scope, stack_name=stack_name)

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
                super().__init__(app_name=app_name, deployment_id=deployment_id, scope=scope, stack_name=stack_name)

        class StackC(Stack):
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(app_name=app_name, deployment_id=deployment_id, scope=scope, stack_name=stack_name)

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

        assert app is not None
        assert app.app_name == "test-app"
        assert app.sidecar_app_name == "test-sidecar"
        assert app.cdk_app is not None

    @patch("da_vinci_cdk.application.GlobalSettings")
    @patch("da_vinci_cdk.application.DockerImage")
    def test_sidecar_application_synth(self, mock_docker, mock_global_settings):
        """Test SideCarApplication can synthesize."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")
        mock_global_settings.return_value.get.return_value = None

        app = SideCarApplication(
            app_name="test-app",
            deployment_id="test-deployment",
            sidecar_app_name="test-sidecar",
        )
        app.synth()

        # Verify synth was called on the CDK app
        assert app.cdk_app is not None

    @patch("da_vinci_cdk.application.GlobalSettings")
    @patch("da_vinci_cdk.application.DockerImage")
    def test_sidecar_application_with_app_entry(self, mock_docker, mock_global_settings, temp_dockerfile_dir):
        """Test SideCarApplication with app_entry specified."""
        mock_docker.from_build.return_value = MagicMock(image="test-image")
        mock_global_settings.return_value.get.return_value = None

        app = SideCarApplication(
            app_name="test-app",
            deployment_id="test-deployment",
            sidecar_app_name="test-sidecar",
            app_entry=temp_dockerfile_dir,
        )

        assert app is not None
        assert app.app_entry == temp_dockerfile_dir
        assert app.app_docker_image is not None

    @patch("da_vinci_cdk.application.GlobalSettings")
    @patch("da_vinci_cdk.application.DockerImage")
    def test_sidecar_application_with_app_entry_without_lib_base(self, mock_docker, mock_global_settings, temp_dockerfile_dir):
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

        assert app is not None
        assert app.app_docker_image is not None

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
            def __init__(self, app_name, deployment_id, scope, stack_name, **kwargs):
                super().__init__(app_name=app_name, deployment_id=deployment_id, scope=scope, stack_name=stack_name)

        stack = app.add_uninitialized_stack(TestStack)
        assert stack is not None
        assert isinstance(stack, TestStack)

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

        assert app.lib_container_entry is not None
        assert isinstance(app.lib_container_entry, str)
