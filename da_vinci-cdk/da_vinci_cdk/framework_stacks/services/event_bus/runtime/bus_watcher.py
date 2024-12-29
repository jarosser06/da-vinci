'''Lambda module for the event bus watcher'''
from datetime import datetime, timedelta, UTC as utc_tz
from typing import Dict, Optional

from da_vinci.core.global_settings import setting_value

from da_vinci.core.rest_service_base import (
    Route,
    SimpleRESTServiceBase,
)

from da_vinci.event_bus.tables.event_bus_responses import (
    EventBusResponse,
    EventBusResponses,
)


class EventBusWatcher(SimpleRESTServiceBase):
    def __init__(self):
        """
        Initialize the EventBusWatcher
        """
        self.event_responses = EventBusResponses()

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
        Trap an event response to store it in the database

        Keyword Arguments:
            event: The originating event
            status: The status of the response
            failure_reason: The reason for the failure
            failure_traceback: The traceback of the failure
        """
        response_retention = setting_value('da_vinci_framework::event_bus', 'response_retention_hours')

        response = EventBusResponse(
            event_type=event['event_type'],
            failure_reason=failure_reason,
            failure_traceback=failure_traceback,
            original_event_body=event,
            originating_event_id=event['event_id'],
            response_status=status,
            time_to_live=datetime.now(tz=utc_tz) + timedelta(hours=response_retention),
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