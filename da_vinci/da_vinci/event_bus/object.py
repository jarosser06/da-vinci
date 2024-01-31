from copy import deepcopy
from dataclasses import dataclass
from enum import auto, StrEnum
from typing import Any, Dict, List, Optional


from da_vinci.core.orm import (
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
)


class SchemaAttributeType(StrEnum):
    """
    SchemaAttributeType is an enumeration of the types of schema
    attributes.
    """
    STRING = auto()
    NUMBER = auto()
    BOOLEAN = auto()
    DATETIME = auto()
    OBJECT = auto()
    STRING_LIST = auto()
    NUMBER_LIST = auto()
    OBJECT_LIST = auto()

    def to_str(self) -> str:
        return self.name

    @property
    def table_object_attribute_type(self) -> TableObjectAttributeType:
        """
        Convert the schema attribute type to a TableObjectAttributeType
        """
        if self == SchemaAttributeType.STRING:
            return TableObjectAttributeType.STRING

        elif self == SchemaAttributeType.NUMBER:
            return TableObjectAttributeType.NUMBER

        elif self == SchemaAttributeType.BOOLEAN:
            return TableObjectAttributeType.BOOLEAN

        elif self == SchemaAttributeType.DATETIME:
            return TableObjectAttributeType.DATETIME

        elif self == SchemaAttributeType.OBJECT:
            return TableObjectAttributeType.JSON

        elif self == SchemaAttributeType.STRING_LIST:
            return TableObjectAttributeType.STRING_LIST

        elif self == SchemaAttributeType.NUMBER_LIST:
            return TableObjectAttributeType.NUMBER_LIST

        elif self == SchemaAttributeType.OBJECT_LIST:
            return TableObjectAttributeType.OBJECT_LIST


@dataclass
class SchemaAttribute:
    """
    SchemaAttribute is a class that represents an attribute of an
    event body.

    Keyword Arguments:
        description: Description of the attribute 
        name: Name of the attribute
        type: Type of the attribute
        object_schema: Schema of the attribute if it is an object
        required: Whether the attribute is required
    """
    name: str
    type: SchemaAttributeType
    description: str = None
    is_primary_key: bool = False
    object_schema: 'ObjectBodySchema' = None
    required: bool = True

    def table_object_attribute(self) -> TableObjectAttribute:
        """
        Returns a TableObjectAttribute that represents the schema
        attribute.
        """

        return TableObjectAttribute(
            attribute_type=self.type.table_object_attribute_type,
            name=self.name,
            description=self.description,
            optional=self.required
        )


@dataclass
class ObjectBodySchema:
    """
    ObjectBodySchema is a class that represents the schema of an
    event/object body.

    Keyword Arguments:
        attributes: List of attributes in the schema
        description: Description of the schema
        name: Name of the schema

    Example:
        ```
        from da_vinci.event_bus.object import (
            ObjectBodySchema,
            SchemaAttribute,
            SchemaAttributeType,
        )

        schema = ObjectBodySchema(
            attributes=[
                SchemaAttribute(
                    name='my_string',
                    type=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name='my_number',
                    type=SchemaAttributeType.NUMBER,
                ),
                SchemaAttribute(
                    name='my_bool',
                    type=SchemaAttributeType.BOOLEAN,
                ),
                SchemaAttribute(
                    name='my_datetime',
                    type=SchemaAttributeType.DATETIME,
                ),
                SchemaAttribute(
                    name='my_object',
                    type=SchemaAttributeType.OBJECT,
                    object_schema=ObjectBodySchema(
                        attributes=[
                            SchemaAttribute(
                                name='my_string',
                                type=SchemaAttributeType.STRING,
                            ),
                        ]
                    )
                ),
                SchemaAttribute(
                    name='my_string_list',
                    type=SchemaAttributeType.STRING_LIST,
                ),
                SchemaAttribute(
                    name='my_number_list',
                    type=SchemaAttributeType.NUMBER_LIST,
                ),
                SchemaAttribute(
                    name='my_object_list',
                    type=SchemaAttributeType.OBJECT_LIST,
                    object_schema=ObjectBodySchema(
                        attributes=[
                            SchemaAttribute(
                                name='my_string',
                                type=SchemaAttributeType.STRING,
                            ),
                        ]
                    )
                ),
            ]
        )
        ```
    """
    attributes: List[SchemaAttribute]
    description: Optional[str] = None
    name: str = None

    def table_object(self) -> TableObject:
        """
        Returns a TableObject that represents the schema.
        """
        partition_key = None

        attributes = []

        for attribute in self.attributes:
            if attribute.is_primary_key:
                partition_key = attribute.table_object_attribute
            else:
                attributes.append(attribute.table_object_attribute)

        TableObject.define(
            partition_key_attribute=partition_key,
            description=self.description,
        )


@dataclass
class ObjectBodyAttribute:
    name: str
    value: Any
    schema_attribute: SchemaAttribute = None


@dataclass
class ObjectBodyUnknownAttribute(ObjectBodyAttribute):
    required: bool = False

    def __post_init__(self):
        """
        Represents an event body attribute not defined in a schema.

        It will attempt to automatically determine the type of the
        attribute and map it to a SchemaAttributeType.
        """
        if type(self.value) is int or type(self.value) is float:
            schema_type = SchemaAttributeType.NUMBER
        elif type(self.value) is bool:
            schema_type = SchemaAttributeType.BOOLEAN

        elif type(self.value) is dict:
            schema_type = SchemaAttributeType.OBJECT

            self.value = ObjectBody(self.value)

        elif type(self.value) is list:
            if len(self.value) > 0:
                if type(self.value[0]) is str:
                    schema_type = SchemaAttributeType.STRING_LIST

                elif type(self.value[0]) is int or type(self.value[0]) is float:
                    schema_type = SchemaAttributeType.NUMBER_LIST

                elif type(self.value[0]) is dict:
                    schema_type = SchemaAttributeType.OBJECT_LIST

                    self.value = [ObjectBody(item) for item in self.value]
        else:
            schema_type = SchemaAttributeType.STRING

        self.schema_attribute = SchemaAttribute(
            name=self.name,
            required=False,
            type=schema_type,
        )


class ObjectBody:
    _UNKNOWN_ATTR_SCHEMA = ObjectBodySchema(attributes=[], name='UNKNOWN')

    def __init__(self, body: Dict, schema: ObjectBodySchema = None):
        """
        ObjectBody is a class that represents an object in an event

        Keyword Arguments:
            body: Body of the event
            schema: Schema of the event body

        Example:
            ```
            from da_vinci.event_bus.object import (
                ObjectBody,
                ObjectBodySchema,
                SchemaAttribute,
                SchemaAttributeType,
            )

            schema = ObjectBodySchema(
                attributes=[
                    SchemaAttribute(
                        name='my_string',
                        type=SchemaAttributeType.STRING,
                    ),
                    SchemaAttribute(
                        name='my_number',
                        type=SchemaAttributeType.NUMBER,
                    ),
                    SchemaAttribute(
                        name='my_bool',
                        type=SchemaAttributeType.BOOLEAN,
                    ),
                    SchemaAttribute(
                        name='my_datetime',
                        type=SchemaAttributeType.DATETIME,
                    ),
                    SchemaAttribute(
                        name='my_object',
                        type=SchemaAttributeType.OBJECT,
                        object_schema=ObjectBodySchema(
                            attributes=[
                                SchemaAttribute(
                                    name='my_string',
                                    type=SchemaAttributeType.STRING,
                                ),
                            ]
                        )
                    ),
                    SchemaAttribute(
                        name='my_string_list',
                        type=SchemaAttributeType.STRING_LIST,
                    ),
                    SchemaAttribute(
                        name='my_number_list',
                        type=SchemaAttributeType.NUMBER_LIST,
                    ),
                    SchemaAttribute(
                        name='my_object_list',
                        type=SchemaAttributeType.OBJECT_LIST,
                        object_schema=ObjectBodySchema(
                            attributes=[
                                SchemaAttribute(
                                    name='my_string',
                                    type=SchemaAttributeType.STRING,
                                ),
                            ]
                        )
                    ),
                ]
            )

            body = ObjectBody(
                body={
                    'my_string': 'my_string',
                    'my_number': 1,
                    'my_bool': True,
                    'my_datetime': datetime.now(),
                    'my_object': {
                        'my_string': 'my_string',
                    },
                    'my_string_list': ['my_string'],
                    'my_number_list': [1],
                    'my_object_list': [
                        {
                            'my_string': 'my_string',
                        }
                    ],
                },
                schema=schema,
            )
            ```
        """
        self.body = self._load(body)
        self.schema = schema or self._UNKNOWN_ATTR_SCHEMA

        self.attributes = {}
        self.unknown_attributes = {}

    def _load(self, body: Dict):
        """
        Load the event body

        Keyword Arguments:
            body: Body of the event

        Returns:
            Loaded body
        """
        remaining_body = deepcopy(body)

        for attribute in self.schema.attributes:
            value = body[attribute.name]

            if attribute.type == SchemaAttributeType.OBJECT:
                value = ObjectBody(value, attribute.object_schema)

            elif attribute.type == SchemaAttributeType.OBJECT_LIST:
                value = [ObjectBody(item, attribute.object_schema) for item in value]

            self.attributes[attribute.name] = ObjectBodyAttribute(
                name=attribute.name,
                schema_attribute=attribute,
                value=value
            )

            del remaining_body[attribute.name]

        if remaining_body:
            for key, value in remaining_body.items():
                self.unknown_attributes[key] = ObjectBodyUnknownAttribute(
                    name=key,
                    value=value
                )

    def has_attribute(self, attribute_name: str) -> bool:
        """
        Check if the event body has an attribute

        Keyword Arguments:
            attribute_name: Name of the attribute

        Returns:
            Whether the event body has the attribute
        """

        return attribute_name in self.attributes or attribute_name in self.unknown_attributes

    def get(self, attribute_name: str) -> Any:
        """
        Get an attribute from the event body

        Keyword Arguments:
            attribute_name: Name of the attribute

        Returns:
            Attribute value
        """
        if not self.has_attribute(attribute_name):
            raise Exception(f'Object does not have attribute {attribute_name}')

        if attribute_name in self.attributes:
            return self.attributes[attribute_name].value

        return self.unknown_attributes[attribute_name].value

    def map_to(self, new_schema: ObjectBodySchema,
               attribute_map: Optional[Dict] = None) -> 'ObjectBody':
        """
        Map the current event body to a new schema

        Keyword Arguments:
            schema: Schema to map to
            attribute_map: Attribute map to use, e.g. {'old_name': 'new_name'}
        """

        attr_map = attribute_map or {}

        new_body = {}

        for attribute in new_schema.attributes:
            if attribute.name in attr_map.values():
                for old_name, new_name in attr_map.items():
                    if new_name == attribute.name:
                        new_body[new_name] = self.get(old_name)

            elif attribute.name in self.attributes:
                new_body[attribute.name] = self.get(attribute.name)

        return ObjectBody(new_body, new_schema)


    def to_dict(self) -> Dict:
        """
        Convert the object to a dictionary

        Returns:
            Dictionary representation of the object
        """
        return {
            **{attribute.name: attribute.value for attribute in self.attributes.values()},
            **{attribute.name: attribute.value for attribute in self.unknown_attributes.values()}
        }