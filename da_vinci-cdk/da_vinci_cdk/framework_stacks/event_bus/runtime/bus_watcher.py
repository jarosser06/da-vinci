'''Lambda module for the event bus watcher'''
from typing import Dict, Optional

from da_vinci.core.rest_service_base import (
    Route,
    SimpleRESTServiceBase,
)
from da_vinci.event_bus.tables.event_bus_responses import (
    EventBusSubscriptionResponse,
    EventBusSubscriptionResponses,
)


class EventBusWatcher(SimpleRESTServiceBase):
    def __init__(self):
        self.event_responses = EventBusSubscriptionResponses()

        super().__init__(
            routes=[
                Route(
                    handler=self.trap_response,
                    method='POST',
                    path='/',
                )
            ]
        )

    def trap_response(self, event: Dict, status: str,
                      failure_reason: Optional[str] = None,
                      failure_traceback: Optional[str] = None):
        """
        Trap an event response

        Keyword Arguments:
            event: The originating event
            status: The status of the response
            failure_reason: The reason for the failure
            failure_traceback: The traceback of the failure
        """
        response = EventBusSubscriptionResponse(
            event_type=event['event_type'],
            failure_reason=failure_reason,
            failure_traceback=failure_traceback,
            original_event_body=event,
            originating_event_id=event['event_id'],
            response_status=status,
        )

        self.event_responses.put(response)

        return self.respond(
            body={'message': 'response saved'},
            status_code=201,
        )


def api(event: Dict, context: Dict):
    """
    API handler for the event bus watcher

    Keyword Arguments:
        event: The event
        context: The context
    """
    watcher = EventBusWatcher()

    return watcher.handle(event=event)