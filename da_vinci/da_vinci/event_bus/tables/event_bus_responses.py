'''Event Bus  Responses Table'''

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from da_vinci.core.orm import (
    TableClient,
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
    TableScanDefinition,
)
from da_vinci.core.orm.table_object import TableObject


def _execute_on_update(table_object: 'EventBusResponse'):
    """
    Execute on update hook for the Event Bus  Response object.

    Keyword Arguments:
        table_object: The table object to update
    """
    if table_object.response_status == 'FAILURE':
        table_object.time_to_live = datetime.utcnow() + timedelta(days=2)


class EventBusResponse(TableObject):
    description = 'Event Bus  Responses'
    execute_on_update = _execute_on_update
    table_name = 'event_bus_responses'

    partition_key_attribute = TableObjectAttribute(
        'event_type',
        TableObjectAttributeType.STRING,
        description='The event type that was subscribed to',
    )

    sort_key_attribute = TableObjectAttribute(
        'response_id',
        TableObjectAttributeType.STRING,
        default=lambda: str(uuid4()),
        description='The unique ID of the response',
    )

    attributes = [
        TableObjectAttribute(
            'created',
            TableObjectAttributeType.DATETIME,
            default=lambda: datetime.utcnow(),
            description='The datetime the response was created',
        ),

        TableObjectAttribute(
            'failure_reason',
            TableObjectAttributeType.STRING,
            description='The reason for the failure',
        ),

        TableObjectAttribute(
            'failure_traceback',
            TableObjectAttributeType.STRING,
            description='The traceback of the failure',
        ),

        TableObjectAttribute(
            'originating_event_id',
            TableObjectAttributeType.STRING,
            description='The ID of the event that triggered the response',
        ),

        TableObjectAttribute(
            'original_event_body',
            TableObjectAttributeType.JSON,
            description='The original event body',
        ),

        TableObjectAttribute(
            'response_status',
            TableObjectAttributeType.STRING,
            description='The status of the response, either "SUCCESS", "FAILURE", or "NO_ROUTE"',
        ),

        TableObjectAttribute(
            'time_to_live',
            TableObjectAttributeType.DATETIME,
            default=lambda: datetime.utcnow() + timedelta(hours=4),
            description='The time to live for the table object',
        )
    ]


class EventBusResponsesScanDefinition(TableScanDefinition):
    def __init__(self):
        super().__init__(
            table_object_class=EventBusResponse,
        )


class EventBusResponses(TableClient):
    def __init__(self, app_name: Optional[str] = None, deployment_id: Optional[str] = None):
        super().__init__(
            app_name=app_name,
            deployment_id=deployment_id,
            default_object_class=EventBusResponse,
        )

    def delete(self, EventResponse: EventBusResponse):
        """
        Delete an event bus subscription response

        Keyword Arguments:
            EventResponse: The event bus subscription response to delete
        """
        self.remove_object(EventResponse)

    def get(self, event_type: str, response_id: str) -> EventBusResponse:
        """
        Get an event bus subscription response

        Keyword Arguments:
            event_type: The event type of the response
            response_id: The response ID

        Returns:
            EventBusResponse
        """

        return self.get_object(
            partition_key=event_type,
            sort_key=response_id,
        )

    def put(self, event_bus_subscription_response: EventBusResponse):
        """
        Put an event bus subscription response

        Keyword Arguments:
            event_bus_subscription_response: The event bus subscription response to put
        """
        return self.put_object(event_bus_subscription_response)

    def scan(self, scan_definition: EventBusResponsesScanDefinition) -> List[EventBusResponse]:
        """
        Scan event bus subscription responses

        Keyword Arguments:
            scan_definition: The scan definition

        Returns:
            List of EventBusResponse
        """
        return self.full_scan(scan_definition=scan_definition)