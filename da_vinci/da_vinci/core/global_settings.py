from os import getenv
from typing import Union

from da_vinci.core.exceptions import GlobalSettingsNotEnabledError, GlobalSettingNotFoundError
from da_vinci.core.orm.client import TableClient
from da_vinci.core.tables.settings import Setting, Settings

SETTINGS_ENABLED_VAR_NAME = 'DaVinciFramework_GlobalSettingsEnabled'


def global_settings_available() -> bool:
    """
    Check if global settings are available

    Try the environment variable first, then check if the settings table exists
    if the environment variable is not set.
    """
    env_var = getenv(SETTINGS_ENABLED_VAR_NAME)

    if env_var is not None:
        return env_var.lower() == 'true'

    return TableClient.table_resource_exists(
        table_object_class=Setting
    )


def setting_value(setting_key: str, namespace: str) -> Union[Setting, None]:
    """
    Retrieve a setting value as the correct Python type, given
    a namespace and key

    Arguments:
        key: The setting key
        namespace: The namespace of the setting
    """

    if not global_settings_available():
        raise GlobalSettingsNotEnabledError()

    settings = Settings()

    setting = settings.get(
        namespace=namespace,
        setting_key=setting_key
    )

    if setting:
        return setting.value_as_type()
    else:
        raise GlobalSettingNotFoundError(
            namespace=namespace,
            setting_key=setting_key,
        )