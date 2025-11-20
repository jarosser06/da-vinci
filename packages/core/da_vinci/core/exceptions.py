"""All Da Vinci Base Exceptions"""


class DuplicateRouteDefinitionError(Exception):
    def __init__(self, route_name: str) -> None:
        """
        Base error for the Da Vinci framework REST Service Base class

        Indicates that a route definition already exists

        Keyword Arguments:
            route_name (str): The name of the route that already exists
        """
        super().__init__(f"Route definition for {route_name} already exists")


class GlobalSettingsNotEnabledError(Exception):
    def __init__(self) -> None:
        """
        Indicates that global settings are not enabled
        """
        super().__init__("Attempting to access global settings when they are not enabled")


class GlobalSettingNotFoundError(Exception):
    def __init__(self, setting_key: str, namespace: str) -> None:
        """
        Indicates that a global setting was not found

        Keyword Arguments:
            setting_key (str): The key of the setting that was not found
            namespace (str): The namespace of the setting that was not found
        """
        super().__init__(f"Setting {setting_key} in namespace {namespace} not found")


class MissingRequiredRuntimeVariableError(RuntimeError):
    def __init__(self, variable_name: str) -> None:
        """
        Indicates that a required runtime variable used by the Da Vinci framework was not found

        Keyword Arguments:
            variable_name (str): The name of the variable that was not found
        """
        super().__init__(f"Required runtime variable {variable_name} not found")


class ResourceNotFoundError(Exception):
    def __init__(self, resource_name: str, resource_type: str) -> None:
        """
        Resource was not able to be located using Da Vinci resource discovery

        Keyword Arguments:
            resource_name (str): The name of the resource that was not found
            resource_type (str): The type of resource that was not found
        """
        super().__init__(f"Resource {resource_name} of type {resource_type} not found")
