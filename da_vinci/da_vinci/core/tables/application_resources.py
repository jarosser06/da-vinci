'''
Table that acts as an alternative storage for service discovery resources.

Managed by the framework, it is not recommended to mess with this table directly.
'''

from datetime import datetime, UTC as utc_tz
from enum import auto, StrEnum
from typing import Any, List, Optional, Union

from da_vinci.core.orm import (
    TableClient,
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
    TableScanDefinition,
)


class ApplicationResource(TableObject):
    description = 'Application Resources used for Service Discovery'
    table_name = 'application_resources'

    partition_key_attribute = TableObjectAttribute(
        name='resource_type',
        attribute_type=TableObjectAttributeType.STRING,
        description='The type of the resource',
    )

    sort_key_attribute = TableObjectAttribute(
        name='resource_name',
        attribute_type=TableObjectAttributeType.STRING,
        description='The name of the resource',
    )

    attributes = [
        TableObjectAttribute(
            name='last_updated',
            attribute_type=TableObjectAttributeType.DATETIME,
            default=lambda: datetime.now(tz=utc_tz),
            description='The last time the resource was updated',
        ),
    ]


class ApplicationResources(TableClient):
    def __init__(self, app_name: Optional[str] = None, deployment_id: Optional[str] = None):
        super().__init__(
            default_object_class=ApplicationResource,
            app_name=app_name,
            deployment_id=deployment_id,
        )

    def all(self) -> List[ApplicationResource]:
        """
        Get all resources
        """
        return self._all_objects()

    def delete(self, resource: ApplicationResource) -> None:
        """
        Delete a resource

        Keyword Arguments:
            resource: The resource to delete
        """
        self.delete_object(resource)

    def get(self, resource_type: str, resource_name: str) -> Union[ApplicationResource, None]:
        """
        Get a resource by its type and name

        Keyword Arguments:
            resource_type: The type of the resource
            resource_name: The name of the resource
        """
        return self.get_object(
            partition_key_value=resource_type,
            sort_key_value=resource_name,
        )

    def put(self, resource: ApplicationResource) -> ApplicationResource:
        """
        Put a resource

        Keyword Arguments:
            resource: The resource to
        """
        return self.put_object(resource)