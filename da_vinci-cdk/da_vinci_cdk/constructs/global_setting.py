from aws_cdk.custom_resources import (
    AwsCustomResource,
    AwsCustomResourcePolicy,
    AwsSdkCall,
    PhysicalResourceId,
)

from constructs import Construct
from da_vinci.core.exceptions import GlobalSettingsNotEnabledError
from da_vinci.core.tables.global_settings_table import GlobalSetting as GlobalSettingTblObj
from da_vinci.core.tables.global_settings_table import (
    GlobalSettingType,
)
from da_vinci_cdk.constructs.base import custom_type_name, resource_namer
from da_vinci_cdk.constructs.dynamodb import DynamoDBItem


class GlobalSetting(DynamoDBItem):
    """Global setting item."""

    def __init__(
        self,
        namespace: str,
        scope: Construct,
        setting_key: str,
        description: str | None = None,
        setting_type: str | GlobalSettingType | None = GlobalSettingType.STRING,
        setting_value: str | None = "PLACEHOLDER",
    ) -> None:
        """
        Initialize the global setting item.

        Keyword Arguments:
            namespace: The namespace of the setting.
            setting_key: The setting key.
            description: The description of the setting, defaults to None.
            setting_type: The type of the setting, defaults to 'STRING'.
            setting_value: The value of the setting, defaults to 'PLACEHOLDER'.
            scope: The CDK scope.
        """
        base_construct_id = f"global_setting-{namespace}-{setting_key}"

        if not scope.node.get_context("global_settings_enabled"):
            raise GlobalSettingsNotEnabledError()

        super().__init__(
            construct_id=base_construct_id,
            custom_type_name=custom_type_name("GlobalSetting"),
            scope=scope,
            table_object=GlobalSettingTblObj(
                namespace=namespace,
                setting_key=setting_key,
                description=description,
                setting_type=setting_type,
                setting_value=setting_value,
            ),
        )

    @classmethod
    def from_definition(cls, setting: GlobalSettingTblObj, scope: Construct):
        """
        Initialize the global setting item.

        Keyword Arguments:
            setting: The setting to initialize the item with.
            scope: The CDK scope.
        """
        return cls(
            namespace=setting.namespace,
            setting_key=setting.setting_key,
            description=setting.description,
            setting_type=setting.setting_type,
            setting_value=setting.setting_value,
            scope=scope,
        )


class GlobalSettingLookup(Construct):
    """
    Lookup construct for a global setting item.
    """

    def __init__(self, scope: Construct, construct_id: str, namespace: str, setting_key: str) -> None:
        """
        Initialize the global setting lookup construct.

        Keyword Arguments:
        scope: The CDK scope.
        construct_id: The construct ID.
        namespace: The namespace of the setting.
        setting_key: The setting key.
        """
        super().__init__(scope, construct_id)

        self.full_table_name = resource_namer(name=GlobalSettingTblObj.table_name, scope=self)

        self.namespace = namespace

        self.setting_key = setting_key

        # Generate the DynamoDB key
        self.item_key = GlobalSettingTblObj.gen_dynamodb_key(
            partition_key_value=namespace,
            sort_key_value=setting_key,
        )

        # Create a custom resource to look up the value
        self.lookup_resource = AwsCustomResource(
            scope=self,
            id=f"{construct_id}-lookup",
            policy=AwsCustomResourcePolicy.from_sdk_calls(
                resources=[
                    f"arn:aws:dynamodb:*:*:table/{self.full_table_name}",
                    f"arn:aws:dynamodb:*:*:table/{self.full_table_name}/*",
                ]
            ),
            on_create=self._get_item_call(),
            on_update=self._get_item_call(),
            resource_type="Custom::DynamoDBLookup",
        )

    def _get_item_call(self) -> AwsSdkCall:
        """
        Create a GetItem AWS SDK call for the resource lookup

        Returns:
            AwsSdkCall: The GetItem call configuration
        """
        return AwsSdkCall(
            action="getItem",
            service="DynamoDB",
            parameters={
                "Key": self.item_key,
                "TableName": self.full_table_name,
            },
            physical_resource_id=PhysicalResourceId.of(
                f"{self.namespace}-{self.setting_key}-lookup"
            ),
        )

    def get_value(self) -> str:
        """
        Get the endpoint from the lookup result

        Returns:
            str: The endpoint of the discovered resource
        """
        return self.lookup_resource.get_response_field("Item.SettingValue.S")
