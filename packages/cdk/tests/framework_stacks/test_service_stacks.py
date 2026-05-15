"""Unit tests for da_vinci_cdk.framework_stacks service stacks."""

from aws_cdk.assertions import Match, Template
from aws_cdk.aws_lambda import Architecture

from da_vinci_cdk.framework_stacks.services.event_bus.stack import EventBusStack
from da_vinci_cdk.framework_stacks.services.exceptions_trap.stack import (
    ExceptionsTrapStack,
)

_GLOBAL_SETTING_TYPE = "Custom::DaVinci@GlobalSetting"
_EXPECTED_ENV = {
    "DA_VINCI_APP_NAME": "test-app",
    "DA_VINCI_DEPLOYMENT_ID": "test-deployment",
    "DA_VINCI_RESOURCE_DISCOVERY_STORAGE": "ssm",
    "LOG_LEVEL": "INFO",
    "DaVinciFramework_GlobalSettingsEnabled": "True",
    "DaVinciFramework_ExceptionTrapEnabled": "True",
}


def _event_bus_stack(app, library_base_image):
    return EventBusStack(
        app_name="test-app",
        architecture=Architecture.ARM_64,
        deployment_id="test-deployment",
        scope=app,
        stack_name="TestEventBusStack",
        library_base_image=library_base_image,
    )


def _exceptions_trap_stack(app, library_base_image):
    return ExceptionsTrapStack(
        app_name="test-app",
        architecture=Architecture.ARM_64,
        deployment_id="test-deployment",
        scope=app,
        stack_name="TestExceptionsTrapStack",
        library_base_image=library_base_image,
    )


class TestEventBusStack:
    """Tests for EventBusStack."""

    def test_async_service_lambda_properties(self, app, library_base_image):
        """The async bus service Lambda has the expected image-package properties."""
        template = Template.from_stack(_event_bus_stack(app, library_base_image))
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "FunctionName": "test-app-test-deployment-event_bus-async-handler",
                "Description": ("Invokes functions with event bodies from the event bus"),
                "PackageType": "Image",
                "Architectures": ["arm64"],
                "Timeout": 30,
                "RecursiveLoop": "Allow",
                "Environment": {"Variables": Match.object_like(_EXPECTED_ENV)},
            },
        )

    def test_rest_responses_lambda_properties(self, app, library_base_image):
        """The REST responses-watcher Lambda is configured as an image function."""
        template = Template.from_stack(_event_bus_stack(app, library_base_image))
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "FunctionName": ("test-app-test-deployment-event_bus_responses-rest-handler"),
                "Description": ("Handles responses from functions executed from the event bus"),
                "PackageType": "Image",
                "Architectures": ["arm64"],
                "Timeout": 30,
            },
        )

    def test_async_service_has_sqs_queue_and_mapping(self, app, library_base_image):
        """The async service is fed by an SQS queue via an event source mapping."""
        template = Template.from_stack(_event_bus_stack(app, library_base_image))
        template.resource_count_is("AWS::SQS::Queue", 1)
        template.has_resource_properties(
            "AWS::SQS::Queue",
            {
                "QueueName": "test-app-test-deployment-event_bus",
                "VisibilityTimeout": 30,
            },
        )
        template.resource_count_is("AWS::Lambda::EventSourceMapping", 1)

    def test_rest_service_exposes_iam_authed_function_url(self, app, library_base_image):
        """The responses service is reachable through an IAM-authed function URL."""
        template = Template.from_stack(_event_bus_stack(app, library_base_image))
        template.resource_count_is("AWS::Lambda::Url", 1)
        template.has_resource_properties(
            "AWS::Lambda::Url",
            {"AuthType": "AWS_IAM"},
        )

    def test_bus_service_can_invoke_tagged_subscriber_functions(self, app, library_base_image):
        """The bus service role may invoke any function tagged as a subscriber."""
        template = Template.from_stack(_event_bus_stack(app, library_base_image))
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Action": "lambda:InvokeFunction",
                                    "Effect": "Allow",
                                    "Resource": "arn:aws:lambda:*",
                                    "Condition": {
                                        "StringEquals": {
                                            "aws:ResourceTag/"
                                            "DaVinciFramework::FunctionPurpose": (
                                                "EventSubscription"
                                            )
                                        }
                                    },
                                }
                            )
                        ]
                    )
                }
            },
        )

    def test_publishes_response_retention_global_setting(self, app, library_base_image):
        """The stack writes the response_retention_hours global setting (=8)."""
        template = Template.from_stack(_event_bus_stack(app, library_base_image))
        template.resource_count_is(_GLOBAL_SETTING_TYPE, 1)

        settings = template.find_resources(_GLOBAL_SETTING_TYPE)
        create = next(iter(settings.values()))["Properties"]["Create"]
        rendered = "".join(
            part if isinstance(part, str) else "__TABLE__" for part in create["Fn::Join"][1]
        )
        assert '"SettingValue":{"S":"8"}' in rendered
        assert '"SettingType":{"S":"INTEGER"}' in rendered
        assert '"SettingKey":{"S":"response_retention_hours"}' in rendered
        assert '"Namespace":{"S":"da_vinci_framework::event_bus"}' in rendered


class TestExceptionsTrapStack:
    """Tests for ExceptionsTrapStack."""

    def test_trap_service_lambda_properties(self, app, library_base_image):
        """The exceptions trap Lambda is an image function with the right metadata."""
        template = Template.from_stack(_exceptions_trap_stack(app, library_base_image))
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "FunctionName": ("test-app-test-deployment-exceptions_trap-rest-handler"),
                "Description": ("Catches exceptions and stores them in a DynamoDB table"),
                "PackageType": "Image",
                "Architectures": ["arm64"],
                "Timeout": 30,
                "Environment": {"Variables": Match.object_like(_EXPECTED_ENV)},
            },
        )

    def test_exposes_iam_authed_function_url(self, app, library_base_image):
        """The trap service is exposed via an IAM-authed function URL."""
        template = Template.from_stack(_exceptions_trap_stack(app, library_base_image))
        template.resource_count_is("AWS::Lambda::Url", 1)
        template.has_resource_properties(
            "AWS::Lambda::Url",
            {"AuthType": "AWS_IAM"},
        )

    def test_publishes_exception_retention_global_setting(self, app, library_base_image):
        """The stack writes the exception_retention_hours global setting (=48)."""
        template = Template.from_stack(_exceptions_trap_stack(app, library_base_image))
        template.resource_count_is(_GLOBAL_SETTING_TYPE, 1)

        settings = template.find_resources(_GLOBAL_SETTING_TYPE)
        create = next(iter(settings.values()))["Properties"]["Create"]
        rendered = "".join(
            part if isinstance(part, str) else "__TABLE__" for part in create["Fn::Join"][1]
        )
        assert '"SettingValue":{"S":"48"}' in rendered
        assert '"SettingType":{"S":"INTEGER"}' in rendered
        assert '"SettingKey":{"S":"exception_retention_hours"}' in rendered
        assert '"Namespace":{"S":"da_vinci_framework::exceptions_trap"}' in rendered

    def test_no_function_url_for_async_only_resources(self, app, library_base_image):
        """Only the single REST trap service is fronted by a function URL."""
        template = Template.from_stack(_exceptions_trap_stack(app, library_base_image))
        # Two Lambda functions: the trap service and the custom-resource provider.
        template.resource_count_is("AWS::Lambda::Function", 2)
