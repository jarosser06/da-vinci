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

from da_vinci.event_bus.tables.event_bus_subscriptions import EventBusSubscription

from da_vinci_cdk.constructs.access_management import ResourceAccessPolicy, ResourceAccessRequest
from da_vinci_cdk.constructs.dynamodb import DynamoDBTable
from da_vinci_cdk.constructs.lambda_function import LambdaFunction

class EventBusSubscription(Construct):
    '''Event Bus Event Subscription CDK Construct'''

    def __init__(self, event_type: str, function_name: str, scope: Construct, subscribed_to: str,
                  active: Optional[bool] = False, generates_events: Optional[List[str]] = None,
                  table_name: Optional[str] = None):

        construct_id = f'{function_name}-event-bus-subscription-{subscribed_to}'

        super().__init__(scope, construct_id)

        if table_name:
            self.table_name = table_name
        else:
            self.table_name = DynamoDBTable.table_full_name_lookup(
                scope=self,
                table_name='event_bus_subscriptions',
            )

        event_bus_subscription = EventBusSubscription(
            active=active,
            event_type=event_type,
            function_name=function_name,
            generates_events=generates_events,
            subscribed_to=subscribed_to,
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
            on_update=self._update(event_bus_subscription),
            resource_type='DaVinciFramework::EventBusSubscription',
        )

    def _create(self, event_bus_subscription: EventBusSubscription):
        '''Create the event bus subscription'''

        return AwsSdkCall(
            action='putItem',
            service='DynamoDB',
            parameters={
                'TableName': self.table_name,
                'Item': event_bus_subscription.to_dynamodb_item(),
            },
            physical_resource_id=PhysicalResourceId.of(event_bus_subscription.subscription_id),
        )

    def _delete(self, event_bus_subscription: EventBusSubscription):
        '''Delete the event bus subscription'''

        return AwsSdkCall(
            action='deleteItem',
            service='DynamoDB',
            parameters={
                'TableName': self.table_name,
                'Key': {
                    'event_type': event_bus_subscription.event_type,
                    'function_name': event_bus_subscription.function_name,
                },
            },
            physical_resource_id=PhysicalResourceId.of(event_bus_subscription.subscription_id),
        )

    def _update(self, event_bus_subscription: EventBusSubscription):
        '''Update the event bus subscription'''

        return AwsSdkCall(
            action='putItem',
            service='DynamoDB',
            parameters={
                'TableName': self.table_name,
                'Item': event_bus_subscription.to_dynamodb_item(),
            },
            physical_resource_id=PhysicalResourceId.of(event_bus_subscription.subscription_id),
        )


class EventBusSubscriptionFunction(Construct):
    '''Event Bus Event Subscription Function CDK Construct'''

    def __init__(self, construct_id: str, event_type: str, scope: Construct,
                 subscribed_to: str, active: Optional[bool] = False,
                 generates_events: Optional[List[str]] = None,
                 managed_policies: Optional[List] = None, **function_config):
        """
        Creates a Lambda function that subscribes to an event bus event. Handles the creation
        of the subscription in DynamoDB as well as the Lambda Function itself. This construct
        will also create the necessary IAM policies to allow the function to provide it's response
        as well as subscribe to the event bus in the event it generates_events and the event
        response service automatically.

        Keyword Arguments:
            construct_id: ID of the construct
            event_type: Type of event to subscribe to
            scope: Parent construct for the EventBusSubscriptionFunction
            subscribed_to: Name of the service that is subscribed to the event
            active: Whether or not the subscription is active (default: False)
            generates_events: List of event types that the function generates (default: None)
            managed_policies: List of managed policies to attach to the Lambda function
            function_config: Additional arguments supported by CDK to pass to the Lambda function
        """

        construct_id = f'{construct_id}-event-bus-subscription-{subscribed_to}'

        super().__init__(scope, construct_id)

        self.function = LambdaFunction(
            scope=self,
            construct_id=f'{construct_id}-fn',
            managed_policies=managed_policies,
            **function_config,
        )

        Tags.of(self.function).add(
            key='DaVinciFramework::FunctionPurpose',
            value='EventSubscription',
            priority=200
        )

        event_response_policy_req = ResourceAccessRequest(
            resource_name='event_bus_responses',
            resource_type='rest_service',
        )

        event_response_policy = ResourceAccessPolicy.policy_from_resource_name(
            request=event_response_policy_req,
        )

        if event_response_policy not in managed_policies:
            self.function.role.add_managed_policy(event_response_policy)

        # Grant acccess to the event bus if the function generates events
        if generates_events:
            event_bus_policy_req = ResourceAccessRequest(
                resource_name='event_bus',
                resource_type='async_service',
            )

            event_bus_policy = ResourceAccessPolicy.policy_from_resource_name(
                request=event_bus_policy_req,
            )

            if event_bus_policy not in managed_policies:
                self.function.role.add_managed_policy(event_bus_policy)

        self.subscription = EventBusSubscription(
            active=active,
            event_type=event_type,
            function_name=self.function.function_name,
            generates_events=generates_events,
            subscribed_to=subscribed_to,
            scope=self,
        )