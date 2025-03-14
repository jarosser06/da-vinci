'''Resource Registry Table Definition'''

from datetime import datetime, UTC as utc_tz

from da_vinci.core.orm import (
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
)

from da_vinci.core.global_settings import setting_value


class ResourceRegistration(TableObject):
    description = 'Resource Registry'

    table_name = 'resource_registry'

    partition_key_attribute = TableObjectAttribute(
        name='resource_type',
        attribute_type=TableObjectAttributeType.STRING,
        description='The type of the resource',
    )

    sort_key_attribute = TableObjectAttribute(
        name='resource_name',
        attribute_type=TableObjectAttributeType.STRING,
        description='The unique global name of the resource',
    )

    attributes = [
        TableObjectAttribute(
            name='created_on',
            attribute_type=TableObjectAttributeType.DATETIME,
            description='The date and time the resource was registered',
            default_value=lambda: datetime.now(tz=utc_tz),
        ),

        TableObjectAttribute(
            name='endpoint',
            attribute_type=TableObjectAttributeType.STRING,
            description='The endpoint where the resource can be reached',
        ),
    ]