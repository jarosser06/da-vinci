"""
The code in this module defines the ObjectBody and ObjectBodySchema classes, which are used to represent
schema capable immutable objects. These classes provide functionality for validating, serializing, and deserializing
objects against a defined schema. The schema can include various attribute types such as strings, numbers,
booleans, datetimes, and nested objects. The ObjectBody class is designed to be immutable, meaning that once
an object is created, its attributes cannot be modified.


The Schema supports multiple ways to control the requiredness of an attribute. The default is to require the attribute
but, you can set the required flag to False. You can also use the required_conditions flag to specify a list of
conditions that must be met for the attribute to be required.

Example:
    ```
    from da_vinci.core.immutable_object import (
        ObjectBody,
        ObjectBodySchema,
        SchemaAttribute,
        SchemaAttributeType,
    )
    schema = ObjectBodySchema(
        attributes=[
            SchemaAttribute(
                name='my_string',
                type_name=SchemaAttributeType.STRING,
            ),
            SchemaAttribute(
                name='my_number',
                type_name=SchemaAttributeType.NUMBER,
            ),
            SchemaAttribute(
                name='execution_type',
                type_name=SchemaAttributeType.STRING,
                enum=['type1', 'type2'],
            ),
            SchemaAttribute(
                name='execution_type_2_req_arg',
                type_name=SchemaAttributeType.STRING,
                required_conditions=[
                    {
                        'operator': 'equals',
                        'param': 'execution_type',
                        'value': 'type1',
                    },
                ]
            ),
            SchemaAttribute(
                name='execution_type_2_opt_arg',
                type_name=SchemaAttributeType.STRING,
            )
        ]
    )

    body = ObjectBody(
        body={
            'my_string': 'my_string',
            'my_number': 1,
            'execution_type': 'type1',
        },
        schema=schema,
    )

    print(body.get('my_string'))  # my_string

    print(body.get('my_number'))  # 1

    print(body.get('execution_type'))  # type1

    print(body.get('execution_type_2_req_arg'))  # None

    ```


**Note**: This module becomes all consuming and any object cast to an ObjectBody will be completely consumed including any sub-objects
and lists of objects. Everything that looks like an object will be cast to an ObjectBody. This is done to ensure that the object is immutable and
that the schema is enforced. This is a trade off that is made to ensure that the object is immutable and that the schema is enforced.
"""

import logging
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass
from enum import StrEnum, auto
from typing import Any, Union

from da_vinci.core.orm.client import (
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
)


class MissingAttributeError(Exception):
    def __init__(self, attribute_name: str):
        super().__init__(f"Missing required attribute {attribute_name}")


class SchemaDeclarationError(Exception):
    def __init__(self, message: str):
        super().__init__(f"Schema declaration error: {message}")


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

    validated_body: dict
    mismatched_types: list[str] = None
    missing_attributes: list[str] = None
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
        message = ["Invalid object schema:"]

        if validation_results.missing_attributes:
            message.append(f" missing attributes: {validation_results.missing_attributes}")

        if validation_results.mismatched_types:
            message.append(f" mismatched types {validation_results.mismatched_types}")

        message = " ".join(message)

        super().__init__(message)


class SchemaAttributeType(StrEnum):
    """
    SchemaAttributeType is an enumeration of the types of schema
    attributes.
    """

    ANY = auto()
    STRING = auto()
    NUMBER = auto()
    BOOLEAN = auto()
    DATETIME = auto()
    OBJECT = auto()
    LIST = auto()
    STRING_LIST = auto()
    NUMBER_LIST = auto()
    OBJECT_LIST = auto()
    UNKNOWN_OBJECT_TYPE = auto()
    UNKNOWN_OBJECT_TYPE_LIST = auto()

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
            return TableObjectAttributeType.JSON_STRING

        elif self == SchemaAttributeType.STRING_LIST or self == SchemaAttributeType.LIST:
            return TableObjectAttributeType.STRING_LIST

        elif self == SchemaAttributeType.NUMBER_LIST:
            return TableObjectAttributeType.NUMBER_LIST

        elif self == SchemaAttributeType.OBJECT_LIST:
            return TableObjectAttributeType.JSON_STRING_LIST


@dataclass
class RequiredCondition:
    """
    RequiredCondition is a class that represents a condition
    that must be met for an attribute to be required.

    Keyword Arguments:
        operator: Operator to use for the condition
        param: Parameter to check against
        value: Value to check against
    """

    param: str
    operator: str = "equals"
    value: Any = None

    def to_dict(self) -> dict:
        """
        Convert the condition to a dictionary

        Returns:
            Dictionary representation of the condition
        """
        return asdict(self)


@dataclass
class RequiredConditionGroup:
    """
    RequiredConditionGroup is a class that represents a group of
    conditions that must be met for an attribute to be required.

    Keyword Arguments:
        group_operator: Operator to use for the group
        conditions: List of conditions in the group
    """

    group_operator: str
    conditions: list[RequiredCondition]

    def to_dict(self) -> dict:
        """
        Convert the group to a dictionary

        Returns:
            Dictionary representation of the group
        """
        return asdict(self)


@dataclass
class SchemaAttribute:
    """
    SchemaAttribute is a class that represents an attribute of an schema

    Keyword Arguments:
        description: Description of the attribute
        name: Name of the attribute
        type: Type of the attribute
        object_schema: Schema of the attribute if it is an object
        required: Whether the attribute is required
    """

    name: str
    type_name: SchemaAttributeType
    default_value: Any = None
    description: str = None
    enum: list[Any] = None
    is_primary_key: bool = False
    object_schema: "ObjectBodySchema" = None
    regex_pattern: str = None
    required: bool = True
    required_conditions: list[dict | RequiredCondition | RequiredConditionGroup] = None
    secret: bool = False

    def __post_init__(self):
        """
        Post init method to convert the required_conditions to a list of
        RequiredCondition objects
        """
        if self.required_conditions:
            normalized_conditions = []

            for condition in self.required_conditions:
                if isinstance(condition, dict):
                    normalized_conditions.append(condition)

                elif isinstance(condition, RequiredCondition) or isinstance(
                    condition, RequiredConditionGroup
                ):
                    normalized_conditions.append(condition.to_dict())

            self.required_conditions = normalized_conditions

    def is_required(self, parameter_values: dict[str, Any]) -> bool:
        """
        Determine if the attribute is required based on the flag and any
        required_conditions.

        Keyword arguments:
        parameter_values -- Dictionary of parameter values to check against

        Returns:
            Whether the attribute is required
        """
        if self.required:
            if self.required_conditions:
                return self._evaluate_required_conditions(parameter_values)

            return True

        return False

    def _evaluate_required_conditions(self, parameter_values: dict) -> bool:
        """
        Evaluate a list of condition objects to determine if parameter is required

        Keyword arguments:
        parameter_values -- Dictionary of parameter values to check against

        Returns:
            True if all conditions are met (AND logic), False otherwise
        """
        for condition in self.required_conditions:
            # Handle condition groups with their own operator
            if "group_operator" in condition:

                group_result = self._evaluate_condition_group(condition, parameter_values)

                if not group_result:

                    return False

            # Handle individual conditions
            elif not self._evaluate_single_condition(condition, parameter_values):
                return False

        return True

    def _evaluate_condition_group(self, group: dict, parameter_values: dict) -> bool:
        """
        Evaluate a group of conditions based on group_operator

        Keyword arguments:
        group -- Dictionary representing the group of conditions
        parameter_values -- Dictionary of parameter values to check against

        Returns:
            Result of evaluating the group
        """
        operator = group.get("group_operator", "and")

        conditions = group.get("conditions", [])

        if operator == "or":
            # OR logic - return True if any condition is True
            return any(
                self._evaluate_single_condition(cond, parameter_values) for cond in conditions
            )
        else:
            # Default to AND logic - return False if any condition is False
            return all(
                self._evaluate_single_condition(cond, parameter_values) for cond in conditions
            )

    def _evaluate_single_condition(self, condition: dict, parameter_values: dict) -> bool:
        """
        Evaluate a single condition object

        Keyword arguments:
        condition -- Dictionary representing the condition
        parameter_values -- Dictionary of parameter values to check against

        Returns:
            Result of evaluating the condition
        """
        op = condition.get("operator", "equals")

        param = condition.get("param")

        value = condition.get("value")

        # Parameter doesn't exist in values
        if param not in parameter_values or parameter_values[param] is None:
            return op == "not_exists"

        param_value = parameter_values[param]

        # Evaluate based on operator
        if op == "exists":
            return param_value is not None

        elif op == "not_exists":
            return param_value is None

        elif op == "equals":
            return param_value == value

        elif op == "not_equals":
            return param_value != value

        elif op == "gt":
            return param_value > value

        elif op == "gte":
            return param_value >= value

        elif op == "lt":
            return param_value < value

        elif op == "lte":
            return param_value <= value

        elif op == "in":
            return param_value in value

        elif op == "not_in":
            return param_value not in value

        elif op == "contains":
            return value in param_value

        elif op == "starts_with":
            return str(param_value).startswith(str(value))

        elif op == "ends_with":
            return str(param_value).endswith(str(value))

        # Unknown operator
        return False

    def table_object_attribute(self) -> TableObjectAttribute:
        """
        Returns a TableObjectAttribute that represents the schema
        attribute.
        """

        return TableObjectAttribute(
            attribute_type=self.type_name.table_object_attribute_type,
            type_name=self.name,
            default=self.default_value,
            description=self.description,
            optional=not self.required,
        )

    def to_dict(self) -> dict:
        """
        Convert the attribute to a dictionary

        Returns:
            Dictionary representation of the attribute
        """
        return asdict(self)


class ObjectBodySchema:
    """
    ObjectBodySchema is a class that represents the schema of an
    event/object body.

    Keyword Arguments:
        attributes: List of attributes in the schema
        description: Description of the schema
        name: Name of the schema
        vanity_types: Dictionary of vanity types

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
                    type_name=SchemaAttributeType.STRING,
                ),
                SchemaAttribute(
                    name='my_number',
                    type_name=SchemaAttributeType.NUMBER,
                ),
                SchemaAttribute(
                    name='my_bool',
                    type_name=SchemaAttributeType.BOOLEAN,
                ),
                SchemaAttribute(
                    name='my_datetime',
                    type_name=SchemaAttributeType.DATETIME,
                ),
                SchemaAttribute(
                    name='my_object',
                    type_name=SchemaAttributeType.OBJECT,
                    object_schema=ObjectBodySchema(
                        attributes=[
                            SchemaAttribute(
                                name='my_string',
                                type_name=SchemaAttributeType.STRING,
                            ),
                        ]
                    )
                ),
                SchemaAttribute(
                    name='my_string_list',
                    type_name=SchemaAttributeType.STRING_LIST,
                ),
                SchemaAttribute(
                    name='my_number_list',
                    type_name=SchemaAttributeType.NUMBER_LIST,
                ),
                SchemaAttribute(
                    name='my_object_list',
                    type_name=SchemaAttributeType.OBJECT_LIST,
                    object_schema=ObjectBodySchema(
                        attributes=[
                            SchemaAttribute(
                                name='my_string',
                                type_name=SchemaAttributeType.STRING,
                            ),
                        ]
                    )
                ),
            ]
        )
        ```
    """

    attributes: list[SchemaAttribute]
    description: str | None = None
    name: str | None = None
    vanity_types: dict[str, str | SchemaAttributeType] | None = None

    @classmethod
    def from_dict(cls, object_name: str, schema_dict: dict) -> "ObjectBodySchema":
        """
        Create a schema from a dictionary

        Keyword Arguments:
            object_name: Name of the dynamically created object
            schema_dict: Dictionary representation of the schema

        Returns:
            New class subclassed from ObjectBodySchema
        """
        attributes = []

        for attribute in schema_dict.get("attributes", []):
            attributes.append(SchemaAttribute(**attribute))

        obj_klass = type(object_name, (cls,), {})

        obj_klass.attributes = attributes

        obj_klass.description = schema_dict.get("description")

        obj_klass.name = schema_dict.get("name")

        obj_klass.vanity_types = schema_dict.get("vanity_types")

        return obj_klass

    @classmethod
    def to_dict(cls) -> dict:
        """
        Convert the schema to a dictionary

        Returns:
            Dictionary representation of the schema
        """
        return {
            "attributes": [attribute.to_dict() for attribute in cls.attributes],
            "description": cls.description,
            "name": cls.name,
            "vanity_types": cls.vanity_types,
        }

    @classmethod
    def table_object(cls) -> TableObject:
        """
        Returns a TableObject that represents the schema.

        Only supports very basic table definitions for now.
        """
        partition_key = None

        attributes = []

        for attribute in cls.attributes:
            if attribute.is_primary_key:
                partition_key = attribute.table_object_attribute

            else:
                attributes.append(attribute.table_object_attribute)

        TableObject.define(
            partition_key_attribute=partition_key,
            description=cls.description,
        )

    @classmethod
    def validate_object(cls, obj: dict) -> ObjectBodyValidationResults:
        """
        Validate an object against the schema

        Keyword Arguments:
            obj: Object to validate

        Returns:
            ObjectBodyValidationResults
        """
        missing_attributes = []

        mismatched_types = []

        compiled_values = {}

        # First, add all default values from schema attributes
        for attribute in cls.attributes:
            if not attribute.required:
                compiled_values[attribute.name] = attribute.default_value

        compiled_values.update(obj)

        for attribute in cls.attributes:
            value = obj.get(attribute.name)

            actual_type_name = attribute.type_name

            logging.debug(
                f"Validating attribute {attribute.name} with value {value} against type {actual_type_name}"
            )

            if cls.vanity_types and attribute.type_name in cls.vanity_types:

                actual_type_name = cls.vanity_types[attribute.type_name]

            if attribute.is_required(parameter_values=compiled_values):
                if attribute.name not in obj or value is None:
                    logging.debug(
                        f"Attribute {attribute.name} is missing entirely or has a None value"
                    )

                    missing_attributes.append(attribute.name)

            if value:
                # Skip None values, as they are valid for optional attributes
                if value is None:
                    continue

                # Both enum and regex do not work together
                if attribute.enum:
                    if value not in attribute.enum:
                        mismatched_types.append(
                            f"{attribute.name} (value not in allowed enum values)"
                        )

                        continue

                elif attribute.regex_pattern:
                    if not actual_type_name == SchemaAttributeType.STRING:
                        raise SchemaDeclarationError(
                            "Regex pattern can only be used with STRING type"
                        )

                    if not re.match(attribute.regex_pattern, value):
                        mismatched_types.append(
                            f"{attribute.name} (value does not match regex pattern {attribute.regex_pattern})"
                        )

                        continue

                if actual_type_name == SchemaAttributeType.ANY:
                    continue

                elif actual_type_name == SchemaAttributeType.OBJECT:
                    if isinstance(value, dict):
                        continue

                    elif isinstance(value, ObjectBody):
                        object_schema = attribute.object_schema

                        # Skip validation if the object schema is not defined, nothing to validate against
                        if not object_schema:
                            continue

                        results = object_schema.validate_object(value)

                        if not results.valid:
                            missing_attributes.extend(results.missing_attributes)

                            mismatched_types.extend(results.mismatched_types)

                    else:
                        mismatched_types.append(attribute.name)

                elif actual_type_name == SchemaAttributeType.LIST:
                    if not isinstance(value, list):
                        mismatched_types.append(attribute.name)

                        continue

                elif actual_type_name == SchemaAttributeType.OBJECT_LIST:
                    if isinstance(value, list):
                        if len(value) > 0 and not isinstance(value[0], (dict, ObjectBody)):
                            mismatched_types.append(attribute.name)

                            continue

                        object_schema = attribute.object_schema

                        for item in value:
                            if not object_schema:
                                continue

                            results = object_schema.validate_object(item)

                            if not results.valid:
                                missing_attributes.extend(results.missing_attributes)

                                mismatched_types.extend(results.mismatched_types)

                    else:
                        mismatched_types.append(attribute.name)

                elif actual_type_name == SchemaAttributeType.STRING_LIST:
                    if isinstance(value, list):
                        if len(value) > 0 and not isinstance(value[0], str):
                            mismatched_types.append(attribute.name)

                        continue

                    else:
                        mismatched_types.append(attribute.name)

                elif actual_type_name == SchemaAttributeType.NUMBER_LIST:
                    if isinstance(value, list):

                        if (
                            len(value) > 0
                            and not isinstance(value[0], int)
                            and not isinstance(value[0], float)
                        ):
                            mismatched_types.append(attribute.name)

                        continue

                    mismatched_types.append(attribute.name)

                elif actual_type_name == SchemaAttributeType.BOOLEAN:
                    if not isinstance(value, bool):
                        mismatched_types.append(attribute.name)

                elif actual_type_name == SchemaAttributeType.NUMBER:
                    if not isinstance(value, int) and not isinstance(value, float):
                        mismatched_types.append(attribute.name)

                elif actual_type_name == SchemaAttributeType.STRING:
                    if not isinstance(value, str):
                        mismatched_types.append(attribute.name)

        valid_obj = len(missing_attributes) == 0 and len(mismatched_types) == 0

        return ObjectBodyValidationResults(
            missing_attributes=missing_attributes,
            mismatched_types=mismatched_types,
            validated_body=compiled_values,
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
        schema_type = None

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

                elif isinstance(self.value[0], ObjectBody):
                    schema_type = SchemaAttributeType.OBJECT_LIST

                else:
                    schema_type = SchemaAttributeType.UNKNOWN_OBJECT_TYPE_LIST

        elif not isinstance(self.value, str):
            schema_type = SchemaAttributeType.UNKNOWN_OBJECT_TYPE

        else:
            schema_type = SchemaAttributeType.STRING

        self.schema_attribute = SchemaAttribute(
            name=self.name,
            required=False,
            type_name=schema_type,
        )


class UnknownAttributeSchema(ObjectBodySchema):
    attributes = []
    name = "UNKNOWN"


class ObjectBody:
    _UNKNOWN_ATTR_SCHEMA = UnknownAttributeSchema

    def __init__(
        self,
        body: Union[dict, "ObjectBody", None] = None,
        schema: ObjectBodySchema | type[ObjectBodySchema] = None,
        secret_masking_fn: Callable[[str], str] | None = None,
    ):
        """
        ObjectBody is a class that represents an object in an event. It comes with support for nested validation
        and full validation against a schema when provided.

        ObjectBody operats similar to a Python Dictionary and supports several native access patterns but, it
        is immutable and cannot be modified.

        Keyword Arguments:
            body: Body of the event
            schema: Schema of the event body
            secret_masking_fn: Function to mask secret values

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
                        type_name=SchemaAttributeType.STRING,
                    ),
                    SchemaAttribute(
                        name='my_number',
                        type_name=SchemaAttributeType.NUMBER,
                    ),
                    SchemaAttribute(
                        name='my_bool',
                        type_name=SchemaAttributeType.BOOLEAN,
                    ),
                    SchemaAttribute(
                        name='my_datetime',
                        type_name=SchemaAttributeType.DATETIME,
                    ),
                    SchemaAttribute(
                        name='my_object',
                        type_name=SchemaAttributeType.OBJECT,
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
                        type_name=SchemaAttributeType.STRING_LIST,
                    ),
                    SchemaAttribute(
                        name='my_number_list',
                        type_name=SchemaAttributeType.NUMBER_LIST,
                    ),
                    SchemaAttribute(
                        name='my_object_list',
                        type_name=SchemaAttributeType.OBJECT_LIST,
                        object_schema=ObjectBodySchema(
                            attributes=[
                                SchemaAttribute(
                                    name='my_string',
                                    type_name=SchemaAttributeType.STRING,
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

        self.schema = schema or self._UNKNOWN_ATTR_SCHEMA

        self.secret_masking_fn = secret_masking_fn

        body_dict = body or {}

        if isinstance(body, ObjectBody):
            body_dict = body.to_dict()

        self._load(body_dict)

    def _load(self, body: dict):
        """
        Load the event body

        Keyword Arguments:
            body: Body of the event

        Returns:
            Loaded body
        """
        schema = self.schema

        if schema is None:
            schema = self._UNKNOWN_ATTR_SCHEMA

        if not body and schema == self._UNKNOWN_ATTR_SCHEMA:
            return

        validation = schema.validate_object(body)

        if not validation.valid:
            raise InvalidObjectSchemaError(validation)

        remaining_body = validation.validated_body

        for attribute in schema.attributes:
            # Somewhat redundant since the default value should have been set during validation
            value = remaining_body.get(attribute.name, attribute.default_value)

            actual_type_name = attribute.type_name

            if schema.vanity_types and attribute.type_name in schema.vanity_types:
                actual_type_name = schema.vanity_types[attribute.type_name]

            if attribute.secret and self.secret_masking_fn:
                value = self.secret_masking_fn(value)

            if actual_type_name == SchemaAttributeType.OBJECT and value:
                value = ObjectBody(value, attribute.object_schema)

            elif actual_type_name == SchemaAttributeType.OBJECT_LIST and value:

                value = [ObjectBody(item, attribute.object_schema) for item in value]

            self.attributes[attribute.name] = ObjectBodyAttribute(
                name=attribute.name, schema_attribute=attribute, value=value
            )

            if attribute.name in remaining_body:
                del remaining_body[attribute.name]

        if remaining_body:
            for key, value in remaining_body.items():
                self.unknown_attributes[key] = ObjectBodyUnknownAttribute(name=key, value=value)

    def __contains__(self, attribute_name: str) -> bool:
        """
        Check if the event body has an attribute

        Keyword arguments:
        attribute_name -- Name of the attribute
        """
        return self.has_attribute(attribute_name)

    def __getitem__(self, attribute_name: str) -> Any:
        """
        Get an attribute from the event body

        Keyword arguments:
        attribute_name -- Name of the attribute
        """
        return self.get(attribute_name, strict=True)

    def __iter__(self):
        """
        Makes ObjectBody iterable over its attributes.
        Yields tuples of (attribute_name, attribute_value) for both schema-defined and unknown attributes.

        Example:
            ```
            body = ObjectBody(...)
            for attr_name, attr_value in body:
                print(f"{attr_name}: {attr_value}")
            ```

        Yields:
            Tuple[str, Any]: A tuple containing the attribute name and its value
        """
        for attr_name in self.attributes.keys():
            yield attr_name

    def __setitem__(self, key: str, value: Any):
        """
        Override the __setitem__ method to prevent modification of the ObjectBody
        """
        raise TypeError("ObjectBody is immutable")

    def items(self):
        """
        Provides a dict-like interface for getting all attributes.
        Similar to __iter__ but returns all items at once instead of yielding them.

        Returns:
            List[Tuple[str, Any]]: List of tuples containing attribute names and values
        """
        return [(key, self.attributes[key].value) for key in self.attributes.keys()]

    def keys(self):
        """
        Returns all attribute names in the ObjectBody.

        Returns:
            List[str]: List of attribute names
        """
        return list(self.attributes.keys()) + list(self.unknown_attributes.keys())

    def has_attribute(self, attribute_name: str) -> bool:
        """
        Check if the event body has an attribute

        Keyword Arguments:
            attribute_name: Name of the attribute

        Returns:
            Whether the event body has the attribute
        """

        return attribute_name in self.attributes or attribute_name in self.unknown_attributes

    def get(
        self,
        attribute_name: str,
        default_return: Any | None = None,
        secret_unmasking_fn: Callable[[str], str] | None = None,
        strict: bool | None = False,
    ) -> Any:
        """
        Get an attribute from the event body

        Keyword Arguments:
            attribute_name: Name of the attribute
            default_return: Default value to return if the attribute is not found or the value is None
            secret_unmasking_fn: Function to unmask secret values, only used if the attribute is a defined secret
            strict: Whether to raise an exception if the attribute is not found

        Returns:
            Attribute value
        """
        if not self.has_attribute(attribute_name):
            if strict:
                raise MissingAttributeError(attribute_name)

            else:
                return default_return

        attr_value = default_return

        if attribute_name in self.attributes:
            if self.attributes[attribute_name].value is not None:
                attr_value = self.attributes[attribute_name].value

                if self.attributes[attribute_name].schema_attribute.secret and secret_unmasking_fn:
                    attr_value = secret_unmasking_fn(attr_value)

        elif attribute_name in self.unknown_attributes:
            if self.unknown_attributes[attribute_name].value is not None:
                attr_value = self.unknown_attributes[attribute_name].value

        return attr_value

    def map_to(
        self,
        new_schema: type[ObjectBodySchema],
        additions: dict | None = None,
        attribute_map: dict | None = None,
    ) -> "ObjectBody":
        """
        Map the current event body to a new schema. Currently only support top-level attribute
        mapping. It will default to using an existing attribute name if the new attribute name
        is not found in the attribute map.

        Keyword Arguments:
            new_schema: Schema to map to
            additions: Additional attributes to add to the new object
            attribute_map: Attribute map to use, e.g. {'old_name': 'new_name'}

        Returns:
            Mapped object
        """
        logging.debug(f"Mapping self attributes to new schema: {new_schema.to_dict()}")

        attr_map = attribute_map or {}

        new_body = {}

        for attribute in new_schema.attributes:
            if attribute.name in attr_map.values():

                for old_name, new_name in attr_map.items():

                    if new_name == attribute.name:
                        new_body[new_name] = self.get(old_name)

            elif self.has_attribute(attribute.name):
                new_body[attribute.name] = self.get(attribute.name)

            elif additions and attribute.name in additions.keys():
                new_body[attribute.name] = additions[attribute.name]

        logging.debug(f"Mapped object to new schema: {new_body}")

        return ObjectBody(new_body, new_schema)

    def new(self, additions: dict | None = None, subtractions: list | None = None) -> "ObjectBody":
        """
        Create a new schemaless object with additional attributes, does not modify the current object
        and does not persist the schema. To persist the schema, use the map_to method.

        Keyword Arguments:
            additions: Additional attributes to add to the new object
        """
        new_body = {attribute.name: attribute.value for attribute in self.attributes.values()}

        if subtractions:
            for attribute in subtractions:
                if attribute in new_body:
                    del new_body[attribute]

        if additions:
            new_body.update(additions)

        return ObjectBody(new_body)

    def to_dict(self, ignore_unkown: bool | None = False) -> dict:
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
                **{
                    attribute.name: attribute.value
                    for attribute in self.unknown_attributes.values()
                },
            }

        flattened_dict = {}

        for key, value in raw_dict.items():
            if isinstance(value, ObjectBody):
                flattened_dict[key] = value.to_dict(ignore_unkown)

            elif isinstance(value, list):
                # Check if the list contains ObjectBody instances
                if all(isinstance(item, ObjectBody) for item in value):
                    flattened_dict[key] = [item.to_dict(ignore_unkown) for item in value]

                else:
                    flattened_dict[key] = value

            else:
                flattened_dict[key] = value

        return flattened_dict

    def values(self):
        """
        Returns all attribute values in the ObjectBody.

        Returns:
            List[Any]: List of attribute values
        """
        return [attr.value for attr in self.attributes.values()] + [
            attr.value for attr in self.unknown_attributes.values()
        ]
