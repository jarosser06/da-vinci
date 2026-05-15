"""Unit tests for da_vinci_cdk.constructs.event_bus module."""

import json
from unittest.mock import patch

from aws_cdk.assertions import Match, Template

from da_vinci.core.resource_discovery import ResourceType
from da_vinci_cdk.constructs.access_management import ResourceAccessRequest
from da_vinci_cdk.constructs.event_bus import (
    EventBusSubscription,
    EventBusSubscriptionFunction,
)

_SUBSCRIPTION_TYPE = "Custom::DaVinci@EventBusSubscription"
_TABLE_NAME = "test-app-test-deployment-event-bus-subscriptions"


def _subscription_resource(template: Template) -> dict:
    """Return the single EventBusSubscription custom-resource Properties block."""
    resources = template.find_resources(_SUBSCRIPTION_TYPE)
    assert len(resources) == 1, f"expected exactly one subscription, got {resources}"
    return next(iter(resources.values()))["Properties"]


def _resolved_call(value) -> dict:
    """Parse a custom-resource call payload into a dict.

    The payload is a plain JSON string for the standalone construct, but an
    ``Fn::Join`` (with token Refs, e.g. the resolved Lambda function name) when
    created via EventBusSubscriptionFunction. Token Refs are replaced with a
    fixed sentinel so the surrounding JSON parses.
    """
    if isinstance(value, str):
        return json.loads(value)
    rendered = "".join(
        part if isinstance(part, str) else "__TOKEN__" for part in value["Fn::Join"][1]
    )
    return json.loads(rendered)


class TestEventBusSubscription:
    """Tests for EventBusSubscription construct."""

    def test_creates_single_custom_resource_with_putitem_policy(self, stack):
        """An active subscription synthesizes one custom resource scoped to the table."""
        subscription = EventBusSubscription(
            scope=stack,
            construct_id="test-subscription",
            event_type="test.event",
            function_name="test-function",
            active=True,
            table_name=_TABLE_NAME,
        )

        assert subscription.resource is not None

        template = Template.from_stack(stack)
        template.resource_count_is(_SUBSCRIPTION_TYPE, 1)

        # The custom-resource provider is granted exactly PutItem (create) and
        # DeleteItem (delete) on the target table and its indexes.
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": [
                        {
                            "Action": "dynamodb:PutItem",
                            "Effect": "Allow",
                            "Resource": [
                                f"arn:aws:dynamodb:*:*:table/{_TABLE_NAME}",
                                f"arn:aws:dynamodb:*:*:table/{_TABLE_NAME}/*",
                            ],
                        },
                        {
                            "Action": "dynamodb:DeleteItem",
                            "Effect": "Allow",
                            "Resource": [
                                f"arn:aws:dynamodb:*:*:table/{_TABLE_NAME}",
                                f"arn:aws:dynamodb:*:*:table/{_TABLE_NAME}/*",
                            ],
                        },
                    ],
                    "Version": "2012-10-17",
                }
            },
        )

    def test_create_call_payload_targets_event_type_and_function(self, stack):
        """The on_create putItem call carries the exact event_type / function_name keys."""
        EventBusSubscription(
            scope=stack,
            construct_id="test-subscription",
            event_type="test.event",
            function_name="test-function",
            active=True,
            table_name=_TABLE_NAME,
        )

        props = _subscription_resource(Template.from_stack(stack))
        create = json.loads(props["Create"])

        assert create["action"] == "putItem"
        assert create["service"] == "DynamoDB"
        assert create["parameters"]["TableName"] == _TABLE_NAME
        assert create["physicalResourceId"]["id"] == "test.event-test-function"

        item = create["parameters"]["Item"]
        assert item["EventType"] == {"S": "test.event"}
        assert item["FunctionName"] == {"S": "test-function"}
        # generates_events defaults to an empty list when not supplied.
        assert item["GeneratesEvents"] == {"L": []}
        # active=True is requested and preserved verbatim.
        assert item["Active"] == {"BOOL": True}

    def test_delete_call_payload_uses_composite_key(self, stack):
        """The on_delete deleteItem call uses the composite (event_type, function_name) key."""
        EventBusSubscription(
            scope=stack,
            construct_id="test-subscription",
            event_type="test.event",
            function_name="test-function",
            table_name=_TABLE_NAME,
        )

        props = _subscription_resource(Template.from_stack(stack))
        delete = json.loads(props["Delete"])

        assert delete["action"] == "deleteItem"
        assert delete["parameters"]["TableName"] == _TABLE_NAME
        assert delete["parameters"]["Key"] == {
            "EventType": {"S": "test.event"},
            "FunctionName": {"S": "test-function"},
        }
        assert delete["physicalResourceId"]["id"] == "test.event-test-function"

    def test_generates_events_serialized_into_create_payload(self, stack):
        """generates_events are written as a DynamoDB string-list in the create payload."""
        EventBusSubscription(
            scope=stack,
            construct_id="test-subscription",
            event_type="test.event",
            function_name="test-function",
            active=True,
            generates_events=["response.event", "status.event"],
            table_name=_TABLE_NAME,
        )

        props = _subscription_resource(Template.from_stack(stack))
        item = json.loads(props["Create"])["parameters"]["Item"]

        assert item["GeneratesEvents"] == {"L": [{"S": "response.event"}, {"S": "status.event"}]}

    def test_active_false_is_preserved(self, stack):
        """active=False must be written as Active=false, not clobbered to the default.

        Regression guard for the ORM default-substitution bug where any falsy
        explicit value was replaced by the attribute default — an inactive
        subscription was silently written as Active=true.
        """
        EventBusSubscription(
            scope=stack,
            construct_id="test-subscription",
            event_type="test.event",
            function_name="test-function",
            active=False,
            table_name=_TABLE_NAME,
        )

        props = _subscription_resource(Template.from_stack(stack))
        item = json.loads(props["Create"])["parameters"]["Item"]

        assert item["Active"] == {"BOOL": False}

    def test_install_latest_aws_sdk_disabled(self, stack):
        """The custom resource pins the bundled SDK rather than installing latest."""
        EventBusSubscription(
            scope=stack,
            construct_id="test-subscription",
            event_type="test.event",
            function_name="test-function",
            table_name=_TABLE_NAME,
        )

        props = _subscription_resource(Template.from_stack(stack))
        assert props["InstallLatestAwsSdk"] is False

    @patch("da_vinci_cdk.constructs.event_bus.DynamoDBTable.table_full_name_lookup")
    def test_without_table_name_uses_discovery_lookup(self, mock_lookup, stack):
        """When no table_name is given, the name is resolved via resource discovery."""
        mock_lookup.return_value = "default-table-name"

        EventBusSubscription(
            scope=stack,
            construct_id="test-subscription",
            event_type="test.event",
            function_name="test-function",
        )

        mock_lookup.assert_called_once()
        assert mock_lookup.call_args.kwargs["table_name"] == ("da_vinci_event_bus_subscriptions")

        template = Template.from_stack(stack)
        props = _subscription_resource(template)
        assert json.loads(props["Create"])["parameters"]["TableName"] == ("default-table-name")

        # IAM policy resources point at the discovered table name.
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Action": "dynamodb:PutItem",
                                    "Resource": [
                                        "arn:aws:dynamodb:*:*:table/default-table-name",
                                        "arn:aws:dynamodb:*:*:table/default-table-name/*",
                                    ],
                                }
                            )
                        ]
                    )
                }
            },
        )


class TestEventBusSubscriptionFunction:
    """Tests for EventBusSubscriptionFunction construct."""

    def test_creates_lambda_and_subscription(self, stack, temp_dockerfile_dir):
        """The function construct produces a Lambda image function and a subscription."""
        function = EventBusSubscriptionFunction(
            construct_id="test-function",
            event_type="TEST_EVENT",
            function_name="test-function",
            scope=stack,
            entry=temp_dockerfile_dir,
            index="index.py",
            handler="handler",
        )

        assert function.handler is not None
        assert function.subscription is not None

        template = Template.from_stack(stack)
        template.resource_count_is(_SUBSCRIPTION_TYPE, 1)
        # Exactly one image-packaged Lambda for the subscriber itself (the other
        # Lambda function present is the custom-resource provider).
        template.resource_count_is("AWS::Lambda::Function", 2)
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {"PackageType": "Image"},
        )

    def test_function_tagged_as_event_subscription(self, stack, temp_dockerfile_dir):
        """The subscriber Lambda is tagged with the EventSubscription purpose."""
        EventBusSubscriptionFunction(
            construct_id="test-function",
            event_type="TEST_EVENT",
            function_name="test-function",
            scope=stack,
            entry=temp_dockerfile_dir,
            index="index.py",
            handler="handler",
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "Tags": Match.array_with(
                    [
                        {
                            "Key": "DaVinciFramework::FunctionPurpose",
                            "Value": "EventSubscription",
                        }
                    ]
                )
            },
        )

    def test_subscription_create_payload_uses_event_type(self, stack, temp_dockerfile_dir):
        """The created subscription records the function's event type."""
        EventBusSubscriptionFunction(
            construct_id="test-function",
            event_type="TEST_EVENT",
            function_name="test-function",
            scope=stack,
            generates_events=["GENERATED_EVENT"],
            entry=temp_dockerfile_dir,
            index="index.py",
            handler="handler",
        )

        props = _subscription_resource(Template.from_stack(stack))
        item = _resolved_call(props["Create"])["parameters"]["Item"]

        assert item["EventType"] == {"S": "TEST_EVENT"}
        assert item["GeneratesEvents"] == {"L": [{"S": "GENERATED_EVENT"}]}

    def test_event_bus_access_adds_two_managed_policy_imports(self, stack, temp_dockerfile_dir):
        """enable_event_bus_access imports the event_bus + event_bus_responses policies.

        Both are imported from SSM via CDK custom resources (one per managed
        policy ARN lookup), so two AWS::CloudFormation custom resources back
        the imports in addition to the subscription record.
        """
        EventBusSubscriptionFunction(
            construct_id="test-function",
            event_type="TEST_EVENT",
            function_name="test-function",
            scope=stack,
            enable_event_bus_access=True,
            entry=temp_dockerfile_dir,
            index="index.py",
            handler="handler",
        )

        template = Template.from_stack(stack)
        # event_bus + event_bus_responses managed-policy ARNs are read from SSM.
        ssm_params = template.find_parameters(
            "*", {"Default": Match.string_like_regexp("access_management")}
        )
        param_defaults = sorted(p["Default"] for p in ssm_params.values())
        assert any("event_bus/default" in d for d in param_defaults)
        assert any("event_bus_responses/default" in d for d in param_defaults)

    def test_resource_access_request_event_bus_not_duplicated(self, stack, temp_dockerfile_dir):
        """An explicit event_bus request is not duplicated by enable_event_bus_access."""
        requests = [
            ResourceAccessRequest(
                resource_name="event_bus",
                resource_type=ResourceType.ASYNC_SERVICE,
            )
        ]

        EventBusSubscriptionFunction(
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

        template = Template.from_stack(stack)
        ssm_params = template.find_parameters(
            "*",
            {"Default": Match.string_like_regexp(r"access_management.*event_bus/")},
        )
        event_bus_defaults = [
            p["Default"]
            for p in ssm_params.values()
            if p["Default"].rstrip("/").endswith("event_bus/default")
        ]
        # Exactly one event_bus (async service) policy import, not two.
        assert len(event_bus_defaults) == 1, event_bus_defaults

    def test_resource_access_request_event_responses_not_duplicated(
        self, stack, temp_dockerfile_dir
    ):
        """An explicit event_bus_responses request suppresses the automatic one."""
        requests = [
            ResourceAccessRequest(
                resource_name="event_bus_responses",
                resource_type=ResourceType.REST_SERVICE,
            )
        ]

        EventBusSubscriptionFunction(
            construct_id="test-function",
            event_type="TEST_EVENT",
            function_name="test-function",
            scope=stack,
            resource_access_requests=requests,
            entry=temp_dockerfile_dir,
            index="index.py",
            handler="handler",
        )

        template = Template.from_stack(stack)
        ssm_params = template.find_parameters(
            "*",
            {"Default": Match.string_like_regexp("access_management")},
        )
        responses_defaults = [
            p["Default"]
            for p in ssm_params.values()
            if p["Default"].rstrip("/").endswith("event_bus_responses/default")
        ]
        assert len(responses_defaults) == 1, responses_defaults

    def test_function_config_sets_timeout_and_memory(self, stack, temp_dockerfile_dir):
        """Extra function_config kwargs flow through to the Lambda properties."""
        from aws_cdk import Duration

        EventBusSubscriptionFunction(
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

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {"Timeout": 300, "MemorySize": 512, "PackageType": "Image"},
        )
