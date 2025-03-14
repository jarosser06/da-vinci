from os import getenv
from typing import Any, Union

from da_vinci.core.exceptions import GlobalSettingsNotEnabledError, GlobalSettingNotFoundError
from da_vinci.core.orm.client import TableClient
from da_vinci.core.tables.global_settings import GlobalSetting, GlobalSettings

SETTINGS_ENABLED_VAR_NAME = 'DaVinciFramework_GlobalSettingsEnabled'

cache = {}

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
        table_object_class=GlobalSetting
    )


def setting_value(namespace: str, setting_key: str, skip_cache: bool = False) -> Union[Any, None]:
    """
    Retrieve a setting value as the correct Python type, given
    a namespace and key

    Arguments:
        setting_key: The setting key
        namespace: The namespace of the setting
    """
    cache_key = f'{namespace}.{setting_key}'
    if not skip_cache and cache_key in cache:
        return cache[cache_key]

    if not global_settings_available():
        raise GlobalSettingsNotEnabledError()

    settings = GlobalSettings()

    setting = settings.get(
        namespace=namespace,
        setting_key=setting_key
    )

    if setting:
        value = setting.value_as_type()
        if not skip_cache:
            cache[cache_key] = value
        return value
    else:
        raise GlobalSettingNotFoundError(
            namespace=namespace,
            setting_key=setting_key,
        )
