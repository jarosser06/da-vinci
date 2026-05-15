"""Unit tests for da_vinci_cdk.constructs.global_setting module."""

import json

import pytest
from aws_cdk import App, Stack
from aws_cdk.assertions import Match, Template

from da_vinci.core.exceptions import GlobalSettingsNotEnabledError
from da_vinci.core.tables.global_settings_table import GlobalSetting as GlobalSettingTblObj
from da_vinci.core.tables.global_settings_table import (
    GlobalSettingType,
)
from da_vinci_cdk.constructs.global_setting import GlobalSetting, GlobalSettingLookup

_SETTING_TYPE = "Custom::DaVinci@GlobalSetting"
_LOOKUP_TYPE = "Custom::DynamoDBLookup"
_LOOKUP_TABLE_NAME = "test-app-test-deployment-da_vinci_global_settings"


def _single_resource(template: Template, resource_type: str) -> dict:
    resources = template.find_resources(resource_type)
    assert len(resources) == 1, f"expected one {resource_type}, got {resources}"
    return next(iter(resources.values()))["Properties"]


def _resolved_call(value) -> dict:
    """Resolve a custom-resource call payload into a parsed JSON dict.

    The payload may be a plain string or a CloudFormation ``Fn::Join`` whose Ref
    tokens (the SSM-resolved table name) are substituted with a fixed sentinel so
    the surrounding JSON parses cleanly.
    """
    if isinstance(value, str):
        return json.loads(value)
    parts = value["Fn::Join"][1]
    rendered = "".join(part if isinstance(part, str) else "__RESOLVED_TABLE__" for part in parts)
    return json.loads(rendered)


class TestGlobalSetting:
    """Tests for GlobalSetting construct."""

    def test_creates_single_custom_resource(self, stack):
        """A GlobalSetting synthesizes exactly one custom resource."""
        GlobalSetting(
            namespace="test-namespace",
            scope=stack,
            setting_key="test-key",
            description="Test description",
            setting_value="test-value",
        )

        template = Template.from_stack(stack)
        template.resource_count_is(_SETTING_TYPE, 1)

    def test_create_payload_contains_full_item(self, stack):
        """The on_create putItem payload carries every setting attribute."""
        GlobalSetting(
            namespace="test-namespace",
            scope=stack,
            setting_key="test-key",
            description="Test description",
            setting_value="test-value",
            setting_type=GlobalSettingType.INTEGER,
        )

        props = _single_resource(Template.from_stack(stack), _SETTING_TYPE)
        create = _resolved_call(props["Create"])

        assert create["action"] == "putItem"
        assert create["service"] == "DynamoDB"
        assert create["parameters"]["TableName"] == "__RESOLVED_TABLE__"
        item = create["parameters"]["Item"]
        assert item["Namespace"] == {"S": "test-namespace"}
        assert item["SettingKey"] == {"S": "test-key"}
        assert item["SettingType"] == {"S": "INTEGER"}
        assert item["SettingValue"] == {"S": "test-value"}
        assert item["Description"] == {"S": "Test description"}
        # LastUpdated is a generated timestamp; only assert its type.
        assert set(item["LastUpdated"].keys()) == {"N"}

        assert create["physicalResourceId"]["id"] == (
            "da_vinci_global_settings-Namespace-SettingKey"
        )

    def test_setting_type_serialized_string(self, stack):
        """STRING setting type is written verbatim."""
        GlobalSetting(
            namespace="test-namespace",
            scope=stack,
            setting_key="test-key",
            setting_type=GlobalSettingType.STRING,
            setting_value="test string value",
        )

        props = _single_resource(Template.from_stack(stack), _SETTING_TYPE)
        item = _resolved_call(props["Create"])["parameters"]["Item"]
        assert item["SettingType"] == {"S": "STRING"}
        assert item["SettingValue"] == {"S": "test string value"}

    def test_boolean_type_serialized_as_string_value(self, stack):
        """Boolean settings store the type as BOOLEAN and value as a string."""
        GlobalSetting(
            namespace="test-namespace",
            scope=stack,
            setting_key="test-key",
            setting_type=GlobalSettingType.BOOLEAN,
            setting_value="true",
        )

        props = _single_resource(Template.from_stack(stack), _SETTING_TYPE)
        item = _resolved_call(props["Create"])["parameters"]["Item"]
        assert item["SettingType"] == {"S": "BOOLEAN"}
        assert item["SettingValue"] == {"S": "true"}

    def test_without_description_serializes_none_string(self, stack):
        """An omitted description is serialized as the literal string "None".

        The construct passes description=None straight through to the table
        object's optional STRING attribute, which stringifies it rather than
        dropping it, so the synthesized item carries Description={"S":"None"}.
        """
        GlobalSetting(
            namespace="test-namespace",
            scope=stack,
            setting_key="test-key",
            setting_value="test-value",
        )

        props = _single_resource(Template.from_stack(stack), _SETTING_TYPE)
        item = _resolved_call(props["Create"])["parameters"]["Item"]
        assert item["Description"] == {"S": "None"}

    def test_delete_payload_uses_composite_key(self, stack):
        """The on_delete payload targets the namespace/setting_key composite key."""
        GlobalSetting(
            namespace="test-namespace",
            scope=stack,
            setting_key="test-key",
            setting_value="test-value",
        )

        props = _single_resource(Template.from_stack(stack), _SETTING_TYPE)
        delete = _resolved_call(props["Delete"])
        assert delete["action"] == "deleteItem"
        assert delete["parameters"]["Key"] == {
            "Namespace": {"S": "test-namespace"},
            "SettingKey": {"S": "test-key"},
        }

    def test_custom_resource_iam_policy_scopes_to_table(self, stack):
        """The provider is granted PutItem and DeleteItem on the resolved table."""
        GlobalSetting(
            namespace="test-namespace",
            scope=stack,
            setting_key="test-key",
            setting_value="test-value",
        )

        template = Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": Match.array_with(
                        [
                            Match.object_like({"Action": "dynamodb:PutItem"}),
                            Match.object_like({"Action": "dynamodb:DeleteItem"}),
                        ]
                    ),
                    "Version": "2012-10-17",
                }
            },
        )

    def test_install_latest_aws_sdk_disabled(self, stack):
        """The custom resource pins the bundled SDK."""
        GlobalSetting(
            namespace="test-namespace",
            scope=stack,
            setting_key="test-key",
            setting_value="test-value",
        )

        props = _single_resource(Template.from_stack(stack), _SETTING_TYPE)
        assert props["InstallLatestAwsSdk"] is False

    def test_global_settings_disabled_raises_error(self):
        """GlobalSetting raises when global settings are disabled in context."""
        app = App(
            context={
                "app_name": "test-app",
                "deployment_id": "test-deployment",
                "global_settings_enabled": False,
            }
        )
        stack = Stack(app, "TestStack")

        with pytest.raises(GlobalSettingsNotEnabledError):
            GlobalSetting(
                namespace="test-namespace",
                scope=stack,
                setting_key="test-key",
                setting_value="test-value",
            )

    def test_from_definition_matches_direct_construction(self, stack):
        """from_definition produces the same custom-resource payload as __init__."""
        tbl_obj = GlobalSettingTblObj(
            namespace="test-namespace",
            setting_key="test-key",
            description="Test description",
            setting_type=GlobalSettingType.STRING,
            setting_value="test-value",
        )

        GlobalSetting.from_definition(setting=tbl_obj, scope=stack)

        props = _single_resource(Template.from_stack(stack), _SETTING_TYPE)
        item = _resolved_call(props["Create"])["parameters"]["Item"]
        assert item["Namespace"] == {"S": "test-namespace"}
        assert item["SettingKey"] == {"S": "test-key"}
        assert item["SettingValue"] == {"S": "test-value"}


class TestGlobalSettingLookup:
    """Tests for GlobalSettingLookup construct."""

    def test_lookup_creates_getitem_custom_resource(self, stack):
        """The lookup synthesizes a DynamoDBLookup custom resource doing getItem."""
        lookup = GlobalSettingLookup(
            scope=stack,
            construct_id="test-lookup",
            namespace="test-namespace",
            setting_key="test-key",
        )

        assert lookup.namespace == "test-namespace"
        assert lookup.setting_key == "test-key"

        template = Template.from_stack(stack)
        template.resource_count_is(_LOOKUP_TYPE, 1)

        props = _single_resource(template, _LOOKUP_TYPE)
        create = json.loads(props["Create"])
        assert create["action"] == "getItem"
        assert create["service"] == "DynamoDB"
        assert create["parameters"]["TableName"] == _LOOKUP_TABLE_NAME
        assert create["parameters"]["Key"] == {
            "Namespace": {"S": "test-namespace"},
            "SettingKey": {"S": "test-key"},
        }
        assert create["physicalResourceId"]["id"] == "test-namespace-test-key-lookup"

    def test_lookup_create_and_update_calls_match(self, stack):
        """on_create and on_update both perform the same getItem call."""
        GlobalSettingLookup(
            scope=stack,
            construct_id="test-lookup",
            namespace="test-namespace",
            setting_key="test-key",
        )

        props = _single_resource(Template.from_stack(stack), _LOOKUP_TYPE)
        assert json.loads(props["Create"]) == json.loads(props["Update"])

    def test_lookup_iam_policy_grants_getitem(self, stack):
        """The lookup provider is granted GetItem on the settings table only."""
        GlobalSettingLookup(
            scope=stack,
            construct_id="test-lookup",
            namespace="test-namespace",
            setting_key="test-key",
        )

        Template.from_stack(stack).has_resource_properties(
            "AWS::IAM::Policy",
            {
                "PolicyDocument": {
                    "Statement": [
                        {
                            "Action": "dynamodb:GetItem",
                            "Effect": "Allow",
                            "Resource": [
                                f"arn:aws:dynamodb:*:*:table/{_LOOKUP_TABLE_NAME}",
                                f"arn:aws:dynamodb:*:*:table/{_LOOKUP_TABLE_NAME}/*",
                            ],
                        }
                    ],
                    "Version": "2012-10-17",
                }
            },
        )

    def test_get_value_reads_setting_value_field(self, stack):
        """get_value pulls the SettingValue string attribute from the lookup result."""
        lookup = GlobalSettingLookup(
            scope=stack,
            construct_id="test-lookup",
            namespace="test-namespace",
            setting_key="test-key",
        )

        value = lookup.get_value()
        # The returned token references the custom resource's GetResponseField
        # for the Item.SettingValue.S path.
        token = stack.resolve(value)
        assert token["Fn::GetAtt"][1] == "Item.SettingValue.S"
