import json

from collections.abc import Callable
from copy import deepcopy
from datetime import datetime, UTC as utc_tz
from enum import auto, StrEnum
from typing import Any, Dict, List, Optional, Union

from da_vinci.core.orm.exceptions import MissingTableObjectAttributeException


class TableObjectAttributeType(StrEnum):
    STRING = auto()
    NUMBER = auto()
    BOOLEAN = auto()
    DATETIME = auto()
    JSON = auto() # Not safe for storing empty attributes, native
    JSON_STRING = auto() # Safe for storing empty attributes
    STRING_LIST = auto()
    NUMBER_LIST = auto()
    JSON_LIST = auto() # Not safe for storing empty attributes, native
    JSON_STRING_LIST = auto() # Safe for storing empty attributes
    COMPOSITE_STRING = auto()
    STRING_SET = auto()
    NUMBER_SET = auto()

    @classmethod
    def is_list(cls, attribute_type: 'TableObjectAttributeType') -> bool:
        """
        Check if the attribute type is a list

        Keyword Arguments:
            attribute_type -- Attribute type to check

        Returns:
            bool
        """

        return attribute_type in (cls.STRING_LIST, cls.NUMBER_LIST, cls.JSON_LIST)

    def to_str(self) -> str:
        """
        Convert the attribute type to a string

        Returns:
            str
        """

        return self.name


class TableObjectAttribute:
    def __init__(self, name: str, attribute_type: TableObjectAttributeType,
                 argument_names: Optional[List[str]] = None, custom_exporter: Optional[Callable] = None,
                 custom_importer: Optional[Callable] = None, description: Optional[str] = None,
                 dynamodb_key_name: Optional[str] = None, default: Optional[Any] = None,
                 exclude_from_dict: Optional[bool] = False, exclude_from_schema_description: Optional[bool] = False,
                 is_indexed: bool = True, optional: bool = False):
        """
        Object representing an attribute of a TableObject

        Keyword Arguments:
            name -- Name of the attribute
            attribute_type -- Type of the attribute
            argument_names -- The names of Python arguments that are merged into a composite
                              string. This is required when the attribute type is COMPOSITE_STRING.
            custom_exporter -- Custom exporter function, called whenever data is converted for DynamoDB
            custom_importer -- Custom importer function, called whenever data is loaded from DynamoDB
            description -- Description of the attribute, annotation primarily
                           used for LLM context.
            dynamodb_key_name -- Name of the DynamoDB key, defaults to the ORM naming convention based
                                 on the attribute name
            default -- Default value for the attribute, attribute is considered optional when this is set.
                       Accepts a value or a callable that returns a value.
            exclude_from_dict -- Attribute is not added to a resulting Dict when calling to_dict()
            exclude_from_schema_description -- Attribute is not included in the table object schema description
            is_indexed -- Whether the attribute is able to be used to query with, defaults to True
            optional -- Whether the attribute optional, defaults to False unless a default is provided
        """
        self.name = name

        self.description = description

        self.attribute_type = attribute_type

        self.exclude_from_dict = exclude_from_dict

        self.exclude_from_schema_description = exclude_from_schema_description

        self.is_indexed = is_indexed

        if self.attribute_type is TableObjectAttributeType.JSON_STRING or \
                self.attribute_type is TableObjectAttributeType.JSON_STRING_LIST:
            self.is_indexed = False

        if dynamodb_key_name:
            self.dynamodb_key_name = dynamodb_key_name

        else:
            self.dynamodb_key_name = self.default_dynamodb_key_name(self.name)

        self.argument_names = argument_names

        if self.attribute_type == TableObjectAttributeType.COMPOSITE_STRING and not self.argument_names:
            raise ValueError('argument_names must be provided when attribute_type is COMPOSITE_STRING')

        self._default = default

        if self._default is None:
            self.optional = optional

        else:
            self.optional = True

        self.custom_exporter = custom_exporter

        self.custom_importer = custom_importer

    @staticmethod
    def composite_string_value(values: List[str]):
        """
        Return a full composite string value given a list of attribute values

        Keyword Arguments:
            values -- List of values to join into the full composite string value
        """

        return '-'.join(values)

    @staticmethod
    def default_dynamodb_key_name(name: str) -> str:
        """
        Convert a name to a DynamoDB key name

        Keyword Arguments:
            name -- Name to convert

        Returns:
            str
        """

        return ''.join([wrd.capitalize() for wrd in name.split('_')])

    @staticmethod
    def timestamp_to_datetime(timestamp: Union[int, float]) -> datetime:
        """
        Convert a timestamp string to a datetime

        Keyword Arguments:
            timestamp -- Timestamp string

        Returns:
            datetime
        """

        return datetime.fromtimestamp(timestamp)

    @staticmethod
    def datetime_to_timestamp(dt: datetime) -> float:
        """
        Convert a datetime to a timestamp

        Keyword Arguments:
            dt -- Datetime

        Returns:
            float
        """

        return dt.timestamp()

    def schema_to_str(self) -> str:
        """
        Describe the schema for the attribute

        Returns:
            str
        """

        descr = f'{self.name} - type: {self.attribute_type.to_str()}'

        if self.description:
            descr += f' description: {self.description}'

        return descr

    @property
    def default(self) -> Any:
        if callable(self._default):
            return self._default()
        
        return self._default

    @property
    def dynamodb_type_label(self) -> str:
        """
        Get the DynamoDB type label for the attribute type

        Returns:
            str
        """
        dynamodb_type_label = 'S'

        # Handle number and datetime types
        if self.attribute_type is TableObjectAttributeType.NUMBER \
                or self.attribute_type is TableObjectAttributeType.DATETIME:
            dynamodb_type_label = 'N'

        # Handle JSON types
        elif self.attribute_type is TableObjectAttributeType.JSON:
            dynamodb_type_label = 'M'

        # Handle boolean types
        elif self.attribute_type is TableObjectAttributeType.BOOLEAN:
            dynamodb_type_label = 'BOOL'

        # Handle list types
        elif TableObjectAttributeType.is_list(self.attribute_type):
            dynamodb_type_label = 'L'

        # Handle set types
        elif self.attribute_type in (TableObjectAttributeType.STRING_SET, TableObjectAttributeType.NUMBER_SET):
            dynamodb_type_label = 'SS' if self.attribute_type == TableObjectAttributeType.STRING_SET else 'NS'

        return dynamodb_type_label

    def _infer_dynamodb_value(self, value: Any) -> Dict:
        """
        Helper method to infer DynamoDB value type for nested structures.

        Keyword Arguments:
            value -- Value to infer
        """
        if isinstance(value, str):
            return {"S": value}

        elif isinstance(value, bool):
            return {"BOOL": value}

        elif isinstance(value, (int, float)):
            return {"N": str(value)}

        elif isinstance(value, dict):
            if 'M' in value:
                return value

            return {"M": {k: self._infer_dynamodb_value(v) for k, v in value.items()}}

        elif isinstance(value, list):
            return {"L": [self._infer_dynamodb_value(v) for v in value]}

        elif value is None:
            return {"NULL": True}

        else:
            raise ValueError(f"Unsupported value type: {type(value)}")

    def dynamodb_value(self, value: Any) -> Any:
        """
        Convert a value to a DynamoDB supported value

        Keyword Arguments:
            value -- Value to convert

        Returns:
            Any
        """
        if self.custom_exporter:
            return self.custom_exporter(value)

        # Handle number types
        if self.attribute_type is TableObjectAttributeType.NUMBER:
            return str(value)

        # Handle datetime types
        elif self.attribute_type is TableObjectAttributeType.DATETIME:
            if not value:
                return str(0)
            return str(float(self.datetime_to_timestamp(value)))

        # Handle JSON types
        elif self.attribute_type is TableObjectAttributeType.JSON:
            if isinstance(value, str):
                value = json.loads(value)

            elif not value:
                return None

            return  {k: self._infer_dynamodb_value(v) for k, v in value.items()}

        elif self.attribute_type is TableObjectAttributeType.JSON_STRING or \
                self.attribute_type is TableObjectAttributeType.JSON_STRING_LIST:
            if not value:
                if self.attribute_type is TableObjectAttributeType.JSON_STRING_LIST:
                    return "[]"

                else:
                    return "{}"

            return json.dumps(value)

        # Handle composite string types
        elif self.attribute_type is TableObjectAttributeType.COMPOSITE_STRING:
            if isinstance(value, str):
                return value

            arg_values = []

            for arg in self.argument_names:
                arg_values.append(getattr(self, arg))

            return TableObjectAttribute.composite_string_value(arg_values)

        # Handle list types
        elif TableObjectAttributeType.is_list(self.attribute_type):
            # Specifically handle JSON_LIST
            if self.attribute_type is TableObjectAttributeType.JSON_LIST:
                if not value:
                    return None

                # Ensure each element in the list is converted properly
                return [{"M": json.loads(item) if isinstance(item, str) else item} for item in value]

            if not value:
                return []

            if self.attribute_type is TableObjectAttributeType.NUMBER_LIST:
                label = 'N'

            else:
                label = 'S'

            return [{label: str(val)} for val in value]

        # Handle string set types
        elif self.attribute_type == TableObjectAttributeType.STRING_SET:
            if not value:
                return None

            return list(value)  # DynamoDB stores sets as lists in JSON format

        # Handle number set types
        elif self.attribute_type == TableObjectAttributeType.NUMBER_SET:
            if not value:
                return None

            return [str(val) for val in value]

        # Handle boolean types
        elif not isinstance(value, bool) and not value:
            return str(value)

        return value

    def as_dynamodb_attribute(self, value: Any) -> Dict:
        """
        Return the attribute as a DynamoDB attribute

        Keyword Arguments:
            value -- Value to convert
        """
        # Skip None values or empty sets/dictionaries for JSON and Set types
        if (self.attribute_type in (TableObjectAttributeType.STRING_SET, TableObjectAttributeType.NUMBER_SET)
                and (value is None or not value)):
            return None  # Skip empty sets

        if self.attribute_type in (TableObjectAttributeType.JSON, TableObjectAttributeType.JSON_LIST) and \
                (value is None or (isinstance(value, dict) and not value)):
            return None  # Skip empty JSON or JSON_LIST

        return {
            self.dynamodb_key_name: {
                self.dynamodb_type_label: self.dynamodb_value(value),
            }
        }

    def _infer_python_value(self, value: Dict) -> Any:
        """
        Helper method to convert DynamoDB types back to Python values.

        Keyword Arguments:
            value -- Value to convert
        """
        if 'S' in value:
            return value['S']

        elif 'N' in value:
            return float(value['N']) if '.' in value['N'] else int(value['N'])

        elif 'BOOL' in value:
            return value['BOOL']

        elif 'M' in value:
            return {k: self._infer_python_value(v) for k, v in value['M'].items()}

        elif 'L' in value:
            return [self._infer_python_value(v) for v in value['L']]

        elif 'NULL' in value:
            return None

        elif 'SS' in value:
            return set(value['SS'])

        elif 'NS' in value:
            return set(map(int, value['NS']))

        else:
            raise ValueError(f"Unsupported DynamoDB value type: {value}")

    def true_value(self, value: Any) -> Any:
        """
        Return the attribute value as a Python value
        """
        value = value[self.dynamodb_type_label]

        if isinstance(value, str) and value == 'None':
            return None

        if self.attribute_type is TableObjectAttributeType.NUMBER:
            if '.' in value:
                return float(value)

            return int(value)

        elif self.attribute_type is TableObjectAttributeType.DATETIME:
            if float(value) == 0.0:
                return None

            return self.timestamp_to_datetime(float(value))

        # Handle JSON_LIST
        elif self.attribute_type is TableObjectAttributeType.JSON_LIST:
            # Convert each item in the list from DynamoDB format to a Python dictionary
            return [self._infer_python_value(item) for item in value]

        # Handle other list types
        elif TableObjectAttributeType.is_list(self.attribute_type):
            if self.attribute_type is TableObjectAttributeType.NUMBER_LIST:
                label = 'N'  
            else:
                label = 'S'

            return [item[label] for item in value]

        elif self.attribute_type == TableObjectAttributeType.STRING_SET:
            return set(value)  # Convert list back to set

        elif self.attribute_type == TableObjectAttributeType.NUMBER_SET:
            return set(value)

        elif self.attribute_type is TableObjectAttributeType.COMPOSITE_STRING:
            return tuple(value.split('-'))

        elif self.attribute_type is TableObjectAttributeType.JSON:
            # If the value is already a dict (DynamoDB MAP), return it as is
            if isinstance(value, dict):
                return {k: self._infer_python_value(v) for k, v in value.items()}

        elif self.attribute_type is TableObjectAttributeType.JSON_STRING or \
                self.attribute_type is TableObjectAttributeType.JSON_STRING_LIST:
            if not value:
                if self.attribute_type is TableObjectAttributeType.JSON_STRING_LIST:
                    return []

                else:
                    return {}

            return json.loads(value)

        return value

    def set_attribute(self, obj: Any, value: Any):
        """
        Set the attribute on an object

        Keyword Arguments:
            obj -- Object to set the attribute on
            value -- Value to set
        """

        setattr(obj, self.name, value)

    def from_dynamodb_attribute(self, value: Any) -> Any:
        """
        Return the attribute value as a Python value, run a
        custom importer if one was set
        """
        true_val = self.true_value(value)

        if self.custom_importer:
            return self.custom_importer(true_val)

        return true_val


class TableObject:
    """
    Base class for Table object definitions

    Class Attributes:
        attribute_lookup_prefix: Attribute lookup prefix, prefixes the attribute name when retrieving attributes
        attributes: List of attributes
        description: Description of the table
        execute_on_update: Function to execute when the object is updated
        object_name: Name of the object, defaults to the class name. This should be set when
                     dynamically defining table objects.
        partition_key_attribute: Partition key attribute
        sort_key_attribute: Sort key attribute
        table_name: Name of the table
        ttl_attribute: Optional TTL attribute

    Example:
        ```
        from uuid import uuid4

        from da_vinci.core.orm.table_object import (
            TableObject,
            TableObjectAttribute,
            TableObjectAttributeType,
        )

        class MyTableObject(TableObject):
            partition_key_attribute = TableObjectAttribute(
                name='my_pk',
                attribute_type=TableObjectAttributeType.STRING,
            )

            sort_key_attribute = TableObjectAttribute(
                name='my_sk',
                attribute_type=TableObjectAttributeType.STRING,
                default=lambda: str(uuid4()),
            )

            table_name = 'my_table'

            attributes = [
                TableObjectAttribute(
                    name='created_on',
                    attribute_type=TableObjectAttributeType.DATETIME,
                    default=lambda: datetime.now(),
                ),
            ]
        ```
    """
    partition_key_attribute: TableObjectAttribute
    table_name: str

    attribute_lookup_prefix: Optional[str] = None
    attributes: List[TableObjectAttribute] = []
    description: Optional[str] = None
    object_name: str = None
    sort_key_attribute: Optional[TableObjectAttribute] = None
    ttl_attribute: Optional[TableObjectAttribute] = None

    def __init__(self, **kwargs):
        """
        Base class for Table objects
        """
        self.__attr_index__ = {}

        for attr in self.all_attributes():
            self.__attr_index__[attr.name] = attr

            if attr.attribute_type is TableObjectAttributeType.COMPOSITE_STRING \
                    and set(kwargs.keys()).issuperset(set(attr.argument_names)):
                composite_args = []

                for arg in attr.argument_names:
                    if arg in kwargs:
                        attr.set_attribute(self, kwargs[arg])
                    else:
                        raise MissingTableObjectAttributeException(arg)

                    composite_args.append(kwargs[arg])

            elif attr.name in kwargs:
                # If the value is None and the attribute has a default, use the default
                if not kwargs[attr.name] and attr.default:
                    attr.set_attribute(self, attr.default)

                else:
                    attr.set_attribute(self, kwargs[attr.name])

            else:
                # If the attribute is optional set default, default will either be a value,
                # a callable, or None which is fine for optional attributes
                if attr.optional:
                    attr.set_attribute(self, attr.default)

                else:
                    raise MissingTableObjectAttributeException(attr.name)

    @classmethod
    def define(cls, partition_key_attribute: TableObjectAttribute, object_name: str, table_name: str,
               attribute_lookup_prefix: Optional[str] = None, attributes: Optional[List[TableObjectAttribute]] = None,
               description: Optional[str] = None, sort_key_attribute: Optional[TableObjectAttribute] = None,
               ttl_attribute: Optional[TableObjectAttribute] = None) -> 'TableObject':
        """
        Define a TableObject

        Keyword Arguments:
            attribute_lookup_prefix: Attribute lookup prefix
            attributes: List of attributes
            description: Description of the table
            partition_key_attribute: Partition key attribute
            object_name: Name of the object
            sort_key_attribute: Sort key attribute
            table_name: Name of the table
            ttl_attribute: Optional TTL attribute
        """
        obj_klass = type(object_name, (cls,), {})

        obj_klass.partition_key_attribute = partition_key_attribute
        obj_klass.object_name = object_name
        obj_klass.table_name = table_name

        obj_klass.attribute_lookup_prefix = attribute_lookup_prefix
        obj_klass.sort_key_attribute = sort_key_attribute
        obj_klass.attributes = attributes or []
        obj_klass.description = description
        obj_klass.ttl_attribute = ttl_attribute

        return obj_klass

    def __getattr__(self, name: str) -> Any:
        """
        Get an attribute by name

        Keyword Arguments:
            name -- Name of the attribute

        Returns:
            Any
        """
        attr_keys = [attr.name for attr in self.all_attributes()]

        if self.attribute_lookup_prefix:
            prefixed_name = f'{self.attribute_lookup_prefix}_{name}'

            if prefixed_name in attr_keys:
                return getattr(self, prefixed_name, None)

        return super().__getattribute__(name)

    def attribute_value(self, name: str) -> Any:
        """
        Get the value of an attribute

        Keyword Arguments:
            name -- Name of the attribute

        Returns:
            Any
        """
        return getattr(self, name)

    def execute_on_update(self):
        """
        Execute the on update function

        Override this method to provide custom behavior when the object is saved to DynamoDB
        """
        pass

    def update(self, **kwargs):
        """
        Update the attributes of the object and provide a list of attribute names
        that were updated.

        Keyword Arguments:
            kwargs -- Attributes to update
        """
        changed_attrs = []

        for attr in self.all_attributes():
            if attr.name in kwargs:
                curr_val = getattr(self, attr.name)

                new_val = kwargs[attr.name]

                if curr_val != new_val:
                    attr.set_attribute(self, new_val)

                    changed_attrs.append(attr.name)

        return changed_attrs

    def to_dict(self, exclude_attribute_names: Optional[List[str]] = None, json_compatible: Optional[bool] = False) -> Dict:
        """
        Convert the object to a dict representation

        Keyword Arguments:
        exclude_attribute_names -- List of attribute names to exclude from the resulting dict
        json_compatible -- Convert datetime objects to strings and sets to lists for JSON compatibility
        """
        res = {}

        if exclude_attribute_names is None:
            exclude_attribute_names = []

        for attr in self.all_attributes():
            if attr.exclude_from_dict or attr.name in exclude_attribute_names:
                continue

            val = getattr(self, attr.name)

            if attr.attribute_type is TableObjectAttributeType.DATETIME and json_compatible \
                and val is not None:
                val = val.isoformat()

            if json_compatible and attr.attribute_type is TableObjectAttributeType.STRING_SET or \
                    attr.attribute_type is TableObjectAttributeType.NUMBER_SET:

                if val is not None:
                    val = list(val)

            if attr.custom_exporter:
                val = attr.custom_exporter(val)

            res[attr.name] = val

        return res
    
    def to_dynamodb_item(self) -> Dict:
        """
        Convert the object to a DynamoDB item

        Returns:
            Dict
        """
        item = {}

        for attr in self.all_attributes():
            val = getattr(self, attr.name)

            dyn_attr = attr.as_dynamodb_attribute(val)

            if dyn_attr:
                item.update(dyn_attr)

        return item

    def to_json(self) -> str:
        """
        Convert the object to a JSON string

        Returns:
            str
        """

        return json.dumps(self.to_dict(json_compatible=True))

    @classmethod
    def all_attributes(cls) -> List[TableObjectAttribute]:
        """
        Class method that returns all defined attributes on the class
        """
        attributes = deepcopy(cls.attributes)

        attributes.append(cls.partition_key_attribute)

        if cls.sort_key_attribute:
            attributes.append(cls.sort_key_attribute)

        if cls.ttl_attribute:
            attributes.append(cls.ttl_attribute)

        return attributes

    @classmethod
    def attribute_definition(cls, name: str) -> TableObjectAttribute:
        """
        Get an attribute definition by name

        Keyword Arguments:
            name -- Name of the attribute

        Returns:
            TableObjectAttribute
        """

        for attr in cls.all_attributes():
            if attr.name == name:
                return attr

        return None

    @classmethod
    def from_dynamodb_item(cls, item: Dict) -> 'TableObject':
        """
        Create a TableObject from a DynamoDB item

        Keyword Arguments:
            item -- Item to convert

        Returns:
            TableObject
        """
        updated_item = {}

        for attr in cls.all_attributes():
            if attr.dynamodb_key_name in item:

                if attr.attribute_type is TableObjectAttributeType.COMPOSITE_STRING:
                    val = item[attr.dynamodb_key_name]

                    for idx, arg in enumerate(attr.argument_names):
                        updated_item[arg] = val[idx]
                else:
                    val = item[attr.dynamodb_key_name]

                    updated_item[attr.name] = attr.from_dynamodb_attribute(val)

        return cls(**updated_item)

    @classmethod
    def gen_dynamodb_key(cls, partition_key_value: str,
                         sort_key_value: Optional[str] = None) -> Dict:
        """
        Generate a DynamoDB key

        Keyword Arguments:
            partition_key_value -- Partition key value
            sort_key_value -- Sort key value

        Returns:
            Dict
        """
        key = cls.partition_key_attribute.as_dynamodb_attribute(
            partition_key_value
        )

        if cls.sort_key_attribute:
            if not sort_key_value:
                raise ValueError('Sort key attribute is required, no value provided')

            key.update(
                cls.sort_key_attribute.as_dynamodb_attribute(
                    sort_key_value
                )
            )

        return key

    @classmethod
    def schema_description(cls) -> str:
        """
        Get the schema for the object in a human readable format

        Returns:
            str
        """
        full_descr = cls.object_name or cls.__name__

        if cls.description:
            full_descr += f' - {cls.description}'

        for attr in cls.all_attributes():
            if attr.exclude_from_schema_description:
                continue

            full_descr += f'\n  - {attr.schema_to_str()}'

        return full_descr

    @classmethod
    def schema_to_str(cls, only_indexed_attributes: bool = True) -> str:
        """
        Describe the full schema for the object

        Keyword Arguments:
            only_indexed_attributes -- Only describe indexed attributes

        Returns:
            str
        """
        schema_str_list = [
            cls.full_description(),
        ]

        for attr in cls.all_attributes():
            schema_str_list.append(attr.schema_to_str())

        return '\n'.join(schema_str_list)

    @staticmethod
    def update_date_attributes(date_attribute_names: List[str], obj: 'TableObject',
                               to_datetime: Optional[datetime] = None):
        """
        Update the record_last_updated attribute on the object. Helper method that is
        commonly used to construct execute_on_update functions.

        Keyword Arguments:
            date_attribute_names -- Names of the date attributes
            obj -- Object to update
            to_datetime -- Datetime to set, defaults to datetime.now()
        """

        if not to_datetime:
            to_datetime = datetime.now(tz=utc_tz)

        for attr_name in date_attribute_names:
            setattr(obj, attr_name, to_datetime)
