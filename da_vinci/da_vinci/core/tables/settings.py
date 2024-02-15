'''Settings Table Definitions'''

from datetime import datetime
from enum import auto, StrEnum
from typing import Any, List, Optional, Union

from da_vinci.core.orm import (
    TableClient,
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
    TableScanDefinition,
)


class SettingType(StrEnum):
    """Setting Types"""
    BOOLEAN = auto()
    FLOAT = auto()
    INTEGER = auto()
    STRING = auto()


def _execute_on_update(table_object: 'Setting'):
    """
    Execute on update hook for the Event Bus Subscription object.

    Keyword Arguments:
        table_object: The table object to update
    """
    table_object.update_date_attributes(
        date_attribute_names=['last_updated'],
        obj=table_object,
    )


class Setting(TableObject):
    description = 'Application Settings'
    execute_on_update = _execute_on_update
    table_name = 'global_settings'

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
            default=lambda: datetime.utcnow(),
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
            last_updated: The last time the setting was updated, defaults to datetime.utcnow()
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
                last_updated=datetime.utcnow(),
                namespace='core',
                setting_key='global_settings_enabled',
                setting_type=SettingType.BOOLEAN,
                setting_value=True,
            )
            ```
        """
        if isinstance(kwargs.get('setting_type'), SettingType):
            kwargs['setting_type'] = kwargs['setting_type'].name

        # Ensure the setting value is a string
        if not isinstance(kwargs.get('setting_value'), str):
            kwargs['setting_value'] = str(kwargs['setting_value'])

        super().__init__(**kwargs)

    def value_as_type(self) -> Any:
        """
        Return the setting value as the correct type
        """
        if self.setting_type == SettingType.BOOLEAN:
            return self.setting_value.lower() == 'true'
        elif self.setting_type == SettingType.FLOAT:
            return float(self.setting_value)
        elif self.setting_type == SettingType.INTEGER:
            return int(self.setting_value)
        
        return self.setting_value


class SettingsScanDefinition(TableScanDefinition):
    def __init__(self):
        super().__init__(table_object_class=Setting)


class Settings(TableClient):
    def __init__(self, app_name: Optional[str] = None, deployment_id: Optional[str] = None):
        super().__init__(
            default_object_class=Setting,
            app_name=app_name,
            deployment_id=deployment_id,
        )

    def all(self) -> List[Setting]:
        """
        Get all settings
        """
        return self._all_objects()

    def delete(self, setting: Setting) -> None:
        """
        Delete a setting

        Arguments:
            setting: The setting to delete
        """
        self.remove_object(setting)

    def get(self, namespace: str, setting_key: str) -> Union[Setting, None]:
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

    def put(self, setting: Setting) -> Setting:
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