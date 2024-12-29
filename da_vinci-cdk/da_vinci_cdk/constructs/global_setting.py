from typing import Optional, Union

from constructs import Construct

from da_vinci.core.exceptions import GlobalSettingsNotEnabledError
from da_vinci.core.tables.global_settings import (
    GlobalSetting as GlobalSettingTblObj,
    GlobalSettingType,
)

from da_vinci_cdk.constructs.base import custom_type_name
from da_vinci_cdk.constructs.dynamodb import DynamoDBItem


class GlobalSetting(DynamoDBItem):
    """Global setting item."""

    def __init__(self, namespace: str, scope: Construct, setting_key: str, description: Optional[str] = None,
                 setting_type: Optional[Union[str, GlobalSettingType]] = GlobalSettingType.STRING,
                 setting_value: Optional[str] = 'PLACEHOLDER'):
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
        base_construct_id = f'global_setting-{namespace}-{setting_key}'

        if not scope.node.get_context('global_settings_enabled'):
            raise GlobalSettingsNotEnabledError()

        super().__init__(
            construct_id=base_construct_id,
            custom_type_name=custom_type_name('GlobalSetting'),
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