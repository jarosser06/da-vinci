"""Event Bus Primitives"""

import json
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from da_vinci.core.immutable_object import ObjectBody


class Event:
    def __init__(
        self,
        body: "ObjectBody | dict | str",
        event_type: str,
        callback_event_type: str | None = None,
        callback_event_type_on_failure: str | None = None,
        created: datetime | None = None,
        event_id: str | None = None,
        previous_event_id: str | None = None,
        response_id: str | None = None,
    ) -> None:
        """
        Event is a class that represents an event that is published to
        the event bus.

        Keyword Arguments:
            body: Body of the event
            event_type: Type of the event
            callback_event_type: An optional event type that results should be sent to
            callback_event_type_on_failure: An optional event type that results should be sent to on failure
            created: When the event was created
            event_id: Unique identifier for the event
            previous_event_id: Unique identifier for the previous event
            response_id: Unique identifier for the response
        """
        if isinstance(body, str):
            self.body = json.loads(body)

        else:
            self.body = body

        if event_id:
            self.event_id = event_id

        else:
            self.event_id = str(uuid.uuid4())

        self.event_type = event_type

        self.callback_event_type = callback_event_type

        self.callback_event_type_on_failure = callback_event_type_on_failure

        self.previous_event_id = previous_event_id

        self.response_id = response_id

        if created:
            self.created = created
        else:
            self.created = datetime.now(tz=UTC)

    @staticmethod
    def from_lambda_event(event: dict) -> "Event":
        """
        Create a Event from a RAW Lambda event

        Keyword Arguments:
            event: Lambda event

        Returns:
            Event
        """

        return Event(**event)

    def next_event(
        self,
        event_type: str,
        body: dict | str,
        callback_event_type: str | None = None,
        callback_event_type_on_failure: str | None = None,
    ) -> "Event":
        """
        Create a new event that is linked to this event

        Keyword Arguments:
            event_type: Type of the event
            body: Body of the event
            callback_event_type: An optional event type that results should be sent to
            callback_event_type_on_failure: An optional event type that results should be sent to on failure

        Returns:
            New Event
        """

        return Event(
            body=body,
            event_type=event_type,
            previous_event_id=self.event_id,
            callback_event_type=callback_event_type,
            callback_event_type_on_failure=callback_event_type_on_failure,
        )

    def to_dict(self) -> dict:
        """
        Convert the event to a dictionary
        """

        return {
            "body": self.body,
            "callback_event_type": self.callback_event_type,
            "callback_event_type_on_failure": self.callback_event_type_on_failure,
            "created": self.created,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "previous_event_id": self.previous_event_id,
            "response_id": self.response_id,
        }
