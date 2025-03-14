from typing import Any, Dict, List, Optional

from aws_cdk import (
    aws_dynamodb as cdk_dynamodb,
    aws_iam as cdk_iam,
    RemovalPolicy,
)

from aws_cdk.custom_resources import (
    AwsCustomResource,
    AwsCustomResourcePolicy,
    AwsSdkCall,
    PhysicalResourceId,
)

from constructs import Construct

from da_vinci.core.resource_discovery import ResourceType
from da_vinci.core.orm.table_object import TableObject, TableObjectAttributeType

from da_vinci_cdk.constructs.access_management import ResourceAccessPolicy
from da_vinci_cdk.constructs.base import custom_type_name, resource_namer
from da_vinci_cdk.constructs.resource_discovery import DiscoverableResource, ResourceDiscoveryStorageSolution


class DynamoDBTable(Construct):
    def __init__(self,  partition_key: cdk_dynamodb.Attribute, scope: Construct,
                 table_name: str, construct_id: Optional[str] = None,
                 exclude_from_discovery: bool = False, removal_policy: Optional[RemovalPolicy] = None,
                 sort_key: Optional[cdk_dynamodb.Attribute] = None,
                 tags: List[Dict[str, Any]] = None,
                 time_to_live_attribute: Optional[str] = None,
                 **kwargs):
        """
        Initialize a DynamoDBTable object

        DynamoDBTable is a wrapper around a DynamoDB table that provisions
        a table utilizing the core service discovery pattern.

        Keyword Arguments:
            construct_id: Identifier for the construct
            exclude_from_discovery: Whether to exclude the table from discovery
            partition_key: Partition key for the DynamoDB table
            removal_policy: Removal policy for the DynamoDB table
            scope: Parent construct for the DynamoDBTable
            sort_key: Sort key for the DynamoDB table
            table_name: Name of the DynamoDB table
            time_to_live_attribute: Attribute to use for TTL
            kwargs: Additional arguments to pass to the DynamoDB table

        Example:
            ```
            from aws_cdk import aws_dynamodb as cdk_dynamodb
            from aws_cdk import RemovalPolicy

            from constructs import Construct

            from da_vinci_cdk.constructs.dynamodb import DynamoDBTable

            table = DynamoDBTable(
                scope=scope,
                partition_key=cdk_dynamodb.Attribute(
                    name='table_object_id',
                    type=cdk_dynamodb.AttributeType.STRING,
                ),
                removal_policy=RmoevalPolicy.DESTROY,
                sort_key=cdk_dynamodb.Attribute(
                    name='table_object_attribute',
                    type=cdk_dynamodb.AttributeType.STRING,
                ),
                table_name=table_name,
            )
        """

        construct_id = construct_id or f'dynamodb-table-{table_name}'

        super().__init__(scope, construct_id)

        additional_tags = {
            'DaVinciFramework::ApplicationName': scope.node.get_context('app_name'),
            'DaVinciFramework::DeploymentId': scope.node.get_context('deployment_id'),
            'DaVinciFrameworkManaged': 'True',
        }

        if not tags:
            tags = []

        for additional_tag in additional_tags:
            tags.append({
                'key': additional_tag,
                'value': additional_tags[additional_tag]
            })

        self.table = cdk_dynamodb.TableV2(
            scope=self,
            id=f'{construct_id}-table',
            billing=cdk_dynamodb.Billing.on_demand(),
            partition_key=partition_key,
            removal_policy=removal_policy,
            sort_key=sort_key,
            table_name=resource_namer(name=table_name, scope=scope),
            tags=tags,
            time_to_live_attribute=time_to_live_attribute,
            **kwargs,
        )

        if not exclude_from_discovery:
            self._discovery_resource = DiscoverableResource(
                construct_id=f'{construct_id}-resource',
                scope=self,
                resource_endpoint=self.table.table_name,
                resource_name=table_name,
                resource_type=ResourceType.TABLE,
            )

        self.read_access_statement = cdk_iam.PolicyStatement(
            actions=['dynamodb:BatchGetItem',
                     'dynamodb:DescribeTable',
                     'dynamodb:GetRecords',
                     'dynamodb:ConditionCheckItem',
                     'dynamodb:GetItem',
                     'dynamodb:Query',
                     'dynamodb:GetShardIterator',
                     'dynamodb:Scan'],
            resources=[
                self.table.table_arn,
                f'{self.table.table_arn}/*',
            ],
        )

        self.read_write_access_statement = cdk_iam.PolicyStatement(
            actions=['dynamodb:BatchGetItem',
                     'dynamodb:BatchWriteItem',
                     'dynamodb:DescribeTable',
                     'dynamodb:GetRecords',
                     'dynamodb:ConditionCheckItem',
                     'dynamodb:GetItem',
                     'dynamodb:DeleteItem',
                     'dynamodb:UpdateItem',
                     'dynamodb:PutItem',
                     'dynamodb:Query',
                     'dynamodb:GetShardIterator',
                     'dynamodb:Scan'],
            resources=[
                self.table.table_arn,
                f'{self.table.table_arn}/*',
            ],
        )

        for policy_name in ('read', 'default'):
            read_policy_stements = [
                self.read_access_statement,
            ]

            if not exclude_from_discovery:
                read_policy_stements.append(self._discovery_resource.access_statement)

            self.read_access_policy = ResourceAccessPolicy(
                scope=scope,
                policy_name=policy_name,
                policy_statements=read_policy_stements,
                resource_name=table_name,
                resource_type=ResourceType.TABLE,
            )

        write_policy_statements = [
            self.read_write_access_statement,
        ]

        if not exclude_from_discovery:
            write_policy_statements.append(self._discovery_resource.access_statement)

        self.read_write_access_policy = ResourceAccessPolicy(
            scope=scope,
            policy_name='read_write',
            policy_statements=write_policy_statements,
            resource_name=table_name,
            resource_type=ResourceType.TABLE,
        )

    def grant_read_access(self, resource: Construct):
        """
        Grant read access to the DynamoDB table

        Keyword Arguments:
            resource: Resource to grant access to
        """
        self.table.grant_read_data(resource)

        self._discovery_resource.grant_read(resource=resource)

    def grant_read_write_access(self, resource: Construct):
        """
        Grant read/write access to the DynamoDB table

        Keyword Arguments:
            resource: Resource to grant access to
        """
        self.table.grant_read_write_data(resource)

        self._discovery_resource.grant_read(resource=resource)

    @classmethod
    def from_orm_table_object(cls, table_object: TableObject, scope: Construct,
                              construct_id: Optional[str] = None,
                              exclude_from_discovery: bool = False,
                              removal_policy: Optional[RemovalPolicy] = None,
                              tags: List[Dict[str, Any]] = None) -> 'DynamoDBTable':
        """
        Lazy constructor that allows defining a DynamoDBTable from a TableObject

        Keyword Arguments:
            table_object: The TableObject to use to initialize the DynamoDBTable
            construct_id: Identifier for the construct
            exclude_from_discovery: Whether to exclude the table from discovery
            removal_policy: Removal policy for the DynamoDB table
            scope: Parent construct for the DynamoDBTable
            tags: Tags to apply to the DynamoDB table
            kwargs: Additional arguments to pass to the DynamoDB table

        Returns:
            A DynamoDBTable initialized from the TableObject

        Example:
            ```
            from da_vinci.core.orm import TableObject, TableObjectAttributeType
            from da_vinci_cdk.constructs.dynamodb import DynamoDBTable

            class MyTableObject(TableObject):
                 table_name = 'my_table'

                 partition_key_attribute = TableObjectAttribute(
                     name='table_object_id',
                     attribute_type=TableObjectAttributeType.STRING,
                 )

                 attributes = [
                     TableObjectAttribute(
                         name='table_object_attribute',
                         attribute_type=TableObjectAttributeType.NUMBER,
                     ),
                 ]


            table = DynamoDBTable.from_orm_table_object(
                table_object=MyTableObject,
                scope=stack,
            )
            ```
        """
        partition_key_type = cls.attribute_type_from_orm_type(
            orm_type=table_object.partition_key_attribute.attribute_type,
        )

        init_args = {
            'construct_id': construct_id,
            'exclude_from_discovery': exclude_from_discovery,
            'partition_key': cdk_dynamodb.Attribute(
                name=table_object.partition_key_attribute.dynamodb_key_name,
                type=partition_key_type,
            ),
            'removal_policy': removal_policy,
            'scope': scope,
            'table_name': table_object.table_name,
            'tags': tags,
        }

        if table_object.sort_key_attribute:
            sort_key_type = cls.attribute_type_from_orm_type(
                orm_type=table_object.sort_key_attribute.attribute_type,
            )

            init_args['sort_key'] = cdk_dynamodb.Attribute(
                name=table_object.sort_key_attribute.dynamodb_key_name,
                type=sort_key_type,
            )

        if table_object.ttl_attribute:
            init_args['time_to_live_attribute'] = table_object.ttl_attribute.dynamodb_key_name

        return cls(**init_args)

    @staticmethod
    def attribute_type_from_orm_type(orm_type: TableObjectAttributeType) -> cdk_dynamodb.AttributeType:
        """
        Return the corresponding DynamoDB AttributeType for a TableObjectAttributeType

        Keyword Arguments:
            orm_type: The TableObjectAttributeType to translate

        Returns:
            The corresponding DynamoDB AttributeType
        """

        if orm_type is TableObjectAttributeType.DATETIME \
                or orm_type is TableObjectAttributeType.NUMBER:
            return cdk_dynamodb.AttributeType.NUMBER

        return cdk_dynamodb.AttributeType.STRING

    @staticmethod
    def table_full_name_lookup(scope: Construct, table_name: str, 
                               app_name: Optional[str] = None,
                               deployment_id: Optional[str] = None,
                               resource_discovery_storage_solution: str = ResourceDiscoveryStorageSolution.SSM) -> str:
        """
        Lookup the full name for the DynamoDB table

        Keyword Arguments:
            table_name: Name of the DynamoDB table
            app_name: Name of the application
            deployment_id: Unique identifier for the installation
            scope: Parent construct for the DynamoDBTable.
        """

        return DiscoverableResource.read_endpoint(
            resource_name=table_name,
            resource_type=ResourceType.TABLE,
            scope=scope,
            app_name=app_name,
            deployment_id=deployment_id,
            storage_solution=resource_discovery_storage_solution,
        )


DEFAULT_ITEM_TYPE_NAME = custom_type_name(name='DynamoDBItem')


class DynamoDBItem(Construct):
    def __init__(self, construct_id: str, scope: Construct, table_object: TableObject,
                 custom_type_name: Optional[str] = DEFAULT_ITEM_TYPE_NAME, support_updates: bool = False):
        """
        Initialize a DynamoDBItem object

        DynamoDBItem is a wrapper around a DynamoDB item that is used to store a
        value in a DynamoDB table.

        Keyword Arguments:
            construct_id: Identifier for the construct
            custom_type_name: The custom resource type name to use for the custom resource
            scope: Parent construct for the CrossStackVariable
            support_updates: Whether the item supports updates
            table_object: The TableObject to use to initialize the DynamoDBItem
        """
        super().__init__(scope, construct_id)

        self.custom_type_name = custom_type_name

        resource_discovery_storage_solution = self.node.get_context('resource_discovery_storage_solution')

        self.full_table_name = DynamoDBTable.table_full_name_lookup(
            scope=self,
            resource_discovery_storage_solution=resource_discovery_storage_solution,
            table_name=table_object.table_name,
        )

        on_update = None

        if support_updates:
            on_update = self.update(table_object)

        self.resource = AwsCustomResource(
            scope=self,
            id=f'{construct_id}-custom-resource',
            policy=AwsCustomResourcePolicy.from_sdk_calls(
                resources=[
                    f'arn:aws:dynamodb:*:*:table/{self.full_table_name}',
                    f'arn:aws:dynamodb:*:*:table/{self.full_table_name}/*',
                ]
            ),
            on_create=self.put(table_object),
            on_delete=self.delete(table_object),
            on_update=on_update,
            resource_type=self.custom_type_name,
        )

    @staticmethod
    def is_attribute_changed(attr_name: str, new_value: Any, old_item_call: AwsSdkCall) -> bool:
        """
        Compare attribute values between old and new state

        Keyword Arguments:
            attr_name: Name of the attribute to compare
            new_value: New value of the attribute
            old_item_call: GetItem call result containing the old state

        Returns:
            bool: True if the attribute has changed, False otherwise
        """
        try:
            old_item = old_item_call.get('Item', {})

            if attr_name not in old_item:
                return True

            return old_item[attr_name] != new_value

        except Exception:
            # If we can't compare (e.g., first update), assume changed
            return True

    @staticmethod
    def physical_resource_id(table_object: TableObject) -> PhysicalResourceId:
        """
        Return the physical resource ID for the custom resource

        Keyword Arguments:
            table_object: The TableObject to use to initialize the DynamoDBItem

        Returns:
            The physical resource ID for the custom resource
        """
        resource_id_items = [
            table_object.table_name,
            table_object.partition_key_attribute.dynamodb_key_name,
        ]

        if table_object.sort_key_attribute:
            resource_id_items.append(table_object.sort_key_attribute.dynamodb_key_name)

        return PhysicalResourceId.of('-'.join(resource_id_items))

    def put(self, table_object: TableObject) -> AwsSdkCall:
        """
        Call AWS SDK to put the DynamoDB item

        Keyword Arguments:
            table_object: The TableObject to use to initialize the DynamoDBItem
        """
        return AwsSdkCall(
            action='putItem',
            service='DynamoDB',
            parameters={
                'Item': table_object.to_dynamodb_item(),
                'TableName': self.full_table_name,
            },
            physical_resource_id=self.physical_resource_id(table_object),
        )

    def update(self, table_object: TableObject) -> AwsSdkCall:
        """
        Call AWS SDK to update the DynamoDB item if there are changes
        Uses UpdateItem with SET operations for changed non-key attributes

        Keyword Arguments:
            table_object: The TableObject to use to initialize the DynamoDBItem

        Returns:
            AwsSdkCall: The update call if there are changes, or a no-op call if no changes
        """
        # Get the item's key attributes
        partition_key_value = table_object.attribute_value(table_object.partition_key_attribute.name)

        sort_key_value = None

        if table_object.sort_key_attribute:
            sort_key_value = table_object.attribute_value(table_object.sort_key_attribute.name)

        item_key = table_object.gen_dynamodb_key(
            partition_key_value=partition_key_value,
            sort_key_value=sort_key_value,
        )

        # Get the current state and compare with old state
        dynamodb_item = table_object.to_dynamodb_item()

        # Get the previous state from CloudFormation's old_value
        get_item_call = AwsSdkCall(
            action='getItem',
            service='DynamoDB',
            parameters={
                'Key': item_key,
                'TableName': self.full_table_name,
                'ConsistentRead': True
            },
            physical_resource_id=self.physical_resource_id(table_object),
        )

        # Compare attributes and only update those that changed
        update_expressions = []

        expression_values = {}

        expression_names = {}

        for attr_name, attr_value in dynamodb_item.items():
            # Skip key attributes as they can't be updated
            if (attr_name == table_object.partition_key_attribute.dynamodb_key_name or 
                (table_object.sort_key_attribute and 
                 attr_name == table_object.sort_key_attribute.dynamodb_key_name)):
                continue

            # Check if the attribute value has changed
            if not self.is_attribute_changed(attr_name, attr_value, get_item_call):
                continue

            placeholder = f":val_{attr_name}"

            update_expressions.append(f"#{attr_name} = {placeholder}")

            expression_values[placeholder] = attr_value

            expression_names[f"#{attr_name}"] = attr_name

        # If nothing changed, return a no-op call
        if not update_expressions:
            return None

        return AwsSdkCall(
            action='updateItem',
            service='DynamoDB',
            parameters={
                'Key': item_key,
                'TableName': self.full_table_name,
                'UpdateExpression': f"SET {', '.join(update_expressions)}",
                'ExpressionAttributeNames': expression_names,
                'ExpressionAttributeValues': expression_values,
            },
            physical_resource_id=self.physical_resource_id(table_object),
        )

    def delete(self, table_object: TableObject) -> AwsSdkCall:
        """
        Call AWS SDK to delete the DynamoDB item

        Keyword Arguments:
            table_object: The TableObject to use to initialize the DynamoDBItem
        """
        partition_key_value=table_object.attribute_value(table_object.partition_key_attribute.name)

        sort_key_value = None

        if table_object.sort_key_attribute:
            sort_key_value=table_object.attribute_value(table_object.sort_key_attribute.name)

        item_key = table_object.gen_dynamodb_key(
            partition_key_value=partition_key_value,
            sort_key_value=sort_key_value,
        )

        return AwsSdkCall(
            action='deleteItem',
            service='DynamoDB',
            parameters={
                'Key': item_key,
                'TableName': self.full_table_name,
            },
            physical_resource_id=self.physical_resource_id(table_object),
        )