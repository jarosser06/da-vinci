import json
import logging

from copy import deepcopy
from dataclasses import asdict, dataclass
from enum import auto, StrEnum
from typing import Any, Dict, List, Optional, Union, Type

from da_vinci.core.orm import (
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
)

from da_vinci.core.json import DateTimeEncoder


class MissingAttributeError(Exception):
    def __init__(self, attribute_name: str):
        super().__init__(f'Missing required attribute {attribute_name}')


@dataclass
class ObjectBodyValidationResults:
    """
    ObjectBodyValidationResults is a class that represents the
    results of validating a Python dictionary against a given schema.

    Keyword Arguments:
        missing_attributes: List of mising attributes
        mismatched_types: List of mismatched types
        valid: Whether the object is valid
    """
    mismatched_types: List[str] = None
    missing_attributes: List[str] = None
    valid: bool = True

    def to_dict(self):
        """
        Convert the results to a dictionary

        Returns:
            Dictionary representation of the results
        """
        return asdict(self)


class InvalidObjectSchemaError(Exception):
    def __init__(self, validation_results: ObjectBodyValidationResults):
        message = ['Invalid object schema:']

        if validation_results.missing_attributes:
            message.append(f' missing attributes: {validation_results.missing_attributes}')

        if validation_results.mismatched_types:
            message.append(' mismatched types {validation_results.mismatched_types}')

        message = ' '.join(message)

        super().__init__(message)


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
    default_value: Any = None
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
            default=self.default_value,
            description=self.description,
            optional=self.required
        )

    def to_dict(self) -> Dict:
        """
        Convert the attribute to a dictionary

        Returns:
            Dictionary representation of the attribute
        """
        return asdict(self)


@dataclass
class ObjectBodySchema:
    """
    ObjectBodySchema is a class that represents the schema of an
    event/object body.

    Keyword Arguments:
        attributes: List of attributes in the schema
        description: Description of the schema

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
    name: Optional[str] = None

    def to_dict(self) -> Dict:
        """
        Convert the schema to a dictionary

        Returns:
            Dictionary representation of the schema
        """
        return {
            'attributes': [attribute.to_dict() for attribute in self.attributes],
            'description': self.description,
            'name': self.name,
        }

    def table_object(self) -> TableObject:
        """
        Returns a TableObject that represents the schema.

        Only supports very basic table definitions for now.
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

    def validate_object(self, obj: Dict) -> ObjectBodyValidationResults:
        """
        Validate an object against the schema

        Keyword Arguments:
            obj: Object to validate

        Returns:
            ObjectBodyValidationResults
        """
        missing_attributes = []

        mismatched_types = []

        for attribute in self.attributes:
            if attribute.required and attribute.name not in obj:
                missing_attributes.append(attribute.name)

            elif attribute.name in obj:
                value = obj[attribute.name]

                # Skip None values, as they are valid for optional attributes
                if value is None:
                    continue

                if attribute.type == SchemaAttributeType.OBJECT:
                    if not isinstance(value, dict):
                        mismatched_types.append(attribute.name)

                    else:
                        object_schema = attribute.object_schema

                        # Skip validation if the object schema is not defined, nothing to validate against
                        if not object_schema:
                            continue

                        results = object_schema.validate_object(value)

                        if not results.valid:
                            missing_attributes.extend(results.missing_attributes)

                            mismatched_types.extend(results.mismatched_types)

                elif attribute.type == SchemaAttributeType.OBJECT_LIST:
                    if not isinstance(value, list):
                        mismatched_types.append(attribute.name)

                    else:
                        object_schema = attribute.object_schema

                        for item in value:
                            results = object_schema.validate_object(item)

                            if not results.valid:
                                missing_attributes.extend(results.missing_attributes)

                                mismatched_types.extend(results.mismatched_types)

                elif attribute.type == SchemaAttributeType.STRING_LIST:
                    if not isinstance(value, list):
                        mismatched_types.append(attribute.name)

                    # Only sampling the first element to determine the type
                    elif len(value) > 0 and isinstance(value[0], str):
                        mismatched_types.append(attribute.name)

                elif attribute.type == SchemaAttributeType.NUMBER_LIST:
                    if not isinstance(value, list):
                        mismatched_types.append(attribute.name)

                    elif len(value) > 0 and not isinstance(value[0], int) and not isinstance(value[0], float):
                        mismatched_types.append(attribute.name)

                elif attribute.type == SchemaAttributeType.BOOLEAN:
                    if not isinstance(value, bool):
                        mismatched_types.append(attribute.name)

                elif attribute.type == SchemaAttributeType.NUMBER:
                    if not isinstance(value, int) and not isinstance(value, float):
                        mismatched_types.append(attribute.name)

                elif attribute.type == SchemaAttributeType.STRING:
                    if not isinstance(value, str):
                        mismatched_types.append(attribute.name)

        valid_obj = len(missing_attributes) == 0 and len(mismatched_types) == 0

        return ObjectBodyValidationResults(
            missing_attributes=missing_attributes,
            mismatched_types=mismatched_types,
            valid=valid_obj,
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

    def __init__(self, body: Dict, schema: Union[ObjectBodySchema, Type[ObjectBodySchema]] = None):
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
        self.attributes = {}

        self.unknown_attributes = {}

        self.schema = self._instantiated_schema(schema or self._UNKNOWN_ATTR_SCHEMA)

        self.body = self._load(body)

    @staticmethod
    def _instantiated_schema(schema: Union[Type[ObjectBodySchema], ObjectBodySchema]) -> ObjectBodySchema:
        """
        Checks if the schema is a class or object and instantiates it if it is a class

        Keyword Arguments:
            schema: Schema class or object

        Returns:
            Instantiated schema
        """
        if isinstance(schema, type):
            return schema()

        return schema

    def _load(self, body: Dict):
        """
        Load the event body

        Keyword Arguments:
            body: Body of the event

        Returns:
            Loaded body
        """
        validation = self.schema.validate_object(body)

        if not validation.valid:
            raise InvalidObjectSchemaError(validation)

        remaining_body = deepcopy(body)

        for attribute in self.schema.attributes:
            if attribute.required and attribute.name not in body:
                raise MissingAttributeError(attribute.name)

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
            raise MissingAttributeError(attribute_name)

        if attribute_name in self.attributes:
            return self.attributes[attribute_name].value

        return self.unknown_attributes[attribute_name].value

    def map_to(self, new_schema: Union[ObjectBodySchema, Type[ObjectBodySchema]],
               attribute_map: Optional[Dict] = None) -> 'ObjectBody':
        """
        Map the current event body to a new schema. Currently only support top-level attribute
        mapping. It will default to using an existing attribute name if the new attribute name
        is not found in the attribute map.

        Keyword Arguments:
            schema: Schema to map to
            attribute_map: Attribute map to use, e.g. {'old_name': 'new_name'}
        """
        initialized_schema = self._instantiated_schema(new_schema)

        logging.debug(f'Mapping self attributes to new schema: {initialized_schema.to_dict()}')

        attr_map = attribute_map or {}

        new_body = {}

        for attribute in initialized_schema.attributes:
            if attribute.name in attr_map.values():
                for old_name, new_name in attr_map.items():
                    if new_name == attribute.name:
                        new_body[new_name] = self.get(old_name)

            elif self.has_attribute(attribute.name):
                new_body[attribute.name] = self.get(attribute.name)

        logging.debug(f'Mapped object to new schema: {new_body}')

        return ObjectBody(new_body, new_schema)

    def to_dict(self, ignore_unkown: Optional[bool] = False) -> Dict:
        """
        Convert the object to a dictionary. It will convert nested objects and lists of objects to dictionaries.

        Keyword Arguments:
        ignore_unkown -- Whether to ignore unknown attributes

        Returns:
            Dictionary representation of the object
        """
        if ignore_unkown:
            raw_dict = {attribute.name: attribute.value for attribute in self.attributes.values()}

        else:
            raw_dict = {
                **{attribute.name: attribute.value for attribute in self.attributes.values()},
                **{attribute.name: attribute.value for attribute in self.unknown_attributes.values()}
            }

        flattened_dict = {}

        for key, value in raw_dict.items():
            if isinstance(value, ObjectBody):
                flattened_dict[key] = value.to_dict(ignore_unkown)

            elif isinstance(value, list):
                flattened_dict[key] = [item.to_dict(ignore_unkown) for item in value]

            else:
                flattened_dict[key] = value

        return flattened_dict

    def to_json(self, ignore_unkown: Optional[bool] = False) -> str:
        """
        Convert the object to a JSON string

        Returns:
            JSON representation of the object
        """
        return json.dumps(self.to_dict(ignore_unkown), cls=DateTimeEncoder)