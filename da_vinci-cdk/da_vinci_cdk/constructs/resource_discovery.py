from typing import Any, Optional

from constructs import Construct

from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_iam as cdk_iam,
)

from aws_cdk.custom_resources import (
    AwsCustomResource,
    AwsCustomResourcePolicy,
    AwsSdkCall,
    PhysicalResourceId,
)

from da_vinci.core.orm.table_object import TableObject
from da_vinci.core.resource_discovery import ResourceDiscovery, ResourceDiscoveryStorageSolution
from da_vinci.core.tables.resource_registry import ResourceRegistration

from da_vinci_cdk.constructs.base import (
    custom_type_name,
    resource_namer,
    GlobalVariable,
)


class DiscoverableResourceDynamoDBItem(Construct):
    def __init__(self, construct_id: str, scope: Construct, endpoint: str, registration_name: str, registration_type: str):
        """
        Initialize a DiscoverableResourceDynamoDBItem object

        Keyword Arguments:
            construct_id: Identifier for the construct
            scope: Parent construct for the DiscoverableResourceDynamoDBItem
            endpoint: The endpoint for the resource
            registration_name: Name of the resource registration
            registration_type: Type of the resource registration
        """
        super().__init__(scope, construct_id)

        self.custom_type_name = custom_type_name(name='DiscoverableResourceDynamoDBItem')

        self.registration_obj = ResourceRegistration(
            endpoint=endpoint,
            resource_name=registration_name,
            resource_type=registration_type,
        )

        tbl_name = scope.node.get_context('resource_discovery_table_name')

        # DynamoDB Endpoints are just the actual table name, can use resource_namer
        # to determine the exact table name
        self.full_table_name = resource_namer(name=tbl_name, scope=self)

        self.resource = AwsCustomResource(
            scope=self,
            id=f'{construct_id}-custom-resource',
            policy=AwsCustomResourcePolicy.from_sdk_calls(
                resources=[
                    f'arn:aws:dynamodb:*:*:table/{self.full_table_name}',
                    f'arn:aws:dynamodb:*:*:table/{self.full_table_name}/*',
                ]
            ),
            on_create=self.put(self.registration_obj),
            on_delete=self.delete(self.registration_obj),
            on_update=self.update(self.registration_obj),
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
    def physical_resource_id(registration: TableObject) -> PhysicalResourceId:
        """
        Return the physical resource ID for the custom resource

        Keyword Arguments:
            registration: The TableObject to use to initialize the DynamoDBItem

        Returns:
            The physical resource ID for the custom resource
        """
        resource_id_items = [
            registration.table_name,
            registration.partition_key_attribute.dynamodb_key_name,
        ]

        if registration.sort_key_attribute:
            resource_id_items.append(registration.sort_key_attribute.dynamodb_key_name)

        return PhysicalResourceId.of('-'.join(resource_id_items))

    def access_statement(self) -> cdk_iam.PolicyStatement:
        """
        Generate a policy statement to access the DynamoDB item
        """
        return cdk_iam.PolicyStatement(
            actions=[
                'dynamodb:GetItem'
            ],
            resources=[
                f'arn:aws:dynamodb:*:*:table/{self.full_table_name}',
            ]
        )

    def put(self, registration: ResourceRegistration) -> AwsSdkCall:
        """
        Call AWS SDK to put the DynamoDB item

        Keyword Arguments:
            registration: The TableObject to use to initialize the DynamoDBItem
        """
        return AwsSdkCall(
            action='putItem',
            service='DynamoDB',
            parameters={
                'Item': registration.to_dynamodb_item(),
                'TableName': self.full_table_name,
            },
            physical_resource_id=self.physical_resource_id(registration),
        )

    def update(self, registration: ResourceRegistration) -> AwsSdkCall:
        """
        Call AWS SDK to update the DynamoDB item if there are changes
        Uses UpdateItem with SET operations for changed non-key attributes

        Keyword Arguments:
            registration: The TableObject to use to initialize the DynamoDBItem

        Returns:
            AwsSdkCall: The update call if there are changes, or a no-op call if no changes
        """
        # Get the item's key attributes
        partition_key_value = registration.attribute_value(registration.partition_key_attribute.name)

        sort_key_value = None

        if registration.sort_key_attribute:
            sort_key_value = registration.attribute_value(registration.sort_key_attribute.name)

        item_key = registration.gen_dynamodb_key(
            partition_key_value=partition_key_value,
            sort_key_value=sort_key_value,
        )

        # Get the current state and compare with old state
        dynamodb_item = registration.to_dynamodb_item()

        # Get the previous state from CloudFormation's old_value
        get_item_call = AwsSdkCall(
            action='getItem',
            service='DynamoDB',
            parameters={
                'Key': item_key,
                'TableName': self.full_table_name,
                'ConsistentRead': True
            },
            physical_resource_id=self.physical_resource_id(registration),
        )

        # Compare attributes and only update those that changed
        update_expressions = []

        expression_values = {}

        expression_names = {}

        for attr_name, attr_value in dynamodb_item.items():
            # Skip key attributes as they can't be updated
            if (attr_name == registration.partition_key_attribute.dynamodb_key_name or 
                (registration.sort_key_attribute and 
                 attr_name == registration.sort_key_attribute.dynamodb_key_name)):
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
            physical_resource_id=self.physical_resource_id(registration),
        )

    def delete(self, registration: ResourceRegistration) -> AwsSdkCall:
        """
        Call AWS SDK to delete the DynamoDB item

        Keyword Arguments:
            registration: The TableObject to use to initialize the DynamoDBItem
        """
        partition_key_value=registration.attribute_value(registration.partition_key_attribute.name)

        sort_key_value = None

        if registration.sort_key_attribute:
            sort_key_value=registration.attribute_value(registration.sort_key_attribute.name)

        item_key = registration.gen_dynamodb_key(
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
            physical_resource_id=self.physical_resource_id(registration),
        )


class DiscoverableResourceDynamoDBLookup(Construct):
    """
    Lookup construct for discovering resources in DynamoDB
    This is a separate construct to allow for clean lifecycle management
    """
    def __init__(self, scope: Construct, construct_id: str, resource_name: str, resource_type: str, table_name: str):
        super().__init__(scope, construct_id)

        self.full_table_name = resource_namer(name=table_name, scope=self)

        self.resource_name = resource_name

        self.resource_type = resource_type

        # Generate the DynamoDB key
        self.item_key = ResourceRegistration.gen_dynamodb_key(
            partition_key_value=resource_type,
            sort_key_value=resource_name,
        )

        # Create a custom resource to look up the value
        self.lookup_resource = AwsCustomResource(
            scope=self,
            id=f'{construct_id}-lookup',
            policy=AwsCustomResourcePolicy.from_sdk_calls(
                resources=[
                    f'arn:aws:dynamodb:*:*:table/{self.full_table_name}',
                    f'arn:aws:dynamodb:*:*:table/{self.full_table_name}/*',
                ]
            ),
            on_create=self._get_item_call(),
            on_update=self._get_item_call(),
            resource_type='Custom::DynamoDBLookup',
        )

    def _get_item_call(self) -> AwsSdkCall:
        """
        Create a GetItem AWS SDK call for the resource lookup
        
        Returns:
            AwsSdkCall: The GetItem call configuration
        """
        return AwsSdkCall(
            action='getItem',
            service='DynamoDB',
            parameters={
                'Key': self.item_key,
                'TableName': self.full_table_name,
                'ConsistentRead': True
            },
            physical_resource_id=PhysicalResourceId.of(
                f'{self.resource_type}-{self.resource_name}-lookup'
            )
        )
    
    def get_endpoint(self) -> str:
        """
        Get the endpoint from the lookup result
        
        Returns:
            str: The endpoint of the discovered resource
        """
        endpoint_attribute = 'Endpoint'

        return self.lookup_resource.get_response_field(f'Item.{endpoint_attribute}.S')


class DiscoverableResource(Construct):
    def __init__(self, construct_id: str, scope: Construct, resource_endpoint: str,
                 resource_name: str, resource_type: str, app_name: Optional[str] = None,
                 deployment_id: Optional[str] = None, resource_discovery_storage_solution: Optional[str] = None):
        """
        Initialize a DiscoverableResource object to 

        ServiceDiscovery is a wrapper around a service discovery resource that
        provisions a resource utilizing the core service discovery pattern.

        Keyword Arguments:
            construct_id: Identifier for the construct
            scope: Parent construct for the ServiceDiscovery
            app_name: Name of the application
            deployment_id: Unique identifier for the installation
            resource_name: Name of the resource
            resource_type: Type of the resource
            resource_endpoint: The endpoint for the resource
            resource_discovery_storage_solution: The storage solution to use for resource discovery
        """
        super().__init__(scope, construct_id)

        self.app_name = app_name or scope.node.get_context('app_name')

        self.deployment_id = deployment_id or scope.node.get_context('deployment_id')

        self.storage_solution = resource_discovery_storage_solution or scope.node.get_context('resource_discovery_storage_solution')

        self.resource_endpoint = resource_endpoint

        self.resource_name = resource_name

        self.resource_type = resource_type

        if self.storage_solution == ResourceDiscoveryStorageSolution.SSM:
            ssm_key = self._gen_ssm_parameter_name(
                app_name=self.app_name,
                deployment_id=self.deployment_id,
                resource_name=self.resource_name,
                resource_type=self.resource_type,
            )

            self.parameter = GlobalVariable(
                construct_id=f'resource-discovery-ssm-parameter-{self.resource_name}',
                scope=self,
                ssm_key=ssm_key,
                ssm_value=self.resource_endpoint,
            )

            self.access_statement = self.parameter.access_statement()

        else:
            self.dynamodb_item = DiscoverableResourceDynamoDBItem(
                construct_id=f'resource-discovery-dynamodb-item-{self.resource_type}-{self.resource_name}',
                scope=self,
                endpoint=self.resource_endpoint,
                registration_name=self.resource_name,
                registration_type=self.resource_type,
            )

            self.access_statement = self.dynamodb_item.access_statement()

    @staticmethod
    def _gen_ssm_parameter_name(app_name: str, deployment_id: str, resource_name: str,
                                resource_type: str) -> str:
        """
        Generate a resource name for a service discovery resource

        Keyword Arguments:
            app_name: Name of the application
            deployment_id: Unique identifier for the installation
            resource_name: Name of the resource
            resource_type: Type of the resource
        """

        return ResourceDiscovery.ssm_parameter_name(
            app_name=app_name,
            deployment_id=deployment_id,
            resource_name=resource_name,
            resource_type=resource_type,
        )

    @classmethod
    def read_endpoint(cls, resource_name: str, resource_type: str, scope: Construct,
                      app_name: Optional[str] = None, deployment_id: Optional[str] = None,
                      storage_solution: str = ResourceDiscoveryStorageSolution.SSM) -> str:
        """
        Read the endpoint for a service discovery resource

        Keyword Arguments:
            resource_name: Name of the resource
            resource_type: Type of the resource
            app_name: Name of the application
            deployment_id: Unique identifier for the installation
            scope: Parent construct for the ServiceDiscovery.
            storage_solution: The storage solution to use for resource discovery
        """
        lookup_args = {'resource_name': resource_name, 'resource_type': resource_type}

        lookup_args['app_name'] = app_name or scope.node.get_context('app_name')

        lookup_args['deployment_id'] = deployment_id or scope.node.get_context('deployment_id')

        actual_storage_solution = storage_solution or scope.node.get_context(
            'resource_discovery_storage_solution'
        )

        for arg_name, arg_value in lookup_args.items():
            if not arg_value:
                raise ValueError(f'{arg_name} must not be None')

        try:
            # Use SSM Parameter Store for lookup
            if actual_storage_solution == ResourceDiscoveryStorageSolution.SSM:
                ssm_key = cls._gen_ssm_parameter_name(**lookup_args)

                endpoint = GlobalVariable.load_variable(
                    scope=scope,
                    ssm_key=ssm_key,
                )

                return endpoint
            
            # Use DynamoDB for lookup
            else:
                table_name = scope.node.get_context('resource_discovery_table_name')
                
                if not table_name:
                    raise ValueError("resource_discovery_table_name must be set in context")
                
                # Create a construct ID that is unique to this lookup
                construct_id = f'resource-discovery-lookup-{resource_type}-{resource_name}'
                
                # Create the lookup construct
                lookup = DiscoverableResourceDynamoDBLookup(
                    scope=scope,
                    construct_id=construct_id,
                    resource_name=resource_name,
                    resource_type=resource_type,
                    table_name=table_name
                )
                
                # Get the endpoint from the lookup
                return lookup.get_endpoint()
                
        except Exception as e:
            # Create a descriptive error
            error_msg = (
                f"Failed to look up resource '{resource_name}' of type '{resource_type}' "
                f"using {actual_storage_solution}. Original error: {str(e)}"
            )
            # You might want to add logging here with your CDK logger
            raise RuntimeError(error_msg) from e

    def grant_read(self, resource: Construct):
        """
        Grant read access to the resource

        """
        if self.storage_solution == ResourceDiscoveryStorageSolution.SSM:
            self.parameter.grant_read(resource)

        else:
            # Get a reference to the DynamoDB table
            table = dynamodb.TableV2.from_table_name(
                scope=self,
                id=f'imported-table-{self.dynamodb_item.full_table_name}',
                table_name=self.dynamodb_item.full_table_name,
            )

            return table.grant_read_data(resource)