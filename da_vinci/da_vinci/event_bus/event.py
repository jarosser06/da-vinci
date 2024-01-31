'''Event Bus Primitives'''
import json
import uuid

from datetime import datetime
from typing import Dict, Optional, Union

from da_vinci.core.json import DateTimeEncoder
from da_vinci.event_bus.object import ObjectBody


class Event:
    def __init__(self, body: Union[ObjectBody, Dict, str], event_type: str,
                 created: Optional[datetime] = None, event_id: str = None,
                 previous_event_id: Optional[str] = None):
        """
        Event is a class that represents an event that is published to
        the event bus.

        Keyword Arguments:
            body: Body of the event
            event_type: Type of the event
            created: When the event was created
            event_id: Unique identifier for the event
            previous_event_id: Unique identifier for the previous event
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
        self.previous_event_id = previous_event_id

        if created:
            self.created = created
        else:
            self.created = datetime.utcnow()

    @staticmethod
    def from_lambda_event(event: Dict) -> 'Event':
        """
        Create a Event from a Lambda event

        Keyword Arguments:
            event: Lambda event

        Returns:
            Event
        """

        body = event['body']

        if isinstance(body, str):
            body = json.loads(body)
        else:
            body = body

        return Event(**body)

    def next_event(self, event_type: str, body: Union[Dict, str]) -> 'Event':
        """
        Create a new event that is linked to this event

        Keyword Arguments:
            event_type: Type of the event
            body: Body of the event

        Returns:
            New Event
        """

        return Event(body=body, event_type=event_type,
                     previous_event_id=self.event_id)

    def to_dict(self) -> Dict:
        """
        Convert the event to a dictionary
        """

        return {
            'body': self.body,
            'created': self.created,
            'event_id': self.event_id,
            'event_type': self.event_type,
            'previous_event_id': self.previous_event_id,
        }

    def to_json(self) -> str:
        """
        Convert the event to a JSON string
        """

        return json.dumps(self.to_dict(), cls=DateTimeEncoder)