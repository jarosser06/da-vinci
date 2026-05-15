"""ORM definition for the parent application's ``people`` table.

The sidecar deliberately does NOT own this table — it belongs to the parent
app's OrmStack. This definition mirrors the parent's schema (same
``table_name`` and attributes) so the sidecar can read/write the parent's
table through a granted ResourceAccessRequest, proving cross-application
resource use.
"""

from uuid import uuid4

from da_vinci.core.orm.client import TableClient
from da_vinci.core.orm.table_object import (
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
)


class PersonTableObject(TableObject):
    table_name = "people"

    description = "People table for the da_vinci integration test app"

    partition_key_attribute = TableObjectAttribute(
        name="person_id",
        attribute_type=TableObjectAttributeType.STRING,
        description="Unique person identifier",
        default=lambda: str(uuid4()),
    )

    attributes = [
        TableObjectAttribute(
            name="name",
            attribute_type=TableObjectAttributeType.STRING,
            description="Person's display name",
        ),
        TableObjectAttribute(
            name="age",
            attribute_type=TableObjectAttributeType.NUMBER,
            description="Age in years",
            optional=True,
        ),
        TableObjectAttribute(
            name="tags",
            attribute_type=TableObjectAttributeType.STRING_LIST,
            description="Arbitrary tags",
            default=[],
        ),
    ]


class PersonTableClient(TableClient):
    def __init__(self) -> None:
        super().__init__(default_object_class=PersonTableObject)

    def get(self, person_id: str) -> TableObject | None:
        return self.get_object(partition_key_value=person_id)

    def put(self, person: PersonTableObject) -> None:
        self.put_object(table_object=person)
