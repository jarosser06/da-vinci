'''Event Bus Event Subscription CDK Primitive'''
from typing import List, Optional

from aws_cdk import Tags
from aws_cdk.custom_resources import (
    AwsCustomResource,
    AwsCustomResourcePolicy,
    PhysicalResourceId,
    AwsSdkCall,
)

from constructs import Construct

from da_vinci.core.resource_discovery import ResourceType

from da_vinci.event_bus.tables.event_bus_subscriptions import (
    EventBusSubscription as EventBusSubscriptionTblObj,
)

from da_vinci_cdk.constructs.access_management import ResourceAccessRequest
from da_vinci_cdk.constructs.base import custom_type_name
from da_vinci_cdk.constructs.dynamodb import DynamoDBTable
from da_vinci_cdk.constructs.lambda_function import LambdaFunction


class EventBusSubscription(Construct):
    '''Event Bus Event Subscription CDK Construct'''

    def __init__(self, construct_id: str, event_type: str, function_name: str, scope: Construct,
                 active: Optional[bool] = False, generates_events: Optional[List[str]] = None,
                 table_name: Optional[str] = None):
        """
        Creates a subscription to an event bus event in DynamoDB. This construct will create
        the necessary DynamoDB table if it does not exist and will create the subscription
        in the table.

        Keyword Arguments:
            construct_id: ID of the construct
            event_type: Type of event to subscribe to
            function_name: Name of the function
            scope: Parent construct for the EventBusSubscription
            active: Whether or not the subscription is active (default: False)
            generates_events: List of event types that the function generates (default: None)
            table_name: Name of the DynamoDB table to use (default: None)
        """

        super().__init__(scope, construct_id)

        if table_name:
            self.table_name = table_name
        else:
            self.table_name = DynamoDBTable.table_full_name_lookup(
                scope=self,
                table_name='event_bus_subscriptions',
            )

        event_bus_subscription = EventBusSubscriptionTblObj(
            active=active,
            event_type=event_type,
            function_name=function_name,
            generates_events=generates_events,
        )

        table_arn = f'arn:aws:dynamodb:*:*:table/{self.table_name}'

        self.resource = AwsCustomResource(
            scope=self,
            id=f'{construct_id}-cr',
            policy=AwsCustomResourcePolicy.from_sdk_calls(
                resources=[table_arn, f'{table_arn}/*'],
            ),
            on_create=self._create(event_bus_subscription),
            on_delete=self._delete(event_bus_subscription),
            resource_type=custom_type_name(name='EventBusSubscription'),
        )

    def _create(self, event_bus_subscription: EventBusSubscriptionTblObj):
        '''Create the event bus subscription'''
        subscription_id = event_bus_subscription.event_type + '-' + event_bus_subscription.function_name

        return AwsSdkCall(
            action='putItem',
            service='DynamoDB',
            parameters={
                'TableName': self.table_name,
                'Item': event_bus_subscription.to_dynamodb_item(),
            },
            physical_resource_id=PhysicalResourceId.of(subscription_id),
        )

    def _delete(self, event_bus_subscription: EventBusSubscriptionTblObj):
        '''Delete the event bus subscription'''
        subscription_id = event_bus_subscription.event_type + '-' + event_bus_subscription.function_name

        return AwsSdkCall(
            action='deleteItem',
            service='DynamoDB',
            parameters={
                'TableName': self.table_name,
                'Key': event_bus_subscription.gen_dynamodb_key(
                    partition_key_value=event_bus_subscription.event_type,
                    sort_key_value=event_bus_subscription.function_name,
                ),
            },
            physical_resource_id=PhysicalResourceId.of(subscription_id),
        )


class EventBusSubscriptionFunction(Construct):
    '''Event Bus Event Subscription Function CDK Construct'''

    def __init__(self, construct_id: str, event_type: str, function_name: str, scope: Construct,
                 active: Optional[bool] = False, enable_event_bus_access: Optional[bool] = False,
                 generates_events: Optional[List[str]] = None, managed_policies: Optional[List] = None,
                 resource_access_requests: Optional[List[ResourceAccessRequest]] = None, **function_config):
        """
        Creates a Lambda function that subscribes to an event bus event. Handles the creation
        of the subscription in DynamoDB as well as the Lambda Function itself. This construct
        will also create the necessary IAM policies to allow the function to provide it's response
        as well as subscribe to the event bus in the event it generates_events and the event
        response service automatically.

        Keyword Arguments:
            construct_id: ID of the construct
            event_type: Type of event to subscribe to
            function_name: Name of the function
            scope: Parent construct for the EventBusSubscriptionFunction
            active: Whether or not the subscription is active (default: False)
            enable_event_bus_access: Whether or not to enable access to the event bus (default: False)
            generates_events: List of event types that the function generates (default: None)
            managed_policies: List of managed policies to attach to the Lambda function
            function_config: Additional arguments supported by CDK to pass to the Lambda function
        """
        super().__init__(scope, construct_id)

        add_event_bus_access = enable_event_bus_access

        if not add_event_bus_access and generates_events:
            add_event_bus_access = True

        add_event_response_access = True

        if resource_access_requests:
                for existing_req in resource_access_requests:
                    if existing_req.resource_name == 'event_bus':
                        add_event_bus_access = False

                    if existing_req.resource_name == 'event_bus_responses':
                        add_event_response_access = False
        else:
            resource_access_requests = []

        if add_event_bus_access:
            resource_access_requests.append(
                ResourceAccessRequest(
                    resource_name='event_bus',
                    resource_type=ResourceType.ASYNC_SERVICE,
                )
            )

        if add_event_response_access:
            resource_access_requests.append(
                ResourceAccessRequest(
                    resource_name='event_bus_responses',
                    resource_type=ResourceType.REST_SERVICE,
                )
            )

        self.handler = LambdaFunction(
            scope=self,
            construct_id=f'{construct_id}-fn',
            function_name=function_name,
            managed_policies=managed_policies,
            resource_access_requests=resource_access_requests,
            **function_config,
        )

        Tags.of(self.handler.function).add(
            key='DaVinciFramework::FunctionPurpose',
            value='EventSubscription',
            priority=200
        )

        self.subscription = EventBusSubscription(
            active=active,
            construct_id=f'{construct_id}-subscription',
            event_type=event_type,
            function_name=self.handler.function.function_name,
            generates_events=generates_events,
            scope=self,
        )