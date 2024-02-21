'''Event Bus runtime'''
import json

from typing import Dict

import boto3

from da_vinci.core.logging import Logger

from da_vinci.event_bus.client import (
    EventResponder,
    EventResponseStatus,
)
from da_vinci.event_bus.event import Event
from da_vinci.event_bus.tables.event_bus_subscriptions import (
    EventBusSubscriptions
)


LOG = Logger('event_bus')


class EventBus:
    def __init__(self):
        self.aws_lambda = boto3.client('lambda')
        self.event_responder = EventResponder()

    def invoke_subscriptions(self, event: Event):
        """
        Invokes any functions subscribed to the event

        Keyword Arguments:
            event: Event
        """
        LOG.debug(f'Invoking {event.event_type}: {event}')

        subscriptions = EventBusSubscriptions()

        all_subs = subscriptions.all_active_subscriptions(
            event_type=event.event_type
        )

        if not all_subs:
            LOG.debug(f'No subscriptions found for {event.event_type}')

            self.event_responder.response(
                event=event.to_dict(),
                failure_reason='No active subscriptions found',
                status=EventResponseStatus.NO_ROUTE,
            )

            return

        for sub in all_subs:
            response = self.aws_lambda.invoke(
                FunctionName=sub.function_name,
                InvocationType='Event',
                Payload=event.to_json(),
            )

            LOG.debug(f'Lambda invocation response: {response}')


def handler(event: Dict, context: Dict):
    """
    Picks up events from the SQS queue and invokes subscribed functions

    Keyword Arguments:
        event: Event payload
        context: Lambda context
    """
    LOG.debug(f'Event: {event}')

    bus = EventBus()

    for record in event['Records']:
        LOG.debug(f'Record recieved: {record}')

        event = Event.from_lambda_event(json.loads(record['body']))

        bus.invoke_subscriptions(event)
