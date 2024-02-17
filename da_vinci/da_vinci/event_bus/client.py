'''Event Bus Clients'''

import json
import logging
import traceback

from dataclasses import asdict, dataclass
from enum import auto, StrEnum
from functools import wraps
from typing import Dict, Optional, Union

from da_vinci.core.client_base import AsyncClientBase, RESTClientBase
from da_vinci.core.json import DateTimeEncoder
from da_vinci.event_bus.event import Event


LOG = logging.getLogger(__name__)


class EventPublisher(AsyncClientBase):
    def __init__(self):
        super().__init__(resource_name='event_bus')

    def submit(self, event: Event, delay: Optional[int] = None):
        """
        Publish an event to the event bus

        Keyword Arguments:
            event: Event to publish
        """
        _delay = delay or 0

        self.publish(body=event.to_json(), delay=_delay)


class EventResponseStatus(StrEnum):
    FAILURE = auto()
    NO_ROUTE = auto()
    SUCCESS = auto()


@dataclass
class EventResponse:
    """
    EventResponse is a dataclass that represents the response from an event
    handler.
    """
    event: Event
    status: EventResponseStatus
    failure_reason: Optional[str] = None
    failure_traceback: Optional[str] = None

    def to_dict(self) -> Dict:
        """
        Create a dictionary representation of the EventResponse

        Returns:
            Dict
        """

        return asdict(self)

    def to_json(self) -> str:
        """
        Create a JSON representation of the EventResponse

        Returns:
            str
        """

        return json.dumps(self.to_dict(), cls=DateTimeEncoder)


class EventResponder(RESTClientBase):
    def __init__(self):
        super().__init__(resource_name='event_bus_responses')

    def response(self, event: Union[Event, Dict], status: Union[EventResponseStatus, str],
                 failure_reason: Optional[str] = None,
                 failure_traceback: Optional[str] = None):
        """
        Publish an EventResponse

        Keyword Arguments:
            event: Event to respond to
            status: Status of the response
            failure_reason: Reason for failure (if applicable)
        """

        if isinstance(event, Event):
            event = event.to_dict()

        response_body = EventResponse(
            event=event,
            status=status,
            failure_reason=failure_reason,
            failure_traceback=failure_traceback,
        )

        self.post(body=response_body)


def fn_event_response(func):
    """Wraps a function that handles an event and returns an EventResponse"""
    @wraps(func)
    def wrapper(event: Dict, context: Dict):
        LOG.debug(f'Got event: {event}')

        event_responder = EventResponder()

        event_obj = Event.from_lambda_event(event=event)

        try:
            func(event, context)

            event_responder.response(event=event_obj,
                                     status=EventResponseStatus.SUCCESS)

        except Exception as exc:
            event_responder.response(event=event_obj,
                                     status=EventResponseStatus.FAILURE, 
                                     failure_reason=str(exc),
                                     failure_traceback=traceback.format_exc())

            traceback.print_exc()
    return wrapper