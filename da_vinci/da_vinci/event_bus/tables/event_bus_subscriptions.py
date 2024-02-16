'''Event Bus Subscriptions Table'''

from datetime import datetime
from typing import List, Optional

from da_vinci.core.orm import (
    TableClient,
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
    TableScanDefinition,
)

from da_vinci.event_bus.exceptions import CircularDependencyException


class EventBusSubscription(TableObject):
    description = 'Event Bus Subscriptions'
    table_name = 'event_bus_subscriptions'

    partition_key_attribute = TableObjectAttribute(
        'event_type',
        TableObjectAttributeType.STRING,
        description='The event type that is subscribed to',
    )

    sort_key_attribute = TableObjectAttribute(
        'function_name',
        TableObjectAttributeType.STRING,
        description='The name of the function that is subscribed to the event type',
    )

    attributes = [
        TableObjectAttribute(
            'active',
            TableObjectAttributeType.BOOLEAN,
            default=True,
            description='Whether or not the subscription is active',
        ),

        TableObjectAttribute(
            'generates_events',
            TableObjectAttributeType.STRING_LIST,
            default=[],
            description='The events generated by the subscribed function',
        ),

        TableObjectAttribute(
            'record_created',
            TableObjectAttributeType.DATETIME,
            default=lambda: datetime.utcnow(),
            description='The date EventSubscription record was created',
        ),

        TableObjectAttribute(
            'record_last_updated',
            TableObjectAttributeType.DATETIME,
            default=lambda: datetime.utcnow(),
            description='The date EventSubscription record was last updated',
        )
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._validate_legal_subscription(
            self.generates_events,
            self.function_name,
            self.event_type,
        )

    def execute_on_update(self):
        """
        Execute on update hook for the Event Bus Subscription object.
        """
        self.update_date_attributes(
            date_attribute_names=['record_last_updated'],
            obj=self,
        )

    @staticmethod
    def _validate_legal_subscription(self, generates_events: List[str], function_name: str,
                                     subscribed_event_type: str):
        """
        Validate the event subscription is legal. This means that the event subscription does not
        create a circular dependency.

        Keyword Arguments:
            generates_events: The events generated by the subscribed function.
            function_name: The name of the subscribed function.
            subscription_event_type: The event type of the subscription.
        """
        if subscribed_event_type in generates_events:
            raise CircularDependencyException(subscribed_event_type, function_name)


class EventBusSubscriptionsScanDefinition(TableScanDefinition):
    def __init__(self):
        super().__init__(table_object_class=EventBusSubscription)


class EventBusSubscriptions(TableClient):
    def __init__(self, app_name: Optional[str] = None, deployment_id: Optional[str] = None):
        super().__init__(
            app_name=app_name,
            default_object_class=EventBusSubscription,
            deployment_id=deployment_id,
        )

    def all_active_subscriptions(self, event_type: str) -> List[EventBusSubscription]:
        """
        Return all event subscriptions for a given event type.
        """
        params = {
            'ExpressionAttributeNames': {
                '#ck': 'event_type',
                '#es': 'active',
            },
            'ExpressionAttributeValues': {
                ':cv': {'S': event_type},
                ':esv': {'BOOL': True},
            },
            'FilterExpression': '#es = :esv',
            'KeyConditionExpression': '#ck = :cv',
        }

        all_items = []

        for page in self.paginated(call='query', params=params):
            all_items.extend(page)

        return all_items

    def delete(self, event_subscription: EventBusSubscription):
        """
        Delete an event subscription

        Keyword Arguments:
            event_subscription: The event subscription
        """

        return self.remove_object(event_subscription)

    def get(self, event_type: str, function_name: str) -> EventBusSubscription:
        """
        Return a single event subscription.

        Keyword Arguments:
            event_type: The event type.
            function_name: The function name.
        """

        return self.get_object(
            partition_key_value=event_type,
            sort_key_value=function_name,
        )

    def put(self, event_subscription: EventBusSubscription):
        """
        Create or update an event subscription.

        Keyword Arguments:
            event_subscription: The event subscription
        """

        return self.put_object(event_subscription)

    def scan(self, scan_definition: EventBusSubscriptionsScanDefinition) -> List[EventBusSubscription]:
        """
        Return all event subscriptions.

        Keyword Arguments:
            scan_definition: The scan definition.
        """

        return self.scan_objects(scan_definition=scan_definition)