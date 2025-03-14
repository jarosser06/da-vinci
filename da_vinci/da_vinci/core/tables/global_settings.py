'''Global Settings Table Definitions'''

from datetime import datetime, UTC as utc_tz
from enum import auto, StrEnum
from typing import Any, List, Optional, Union

from da_vinci.core.orm.client import (
    TableClient,
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
    TableScanDefinition,
)
from da_vinci.core.base import GLOBAL_SETTINGS_TABLE_NAME

class GlobalSettingType(StrEnum):
    """Setting Types"""
    BOOLEAN = auto()
    FLOAT = auto()
    INTEGER = auto()
    STRING = auto()


class GlobalSetting(TableObject):
    description = 'Application Settings'
    table_name = GLOBAL_SETTINGS_TABLE_NAME

    partition_key_attribute = TableObjectAttribute(
        name='namespace',
        attribute_type=TableObjectAttributeType.STRING,
        description='The namespace that the setting belongs to',
    )

    sort_key_attribute = TableObjectAttribute(
        name='setting_key',
        attribute_type=TableObjectAttributeType.STRING,
        description='The setting key',
    )

    attributes = [
        TableObjectAttribute(
            name='description',
            attribute_type=TableObjectAttributeType.STRING,
            description='The description of the setting',
            optional=True,
        ),
        TableObjectAttribute(
            name='last_updated',
            attribute_type=TableObjectAttributeType.DATETIME,
            default=lambda: datetime.now(tz=utc_tz),
            description='The last time the setting was updated',
        ),
        TableObjectAttribute(
            name='setting_type',
            attribute_type=TableObjectAttributeType.STRING,
            description='The type of the setting',
        ),
        TableObjectAttribute(
            name='setting_value',
            attribute_type=TableObjectAttributeType.STRING,
            description='The value of the setting',
        ),
    ]

    def __init__(self, **kwargs):
        """
        Initialize a new Setting object

        Keyword Arguments:
            description: The description of the setting
            last_updated: The last time the setting was updated, defaults to now
            namespace: The namespace that the setting belongs to
            setting_key: The setting key
            setting_type: The type of the setting
            setting_value: The value of the setting

        Example:
            ```
            from datetime import datetime

            from da_vinci.core.tables.settings import Setting, SettingType

            setting = Setting(
                description='The description of the setting',
                last_updated=datetime.now(),
                namespace='core',
                setting_key='global_settings_enabled',
                setting_type=SettingType.BOOLEAN,
                setting_value=True,
            )
            ```
        """
        if isinstance(kwargs.get('setting_type'), GlobalSettingType):
            kwargs['setting_type'] = kwargs['setting_type'].name

        # Ensure the setting value is a string
        if not isinstance(kwargs.get('setting_value'), str):
            kwargs['setting_value'] = str(kwargs['setting_value'])

        super().__init__(**kwargs)

    def value_as_type(self) -> Any:
        """
        Return the setting value as the correct type
        """
        if self.setting_type == GlobalSettingType.BOOLEAN.name:
            return self.setting_value.lower() == 'true'
        elif self.setting_type == GlobalSettingType.FLOAT.name:
            return float(self.setting_value)
        elif self.setting_type == GlobalSettingType.INTEGER.name:
            return int(self.setting_value)
        
        return self.setting_value


class GlobalSettingsScanDefinition(TableScanDefinition):
    def __init__(self):
        super().__init__(table_object_class=GlobalSetting)


class GlobalSettings(TableClient):
    def __init__(self, app_name: Optional[str] = None, deployment_id: Optional[str] = None):
        super().__init__(
            default_object_class=GlobalSetting,
            app_name=app_name,
            deployment_id=deployment_id,
        )

    def all(self) -> List[GlobalSetting]:
        """
        Get all settings
        """
        return self._all_objects()

    def delete(self, setting: GlobalSetting) -> None:
        """
        Delete a setting

        Arguments:
            setting: The setting to delete
        """
        self.delete_object(setting)

    def get(self, namespace: str, setting_key: str) -> Union[GlobalSetting, None]:
        """
        Get a setting by namespace and setting key

        Arguments:
            namespace: The namespace of the setting
            setting_key: The setting key
        """
        return self.get_object(
            partition_key_value=namespace,
            sort_key_value=setting_key,
        )

    def put(self, setting: GlobalSetting) -> GlobalSetting:
        """
        Put a setting

        Arguments:
            setting: The setting to put
        """
        return self.put_object(setting)

    def scan(self, scan_definition: TableScanDefinition) -> List[TableObject]:
        """
        Scan for settings

        Keyword Arguments:
            scan_definition: The scan definition
        """
        return self.full_scan(scan_definition)