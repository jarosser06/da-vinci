"""Unit tests for da_vinci_cdk.framework_stacks table stacks."""

from aws_cdk.assertions import Match, Template

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

_TABLE_TYPE = "AWS::DynamoDB::GlobalTable"


def _build(cls, app, stack_name):
    return cls(
        app_name="test-app",
        deployment_id="test-deployment",
        scope=app,
        stack_name=stack_name,
    )


def _assert_table(
    template: Template,
    *,
    table_name: str,
    attributes: list[dict],
    key_schema: list[dict],
    ttl_attribute: str | None,
):
    """Assert the single GlobalTable matches the expected on-demand schema."""
    template.resource_count_is(_TABLE_TYPE, 1)

    expected = {
        "TableName": table_name,
        "BillingMode": "PAY_PER_REQUEST",
        "AttributeDefinitions": attributes,
        "KeySchema": key_schema,
        "Replicas": Match.array_with(
            [
                Match.object_like(
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
                                {
                                    "Key": "DaVinciFrameworkManaged",
                                    "Value": "True",
                                },
                            ]
                        )
                    }
                )
            ]
        ),
    }

    if ttl_attribute is not None:
        expected["TimeToLiveSpecification"] = {
            "AttributeName": ttl_attribute,
            "Enabled": True,
        }

    template.has_resource_properties(_TABLE_TYPE, expected)
    # Tables are retained on delete to protect data.
    template.has_resource(_TABLE_TYPE, {"DeletionPolicy": "Retain"})


class TestEventBusResponsesTableStack:
    """Tests for EventBusResponsesTableStack."""

    def test_table_schema(self, app):
        template = Template.from_stack(
            _build(EventBusResponsesTableStack, app, "EventBusResponsesTable")
        )
        _assert_table(
            template,
            table_name="test-app-test-deployment-da_vinci_event_bus_responses",
            attributes=[
                {"AttributeName": "EventType", "AttributeType": "S"},
                {"AttributeName": "ResponseId", "AttributeType": "S"},
            ],
            key_schema=[
                {"AttributeName": "EventType", "KeyType": "HASH"},
                {"AttributeName": "ResponseId", "KeyType": "RANGE"},
            ],
            ttl_attribute="TimeToLive",
        )

    def test_access_policies_published(self, app):
        """Read, default and read_write access policies are published to SSM."""
        template = Template.from_stack(
            _build(EventBusResponsesTableStack, app, "EventBusResponsesTable")
        )
        template.resource_count_is("AWS::IAM::ManagedPolicy", 3)


class TestEventBusSubscriptionsTableStack:
    """Tests for EventBusSubscriptionsTableStack."""

    def test_table_schema(self, app):
        template = Template.from_stack(
            _build(EventBusSubscriptionsTableStack, app, "EventBusSubscriptionsTable")
        )
        _assert_table(
            template,
            table_name="test-app-test-deployment-da_vinci_event_bus_subscriptions",
            attributes=[
                {"AttributeName": "EventType", "AttributeType": "S"},
                {"AttributeName": "FunctionName", "AttributeType": "S"},
            ],
            key_schema=[
                {"AttributeName": "EventType", "KeyType": "HASH"},
                {"AttributeName": "FunctionName", "KeyType": "RANGE"},
            ],
            ttl_attribute=None,
        )

    def test_no_ttl_specification(self, app):
        """Subscriptions are durable, so no TTL specification is emitted."""
        template = Template.from_stack(
            _build(EventBusSubscriptionsTableStack, app, "EventBusSubscriptionsTable")
        )
        tables = template.find_resources(_TABLE_TYPE)
        props = next(iter(tables.values()))["Properties"]
        assert "TimeToLiveSpecification" not in props


class TestGlobalSettingsTableStack:
    """Tests for GlobalSettingsTableStack."""

    def test_table_schema(self, app):
        template = Template.from_stack(_build(GlobalSettingsTableStack, app, "GlobalSettingsTable"))
        _assert_table(
            template,
            table_name="test-app-test-deployment-da_vinci_global_settings",
            attributes=[
                {"AttributeName": "Namespace", "AttributeType": "S"},
                {"AttributeName": "SettingKey", "AttributeType": "S"},
            ],
            key_schema=[
                {"AttributeName": "Namespace", "KeyType": "HASH"},
                {"AttributeName": "SettingKey", "KeyType": "RANGE"},
            ],
            ttl_attribute=None,
        )

    def test_discovery_parameter_published(self, app):
        """The table name is published to the service-discovery SSM path."""
        template = Template.from_stack(_build(GlobalSettingsTableStack, app, "GlobalSettingsTable"))
        template.has_resource_properties(
            "AWS::SSM::Parameter",
            {
                "Name": (
                    "/da_vinci_framework/service_discovery/test-app/"
                    "test-deployment/table/da_vinci_global_settings"
                ),
                "Type": "String",
            },
        )

    def test_read_policy_grants_full_read_actions(self, app):
        """The read managed policy grants the canonical read action set on the table."""
        template = Template.from_stack(_build(GlobalSettingsTableStack, app, "GlobalSettingsTable"))
        template.has_resource_properties(
            "AWS::IAM::ManagedPolicy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Action": [
                                        "dynamodb:BatchGetItem",
                                        "dynamodb:DescribeTable",
                                        "dynamodb:GetRecords",
                                        "dynamodb:ConditionCheckItem",
                                        "dynamodb:GetItem",
                                        "dynamodb:Query",
                                        "dynamodb:GetShardIterator",
                                        "dynamodb:Scan",
                                    ],
                                    "Effect": "Allow",
                                }
                            )
                        ]
                    )
                }
            },
        )


class TestResourceRegistrationTableStack:
    """Tests for ResourceRegistrationTableStack."""

    def test_table_schema(self, app):
        template = Template.from_stack(
            _build(ResourceRegistrationTableStack, app, "ResourceRegistrationTable")
        )
        _assert_table(
            template,
            table_name="test-app-test-deployment-da_vinci_resource_registry",
            attributes=[
                {"AttributeName": "ResourceType", "AttributeType": "S"},
                {"AttributeName": "ResourceName", "AttributeType": "S"},
            ],
            key_schema=[
                {"AttributeName": "ResourceType", "KeyType": "HASH"},
                {"AttributeName": "ResourceName", "KeyType": "RANGE"},
            ],
            ttl_attribute=None,
        )

    def test_excluded_from_service_discovery(self, app):
        """The registry table is not itself published to service discovery."""
        template = Template.from_stack(
            _build(ResourceRegistrationTableStack, app, "ResourceRegistrationTable")
        )
        params = template.find_resources("AWS::SSM::Parameter")
        names = [p["Properties"]["Name"] for p in params.values()]
        assert not any("service_discovery" in n for n in names), names
        # Only the three access-management policy params are published.
        assert len(names) == 3, names


class TestTrappedExceptionsTableStack:
    """Tests for TrappedExceptionsTableStack."""

    def test_table_schema(self, app):
        template = Template.from_stack(
            _build(TrappedExceptionsTableStack, app, "TrappedExceptionsTable")
        )
        _assert_table(
            template,
            table_name="test-app-test-deployment-da_vinci_trapped_exceptions",
            attributes=[
                {"AttributeName": "FunctionName", "AttributeType": "S"},
                {"AttributeName": "ExceptionId", "AttributeType": "S"},
            ],
            key_schema=[
                {"AttributeName": "FunctionName", "KeyType": "HASH"},
                {"AttributeName": "ExceptionId", "KeyType": "RANGE"},
            ],
            ttl_attribute="TimeToLive",
        )
