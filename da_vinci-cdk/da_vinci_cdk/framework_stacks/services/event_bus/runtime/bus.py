"""
Event Bus Router

# Last version this file was updated for:
version: 2025.3.16
"""
import json
import logging

from typing import Dict
from uuid import uuid4

import boto3

from da_vinci.core.json import DaVinciObjectEncoder

from da_vinci.event_bus.client import EventResponder, EventResponseStatus
from da_vinci.event_bus.event import Event

from da_vinci.event_bus.tables.event_bus_subscriptions import EventBusSubscriptions



class EventBus:
    def __init__(self):
        """
        Initialize the EventBus object
        """
        self.aws_lambda = boto3.client('lambda')

        self.event_responder = EventResponder()

    def invoke_subscriptions(self, event: Event):
        """
        Invokes any functions subscribed to the event

        Keyword Arguments:
            event: Event
        """
        logging.debug(f"Invoking {event.event_type}: {event}")

        subscriptions = EventBusSubscriptions()

        all_subs = subscriptions.all_active_subscriptions(
            event_type=event.event_type
        )

        if not all_subs:
            logging.debug(f"No subscriptions found for {event.event_type}")

            self.event_responder.response(
                event=event.to_dict(),
                failure_reason="No active subscriptions found",
                status=EventResponseStatus.NO_SUBSCRIPTIONS,
            )

            return

        for sub in all_subs:
            logging.debug("Recording request in response table as routed")

            # Generate unique response id for each invocation
            response_id = str(uuid4())

            logging.debug(f"Setting response id: {response_id}")

            event.response_id = response_id

            self.event_responder.response(
                event=event.to_dict(),
                response_id=response_id,
                status=EventResponseStatus.INITIALIZED,
            )

            logging.debug(f"Invoking {sub.function_name}")

            response = self.aws_lambda.invoke(
                FunctionName=sub.function_name,
                InvocationType="Event",
                Payload=json.dumps(event.to_dict(), cls=DaVinciObjectEncoder),
            )

            logging.debug(f"Lambda invocation response: {response}")


def handler(event: Dict, context: Dict):
    """
    Picks up events from the SQS queue and invokes subscribed functions

    Keyword Arguments:
        event: Event payload
        context: Lambda context
    """
    logging.debug(f"Event: {event}")

    bus = EventBus()

    for record in event["Records"]:
        logging.debug(f"Record recieved: {record}")

        event = Event.from_lambda_event(json.loads(record["body"]))

        bus.invoke_subscriptions(event)