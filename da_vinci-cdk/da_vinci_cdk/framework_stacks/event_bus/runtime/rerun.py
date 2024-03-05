from typing import Dict

from da_vinci.core.rest_service_base import (
    Route,
    SimpleRESTServiceBase,
)
from da_vinci.event_bus.client import EventPublisher
from da_vinci.event_bus.event import Event
from da_vinci.event_bus.tables.event_bus_responses import (
    EventBusSubscriptionResponses,
)


class EventRerun(SimpleRESTServiceBase):
    def __init__(self):
        self.event_responses = EventBusSubscriptionResponses()
        self.publisher = EventPublisher()

        super().__init__(
            routes=[
                Route(
                    handler=self.rerun,
                    method='POST',
                    path='/',
                )
            ]
        )

    def rerun(self, event_type: str, response_id: str):
        """
        Pull an event from an event response and publish it back
        into the event bus for reprocessing.

        Keyword Arguments:
            event_type: The type of event to rerun
            response_id: The response ID of the event to rerun
        """
        event_response = self.event_responses.get(
            event_type=event_type,
            response_id=response_id,
        )

        if not event_response:
            return self.respond(
                body={'message': 'event response not found'},
                status_code=404,
            )

        u_event = Event(**event_response.event_body)

        self.publisher.publish(u_event)

        return self.respond(
            body={'message': 'event submitted for reprocessing'},
            status_code=201,
        )


def api(event: Dict, context: Dict):
    """
    API handler for the event rerun service

    Keyword Arguments:
        event: The event
        context: The context
    """
    re_run = EventRerun()

    return re_run.handle(event=event)