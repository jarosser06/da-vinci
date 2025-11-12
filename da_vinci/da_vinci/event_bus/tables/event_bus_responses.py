"""Event Bus  Responses Table"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from da_vinci.core.orm.client import (
    TableClient,
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
    TableScanDefinition,
)


class EventBusResponse(TableObject):
    description = "Event Bus Responses"

    table_name = "da_vinci_event_bus_responses"

    partition_key_attribute = TableObjectAttribute(
        "event_type",
        TableObjectAttributeType.STRING,
        description="The event type that was subscribed to",
    )

    sort_key_attribute = TableObjectAttribute(
        "response_id",
        TableObjectAttributeType.STRING,
        default=lambda: str(uuid4()),
        description="The unique ID of the response",
    )

    ttl_attribute = TableObjectAttribute(
        "time_to_live",
        TableObjectAttributeType.DATETIME,
        default=lambda: datetime.now(tz=UTC) + timedelta(hours=8),
        description="The time to live for the table object",
    )

    attributes = [
        TableObjectAttribute(
            "created",
            TableObjectAttributeType.DATETIME,
            default=lambda: datetime.now(tz=UTC),
            description="The datetime the response was created",
        ),
        TableObjectAttribute(
            "failure_reason",
            TableObjectAttributeType.STRING,
            description="The reason for the failure",
            optional=True,
        ),
        TableObjectAttribute(
            "failure_traceback",
            TableObjectAttributeType.STRING,
            description="The traceback of the failure",
            optional=True,
        ),
        TableObjectAttribute(
            "originating_event_id",
            TableObjectAttributeType.STRING,
            description="The ID of the event that triggered the response",
        ),
        TableObjectAttribute(
            "original_event_body",
            TableObjectAttributeType.JSON_STRING,
            description="The original event body",
        ),
        TableObjectAttribute(
            "response_status",
            TableObjectAttributeType.STRING,
            description='The status of the response, either "SUCCESS", "FAILURE", "ROUTED", or "NO_ROUTE"',
        ),
    ]

    def __init__(
        self,
        event_type: str,
        response_id: str,
        response_status: str,
        original_event_body: dict,
        originating_event_id: str,
        created: datetime | None = None,
        failure_reason: str | None = None,
        failure_traceback: str | None = None,
        time_to_live: datetime | None = None,
    ):
        """
        Initialize an event bus response object

        Keyword Arguments:
            event_type: The event type that was subscribed to
            response_id: The unique ID of the response
            response_status: The status of the response, either "SUCCESS", "FAILURE", or "NO_ROUTE"
            original_event_body: The original event body
            originating_event_id: The ID of the event that triggered the response
            created: The datetime the response was created
            failure_reason: The reason for the failure
            failure_traceback: The traceback of the failure
            time_to_live: The time to live for the table object
        """
        super().__init__(
            created=created,
            event_type=event_type,
            original_event_body=original_event_body,
            originating_event_id=originating_event_id,
            failure_reason=failure_reason,
            failure_traceback=failure_traceback,
            response_id=response_id,
            response_status=response_status,
            time_to_live=time_to_live,
        )


class EventBusResponsesScanDefinition(TableScanDefinition):
    def __init__(self):
        super().__init__(
            table_object_class=EventBusResponse,
        )


class EventBusResponses(TableClient):
    def __init__(self, app_name: str | None = None, deployment_id: str | None = None):
        super().__init__(
            app_name=app_name,
            deployment_id=deployment_id,
            default_object_class=EventBusResponse,
        )

    def delete(self, event_response: EventBusResponse):
        """
        Delete an event bus subscription response

        Keyword Arguments:
            event_response: The event bus subscription response to delete
        """
        self.delete_object(event_response)

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
            partition_key_value=event_type,
            sort_key_value=response_id,
        )

    def put(self, event_bus_subscription_response: EventBusResponse):
        """
        Put an event bus subscription response

        Keyword Arguments:
            event_bus_subscription_response: The event bus subscription response to put
        """
        return self.put_object(event_bus_subscription_response)

    def scan(self, scan_definition: EventBusResponsesScanDefinition) -> list[EventBusResponse]:
        """
        Scan event bus subscription responses

        Keyword Arguments:
            scan_definition: The scan definition

        Returns:
            List of EventBusResponse
        """
        return self.full_scan(scan_definition=scan_definition)
