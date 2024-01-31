import logging

from typing import Any, Dict, List, Optional, Union

import boto3

from da_vinci.core.exceptions import ResourceNotFoundError
from da_vinci.core.resource_discovery import resource_endpoint_lookup
from da_vinci.core.orm.exceptions import (
    TableScanInvalidAttributeException,
    TableScanInvalidComparisonException,
)
from da_vinci.core.orm.table_object import (
    TableObject,
    TableObjectAttributeType,
)


LOG = logging.getLogger(__name__)


class TableScanDefinition:
    __comparison_operators = {
        'contains': 'contains',
        'equal': '=',
        'greater_than': '>',
        'greater_than_or_equal': '>=',
        'less_than': '<',
        'less_than_or_equal': '<=',
        'not_equal': '!=',
    }

    def __init__(self, table_object_class: TableObject):
        self._attribute_filters = []
        self.table_object_class = table_object_class

    def add(self, attribute_name: str, comparison: str, value: Any):
        """
        Add an attribute filter to the scan definition

        Keyword Arguments:
            attribute_name: Name of the attribute to filter on
            comparison: Comparison operator to use (ex: equal or greater_than)
            value: Value to compare against
        """
        if comparison not in self.__comparison_operators:
            raise TableScanInvalidComparisonException(comparison)

        attribute_definition = self.table_object_class.attribute_definition(
            attribute_name=attribute_name,
        )

        if not attribute_definition:
            raise TableScanInvalidAttributeException(attribute_name)

        comparison = self.comparison_map[comparison]

        self._attribute_filters.append(
            (attribute_name, comparison, value)
        )

    def to_expression(self) -> str:
        """
        Convert the scan definition to a DynamoDB expression

        Returns:
            DynamoDB expression
        """
        attr_keys = 'abcdefghijklmnopqrstuvwxyz'

        # Caching loaded attributes to avoid multiple calls to reduce the
        # excess looping that would occur with constant attribute_definition lookups
        loaded_attrs = {}

        expression = []
        expression_attributes = {}

        for idx, fltr in enumerate(self._attribute_filters):
            name, comparison, value = fltr

            if name in loaded_attrs:
                attr = loaded_attrs[name]
            else:
                attr = self.table_object_class.attribute_definition(name)

                if not attr:
                    raise TableScanInvalidAttributeException(name)

                loaded_attrs[name] = attr

            attr_key = ':' + attr_keys[idx]

            expr_part = ''
            if comparison == 'contains':
                expr_part = f'contains({attr.dynamodb_key_name}, {attr_key})'

            else:
                expr_part = f'{attr.dynamodb_key_name} {comparison} {attr_key}'

            if comparison == 'contains' and attr.attribute_type == TableObjectAttributeType.STRING_LIST:
                attr_dynamodb = {attr.dynamodb_key_name: {'S': value}}

            # Ignore custom loaders for JSON types since it is just a string and
            # a string comparison is all that is needed
            elif attr.attribute_type == TableObjectAttributeType.JSON \
                    and isinstance(value, str):
                attr_dynamodb = {attr.dynamodb_key_name: {'S': value}}

            else:
                attr_dynamodb = attr.as_dynamodb_attribute(value)

            expression_attributes[attr_key] = attr_dynamodb
            expression.append(expr_part)

        return ' AND '.join(expression), expression_attributes

    def to_instructions(self) -> List[str]:
        """
        Convert the scan definition to a list of basic scan instructions

        Returns:
            List of DynamoDB scan instructions
        """
        instructions = []

        for fltr in self._attribute_filters:
            name, comparison, value = fltr

            instructions.append(
                f'{name} {comparison} {value}'
            )

        return instructions

    def __getattr__(self, attr: str):
        """
        Override to dynamically add attribute filters to the scan definition
        using comparison names as method names.

        Example: scan_definition.equal('foo', 'bar') will add a filter for
        the attribute foo equal to bar

        Keyword Arguments:
            attr: Name of the attribute to filter on
        """
        if attr in self.__comparison_operators:
            def add_filter(attribute_name: str, value: Any):
                self.add(
                    attribute_name=attribute_name,
                    comparison=attr,
                    value=value,
                )

            return add_filter

        raise AttributeError(attr)


class TableClient:
    def __init__(self, default_object_class: TableObject, app_name: Optional[str] = None,
                 deployment_id: Optional[str] = None, table_endpoint_name: Optional[str] = None):
        self.default_object_class = default_object_class
        self.table_name = self.default_object_class.table_name

        self.table_endpoint_name = table_endpoint_name

        if not self.table_endpoint_name:
            self.table_endpoint_name = resource_endpoint_lookup(
                resource_type='table',
                resource_name=self.table_name,
                app_name=app_name,
                deployment_id=deployment_id,
            )

        self.client = boto3.client('dynamodb')

    @classmethod
    def table_resource_exists(cls, table_object_class: TableObject, app_name: Optional[str] = None,
                              deployment_id: Optional[str] = None) -> bool:
        """
        Check if a DaVinci based DynamoDB table exists

        Arguments:
            app_name: Name of the application
            deployment_id: Unique identifier for the installation
            table_object_class: The object class of the table to check
        """
        try:
            resource_endpoint_lookup(
                resource_type='table',
                resource_name=table_object_class.table_name,
                app_name=app_name,
                deployment_id=deployment_id,
            )
            
        except ResourceNotFoundError:
            return False

    def paginated(self, call: str = 'scan', parameters: Optional[Dict] = None) -> List[TableObject]:
        """
        Handle paginated DynamoDB table results

        Keyword Arguments:
            call: Name of the DynamoDB client method to call, either a scan or query (default: scan)
            parameters: Parameters to pass to the client method
        """
        more_results = True
        params = parameters or {}

        if 'TableName' not in params:
            params['TableName'] = self.table_endpoint_name

        if 'Select' not in params:
            params['Select'] = 'ALL_ATTRIBUTES'

        mthd = getattr(self.client, call)

        # Iterate through each page of results, yielding the results as
        # a list of TableObjects
        while more_results:
            items = []
            response = mthd(**params)

            for item in response.get('Items', []):
                items.append(self.default_object_class.from_dynamodb(item))

            yield items

            more_results = 'LastEvaluatedKey' in response

            if more_results:
                params['ExclusiveStartKey'] = response['LastEvaluatedKey']

    def __all_objects(self) -> List[TableObject]:
        """
        Loads all objects from a DynamoDB table into memory. Not recommended to use
        for large tables.
        """
        all = []

        for page in self.paginated():
            all.extend(page)

        return all

    def get_object(self, partition_key_value: Any, sort_key_value: Any = None) -> Union[TableObject, None]:
        """
        Retrieve a single object from the table by partition and sort key

        Keyword Arguments:
            partition_key_value: Value of the partition key
            sort_key_value: Value of the sort key (default: None)
        """
        dynamodb_key = self.default_object_class.gen_dynamodb_key(
            partition_key_value=partition_key_value,
            sort_key_value=sort_key_value,
        )

        results = self.client.get_item(
            TableName=self.table_endpoint_name,
            Key=dynamodb_key,
        )

        if 'Item' not in results:
            return None

        return self.default_object_class.from_dynamodb(results['Item'])

    def put_object(self, table_object: TableObject):
        """
        Save a single object to the table

        Keyword Arguments:
            table_object: Object to save
        """

        if table_object.execute_on_update:
            if not callable(table_object.execute_on_update):
                raise ValueError('execute_on_update must be a function')

            table_object.execute_on_update(table_object)

        self.client.put_item(
            TableName=self.table_endpoint_name,
            Item=table_object.to_dynamodb_item(),
        )

    def remove_object(self, table_object: TableObject):
        """
        Remove a single object from the table

        Keyword Arguments:
            table_object: Object to remove
        """
        self.client.delete_item(
            TableName=self.table_endpoint_name,
            Key=table_object.gen_dynamodb_key(),
        )

    def scanner(self, scan_definition: TableScanDefinition) -> List[TableObject]:
        """
        Perform a scan on the table, works similar to the paginator.

        Keyword Arguments:
            scan_definition: Scan definition to use (default: None)
            kwargs: Additional arguments to pass to the scan
        """
        filter_expression, attribute_values = scan_definition.to_expression()

        params = {
            'ExpressionAttributeValues': attribute_values,
            'FilterExpression': filter_expression,
            'Select': 'ALL_ATTRIBUTES',
            'TableName': self.table_endpoint_name,
        }

        for page in self.paginated(call='scan', parameters=params):
            yield page

    def full_scan(self, scan_definition: TableScanDefinition) -> List[TableObject]:
        """
        Perform a full scan on the table, works similar to the paginator.

        Keyword Arguments:
            scan_definition: Scan definition to use (default: None)
        """
        all = []

        for page in self.scanner(scan_definition=scan_definition):
            all.extend(page)

        return all