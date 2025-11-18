from datetime import UTC as utc_tz
from datetime import datetime
from uuid import uuid4

from da_vinci.core.orm.client import (
    TableClient,
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
)


class ExampleTableObject(TableObject):
    table_name = "example_table"

    description = "Basic ORM Table Object"

    partition_key_attribute = TableObjectAttribute(
        name="primary_key",
        type=TableObjectAttributeType.STRING,
        description="Primary Key",
        default=lambda: str(uuid4()),
    )

    attributes = [
        TableObjectAttribute(
            name="created_at",
            type=TableObjectAttributeType.DATETIME,
            description="Created At",
            default=lambda: datetime.now(utc_tz),
        ),

        TableObjectAttribute(
            name="updated_at",
            type=TableObjectAttributeType.DATETIME,
            description="Updated At",
            default=lambda: datetime.now(utc_tz),
        ),

        TableObjectAttribute(
            name="name",
            type=TableObjectAttributeType.STRING,
            description="Name",
        ),

        TableObjectAttribute(
            name="age",
            type=TableObjectAttributeType.NUMBER,
            description="Age",
            optional=True,
        ),

        TableObjectAttribute(
            name="is_active",
            type=TableObjectAttributeType.BOOLEAN,
            description="Is Active",
            default=True,
        ),

        TableObjectAttribute(
            name="metadata",
            type=TableObjectAttributeType.JSON,
            description="Other metadata, converts to a DynamoDB MAP",
            default={},
        ),

        TableObjectAttribute(
            name="tags",
            type=TableObjectAttributeType.STRING_LIST,
            description="Tags",
            default=[],
        ),
    ]


class ExampleTableClient(TableClient):
    def __init__(self, app_name: str | None = None, deployment_id: str | None = None):
        super().__init__(
            app_name=app_name,
            deployment_id=deployment_id,
            default_object_class=ExampleTableObject
        )

    def get(self, primary_key: str) -> ExampleTableObject | None:
        """
        Get an object by primary key
        """
        return self.get_object(partition_key_value=primary_key)

    def delete(self, obj: ExampleTableObject) -> None:
        """
        Delete an object
        """
        self.delete_object(obj=obj)

    def put(self, obj: ExampleTableObject) -> None:
        """
        Put an object
        """
        self.put_object(obj=obj)
