"""Lambda module for the event bus watcher"""

import logging
from datetime import UTC, datetime, timedelta

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
    def __init__(self) -> None:
        """
        Initialize the EventBusWatcher
        """
        self.event_responses = EventBusResponses()

        super().__init__(
            routes=[
                Route(
                    handler=self.trap_response,
                    method="POST",
                    path="/",
                )
            ]
        )

    def trap_response(
        self,
        event: dict,
        status: str,
        failure_reason: str | None = None,
        failure_traceback: str | None = None,
        response_id: str | None = None,
    ):
        """
        Trap an event response to store it in the database

        Keyword Arguments:
            event: The originating event
            status: The status of the response
            failure_reason: The reason for the failure
            failure_traceback: The traceback of the failure
        """
        response_retention = setting_value(
            "da_vinci_framework::event_bus", "response_retention_hours"
        )

        if response_id:
            response = self.event_responses.get(
                event_type=event["event_type"], response_id=response_id
            )

            if response:
                response.response_status = status  # type: ignore[attr-defined]

                response.failure_reason = failure_reason  # type: ignore[attr-defined]

                response.failure_traceback = failure_traceback  # type: ignore[attr-defined]

                self.event_responses.put(response)

                return self.respond(
                    body={"message": "response updated"},
                    status_code=200,
                )

        response = EventBusResponse(
            event_type=event["event_type"],
            failure_reason=failure_reason,
            failure_traceback=failure_traceback,
            original_event_body=event,
            originating_event_id=event["event_id"],
            response_id=event.get("response_id"),
            response_status=status,
            time_to_live=datetime.now(tz=UTC) + timedelta(hours=response_retention),
        )

        self.event_responses.put(response)

        return self.respond(
            body={"message": "response saved"},
            status_code=201,
        )


def api(event: dict, context: dict):
    """
    API handler for the event bus watcher

    Keyword Arguments:
        event: The event
        context: The context
    """
    logging.debug(f"Event: {event}")

    watcher = EventBusWatcher()

    return watcher.handle(event=event)
