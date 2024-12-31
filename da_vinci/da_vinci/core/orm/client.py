import logging

from enum import auto, StrEnum
from typing import Any, Dict, Generator, List, Optional, Union

import boto3

from botocore.exceptions import ClientError

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


class TableResultSortOrder(StrEnum):
    ASCENDING = auto()
    DESCENDING = auto()


class PaginatorCall:
    QUERY = 'query'
    SCAN = 'scan'


class PaginatedResults:
    def __init__(self, items: List[TableObject], last_evaluated_key: Optional[Dict] = None):
        self.items = items

        self.last_evaluated_key = last_evaluated_key

        self.has_more = last_evaluated_key is not None

    def __iter__(self):
        return iter(self.items)


class TableScanDefinition:
    _comparison_operators = {
        'contains': 'contains',
        'equal': '=',
        'greater_than': '>',
        'greater_than_or_equal': '>=',
        'less_than': '<',
        'less_than_or_equal': '<=',
        'not_equal': '!=',
    }

    def __init__(self, table_object_class: TableObject, attribute_prefix: Optional[str] = None):
        """
        Create a new scan definition for a DynamoDB table

        Keyword Arguments:
            table_object_class: Table object class to scan
            attribute_prefix: Prefix to use for attribute names (default: None)
        """
        self._attribute_filters = []
        self.attribute_prefix = attribute_prefix
        self.table_object_class = table_object_class

    def add(self, attribute_name: str, comparison: str, value: Any):
        """
        Add an attribute filter to the scan definition

        Keyword Arguments:
            attribute_name: Name of the attribute to filter on
            comparison: Comparison operator to use (ex: equal or greater_than)
            value: Value to compare against
        """
        if comparison not in self._comparison_operators:
            raise TableScanInvalidComparisonException(comparison)

        attr_name = attribute_name
        if self.attribute_prefix:
            attr_name = f'{self.attribute_prefix}_{attribute_name}'

        attribute_definition = self.table_object_class.attribute_definition(
            name=attr_name,
        )

        if not attribute_definition:
            raise TableScanInvalidAttributeException(attr_name)

        comparison = self._comparison_operators[comparison]

        self._attribute_filters.append(
            (attr_name, comparison, value)
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

        if not self._attribute_filters:
            return None, None

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

            expression_attributes[attr_key] = attr_dynamodb[attr.dynamodb_key_name]
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
        if attr in self._comparison_operators:
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

    def paginated(self, call: Union[str, PaginatorCall] = PaginatorCall.QUERY,
                  last_evaluated_key: Optional[Dict] = None, last_evaluated_object: Optional[TableObject] = None,
                  limit: Optional[int] = None, max_pages: Optional[int] = None, parameters: Optional[Dict] = None,
                  sort_order: Optional[TableResultSortOrder] = TableResultSortOrder.ASCENDING) -> Generator[PaginatedResults, None, None]:
        """
        Handle paginated DynamoDB table results. The last item in a page should be the last evaluated item.

        Keyword Arguments:
            call: Name of the DynamoDB client method to call, either a scan or query (default: query)
            last_evaluated_key: Last evaluated key from a previous page of results (default: None)
            last_evaluated_object: Last evaluated object from a previous page of results (default: None), only supported for query
            limit: Maximum number of items to retrieve per page (default: None)
            max_pages: Maximum number of pages to retrieve, if None it will return all available (default: None)
            parameters: Parameters to pass to the client method
            sort_order: Sort order to use for the results, only works for query calls (default: ASCENDING)
        """
        more_results = True

        params = parameters or {}

        if 'TableName' not in params:
            params['TableName'] = self.table_endpoint_name

        if 'Select' not in params:
            params['Select'] = 'ALL_ATTRIBUTES'

        if limit and 'Limit' not in params:
            params['Limit'] = limit

        mthd = getattr(self.client, call)

        if call == 'query' and sort_order:
            if not self.default_object_class.sort_key_attribute:
                raise Exception("Table object must have sort key to enable sorting")

            params['ScanIndexForward'] = sort_order == TableResultSortOrder.ASCENDING

        if last_evaluated_key:
            if call == 'scan':
                if not isinstance(last_evaluated_key, dict):
                    raise Exception("Last evaluated key must be a dictionary for scan operations")

                params['ExclusiveStartKey'] = last_evaluated_key

            else: # query
                params['ExclusiveStartKey'] = last_evaluated_key

        elif last_evaluated_object:
            key_gen_args = {
                'partition_key_value': last_evaluated_object.attribute_value(
                    last_evaluated_object.partition_key_attribute.name
                )
            }

            if self.default_object_class.sort_key_attribute:
                key_gen_args['sort_key_value'] = last_evaluated_object.attribute_value(
                    self.default_object_class.sort_key_attribute.name
                )

            params['ExclusiveStartKey'] = last_evaluated_object.gen_dynamodb_key(**key_gen_args)

        logging.debug(f"Created paginated parameters: {params}")

        # Page iteration counter
        retrieved_pages = 0

        # Iterate through each page of results, yielding the results as
        # a list of TableObjects
        while more_results:
            items = []

            response = mthd(**params)

            logging.debug(f"Paginated response: {response}")

            for item in response.get('Items', []):
                item_obj = self.default_object_class.from_dynamodb_item(item)

                items.append(item_obj)

            yield PaginatedResults(items=items, last_evaluated_key=response.get('LastEvaluatedKey'))

            more_results = 'LastEvaluatedKey' in response

            if more_results:
                logging.debug(f"More results found, continuing paginated query: {response['LastEvaluatedKey']}")

                params['ExclusiveStartKey'] = response['LastEvaluatedKey']

            retrieved_pages += 1

            # Break if max_pages is set and we've reached the requested limit
            if max_pages and retrieved_pages >= max_pages:
                break

    def _all_objects(self) -> List[TableObject]:
        """
        Loads all objects from a DynamoDB table into memory. Not recommended to use
        for large tables.
        """
        all = []

        for page in self.paginated():
            all.extend(page)

        return all

    def get_object(self, partition_key_value: Any, sort_key_value: Any = None,
                   consistent_read: Optional[bool] = False) -> Union[TableObject, None]:
        """
        Retrieve a single object from the table by partition and sort key

        Keyword Arguments:
            partition_key_value: Value of the partition key
            sort_key_value: Value of the sort key (default: None)
            consistent_read: Whether to use consistent read (default: False)
        """
        dynamodb_key = self.default_object_class.gen_dynamodb_key(
            partition_key_value=partition_key_value,
            sort_key_value=sort_key_value,
        )

        results = self.client.get_item(
            TableName=self.table_endpoint_name,
            Key=dynamodb_key,
            ConsistentRead=consistent_read,
        )

        logging.debug(f"Get object results: {results}")

        if 'Item' not in results:
            return None

        return self.default_object_class.from_dynamodb_item(results['Item'])

    def put_object(self, table_object: TableObject):
        """
        Save a single object to the table

        Keyword Arguments:
            table_object: Object to save
        """

        logging.debug(f"Saving object: {table_object.to_dynamodb_item()}")

        try:
            table_object.execute_on_update()

            self.client.put_item(
                TableName=self.table_endpoint_name,
                Item=table_object.to_dynamodb_item(),
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationException':
                error_message = e.response['Error']['Message']

                if "Supplied AttributeValue is empty" in error_message:
                    raise Exception(f"Empty attribute value detected, if using JSON type, attributes cannot be empty. Original Error: {error_message}")

                else:
                    raise

            else:
                # Re-raise the error if it's not a ValidationException
                raise

    def delete_object_by_key(self, partition_key_value: Any, sort_key_value: Any = None):
        """
        Delete a single object from the table by partition and sort key

        Keyword Arguments:
            partition_key_value: Value of the partition key
            sort_key_value: Value of the sort key (default: None)
        """
        key_args = {
            'partition_key_value': partition_key_value,
        }

        if sort_key_value:
            key_args['sort_key_value'] = sort_key_value

        self.client.delete_item(
            TableName=self.table_endpoint_name,
            Key=self.default_object_class.gen_dynamodb_key(**key_args),
        )

    def delete_object(self, table_object: TableObject):
        """
        Delete a single object from the table

        Keyword Arguments:
            table_object: Object to remove
        """
        partition_key = table_object.partition_key_attribute

        key_args = {
            'partition_key_value': table_object.attribute_value(partition_key.name),
        }

        if table_object.sort_key_attribute:
            key_args['sort_key_value'] = table_object.attribute_value(
                table_object.sort_key_attribute.name
            )

        self.client.delete_item(
            TableName=self.table_endpoint_name,
            Key=table_object.gen_dynamodb_key(**key_args),
        )

    def scanner(self, scan_definition: TableScanDefinition):
        """
        Perform a scan on the table, works similar to the paginator.

        Keyword Arguments:
            scan_definition: Scan definition to use (default: None)
        """
        filter_expression, attribute_values = scan_definition.to_expression()

        params = {
            'Select': 'ALL_ATTRIBUTES',
            'TableName': self.table_endpoint_name,
        }

        if filter_expression:
            params['ExpressionAttributeValues'] = attribute_values

            params['FilterExpression'] = filter_expression

        for page in self.paginated(call='scan', parameters=params):
            yield page

    def full_scan(self, scan_definition: TableScanDefinition) -> List[TableObject]:
        """
        Perform a full scan on the table, returns all items matching the scan definition at once.

        Keyword Arguments:
            scan_definition: Scan definition to use (default: None)
        """
        all = []

        for page in self.scanner(scan_definition=scan_definition):
            all.extend(page)

        return all

    def update_object(self, partition_key_value: Any, sort_key_value: Any,
                      updates: Dict[str, Any] = None, remove_keys: List[str] = None) -> None:
        """
        Updates an item in the DynamoDB table by applying SET and REMOVE operations.

        This method allows partial updates to items by setting new values for attributes or 
        removing existing ones. It supports dot notation for nested JSON map updates, enabling 
        the modification of specific keys within a JSON-like structure in DynamoDB.

        Arguments:
            partition_key_value (Any): The value of the partition key for the item to be updated.
            sort_key_value (Any): The value of the sort key for the item to be updated.
            updates (Dict[str, Any], optional): A dictionary containing attribute names (as keys) 
                and their new values (as values) to be updated in the table. If dot notation is 
                used in the attribute name (e.g., 'json_map.sub_key'), it will update a nested key 
                within a DynamoDB MAP type.
            remove_keys (List[str], optional): A list of attribute names to be removed from the item. 
                Dot notation can be used to remove nested attributes from a DynamoDB MAP.

        Example Usage:
            - To update a nested key inside a JSON map:
                updates = {'json_map.sub_key': 'new_value'}
                remove_keys = ['json_map.another_sub_key']

            - To update a top-level attribute and remove another:
                updates = {'attribute1': 'new_value'}
                remove_keys = ['attribute2']

        Notes:
            - This method generates DynamoDB UpdateExpressions to execute the SET and REMOVE 
            operations in a single request.
            - If both updates and remove_keys are provided, they are combined in the final 
            update expression.
            - Dot notation in updates or remove_keys will handle nested attributes within DynamoDB 
            MAP types.
            - This method assumes the object's table schema is already defined in the `default_object_class`.

        Raises:
            ClientError: If a client error occurs during the DynamoDB update operation.
            Exception: If an attribute with an empty value is provided for a DynamoDB JSON attribute.

        Returns:
            None
        """
        update_expressions = []

        expression_attribute_values = {}

        expression_attribute_names = {}

        # Handle updates (SET operations)
        if updates:
            for attribute_name, value in updates.items():
                # Check for dot notation (e.g. 'json_map.sub_key')
                if '.' in attribute_name:
                    parts = attribute_name.split('.')

                    dynamo_key = f"#{parts[0]}"

                    nested_key = '.'.join([f"#{part}" for part in parts[1:]])

                    dynamo_value = f":val_{attribute_name.replace('.', '_')}"

                    # Construct the SET expression for nested MAP
                    update_expressions.append(f"SET {dynamo_key}.{nested_key} = {dynamo_value}")

                    # Prepare the attribute value and name mappings
                    expression_attribute_values[dynamo_value] = value

                    expression_attribute_names.update({f"#{part}": part for part in parts})
                else:
                    # Regular attribute (non-nested)
                    dynamo_key = f"#{attribute_name}"

                    dynamo_value = f":val_{attribute_name}"

                    update_expressions.append(f"SET {dynamo_key} = {dynamo_value}")

                    expression_attribute_values[dynamo_value] = self.default_object_class.attribute_definition(attribute_name).dynamodb_value(value)

                    expression_attribute_names[dynamo_key] = attribute_name

        # Handle removals (REMOVE operations)
        if remove_keys:
            for attribute_name in remove_keys:
                if '.' in attribute_name:
                    # Dot notation for removing nested MAP attributes
                    parts = attribute_name.split('.')

                    dynamo_key = f"#{parts[0]}"

                    nested_key = '.'.join([f"#{part}" for part in parts[1:]])

                    update_expressions.append(f"REMOVE {dynamo_key}.{nested_key}")

                    expression_attribute_names.update({f"#{part}": part for part in parts})
                else:
                    # Regular attribute (non-nested)
                    dynamo_key = f"#{attribute_name}"

                    update_expressions.append(f"REMOVE {dynamo_key}")

                    expression_attribute_names[dynamo_key] = attribute_name

        # Combine all expressions into a single DynamoDB expression
        update_expression = " ".join(update_expressions)

        # Generate the DynamoDB key for the object
        dynamodb_key = self.default_object_class.gen_dynamodb_key(
            partition_key_value=partition_key_value,
            sort_key_value=sort_key_value,
        )

        # Execute the update in DynamoDB
        self.client.update_item(
            TableName=self.table_endpoint_name,
            Key=dynamodb_key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names
        )