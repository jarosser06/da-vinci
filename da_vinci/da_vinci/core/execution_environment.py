import os

from da_vinci.core.exceptions import MissingRequiredRuntimeVariableError


APP_NAME_ENV_NAME = "DA_VINCI_APP_NAME"
DEPLOYMENT_ID_ENV_NAME = "DA_VINCI_DEPLOYMENT_ID"
SERVICE_DISC_STOR_ENV_NAME = "DA_VINCI_RESOURCE_DISCOVERY_STORAGE"


REQUIRED_RUNTIME_VARIABLES = (
    APP_NAME_ENV_NAME,
    DEPLOYMENT_ID_ENV_NAME,
    SERVICE_DISC_STOR_ENV_NAME,
)

__APP_USAGE_VAR_NAMES = {
    APP_NAME_ENV_NAME: "app_name",
    DEPLOYMENT_ID_ENV_NAME: "deployment_id",
    SERVICE_DISC_STOR_ENV_NAME: "resource_discovery_storage",
}


def validate_expected_environment_variables() -> None:
    """
    Validate that all expected runtime environment variables are present
    """
    for env_name in REQUIRED_RUNTIME_VARIABLES:
        if env_name not in os.environ:
            raise MissingRequiredRuntimeVariableError(f"Environment variable {env_name} not found")


def runtime_environment_dict(
    app_name: str, deployment_id: str, resource_discovery_storage: str, log_level: str | None = None
) -> dict:
    """
    Return runtime environment variables as a dictionary

    Keyword Arguments:
        app_name: Name of the application
        deployment_id: Identifier assigned to the installation
        resource_discovery_storage: Storage location for service discovery
        log_level: Logging level to use for the application (default: INFO)
    """
    result = {
        APP_NAME_ENV_NAME: app_name,
        DEPLOYMENT_ID_ENV_NAME: deployment_id,
        SERVICE_DISC_STOR_ENV_NAME: resource_discovery_storage,
    }

    if log_level:
        result["LOG_LEVEL"] = log_level

    return result


def load_runtime_environment_variables(
    variable_names: tuple[str, str, str] = REQUIRED_RUNTIME_VARIABLES,
) -> dict:
    """
    Load all requested runtime environment variables into a dictionary, the dictionary keys match
    the app usage names for the common variables.

    Keyword Arguments:
        variable_names: List of environment variable names to load (default: _REQUIRED_RUNTIME_VARIABLES)
    """
    unsupported = set(variable_names).difference(set(REQUIRED_RUNTIME_VARIABLES))

    if unsupported:
        raise ValueError(f"Unsupported runtime variables requested: {unsupported}")

    results: dict = {}

    for variable_name in variable_names:
        if variable_name not in os.environ:
            raise MissingRequiredRuntimeVariableError(variable_name)

        app_usage_name = __APP_USAGE_VAR_NAMES[variable_name]

        results[app_usage_name] = os.environ[variable_name]

    return results
