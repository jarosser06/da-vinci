"""Publish events to a deployed application's event bus.

Uses the framework's own ``AsyncClientBase`` so the published message is
byte-for-byte what application code would send: it discovers the event-bus
SQS queue via the deployed SSM service-discovery parameters and serializes the
:class:`~da_vinci.event_bus.event.Event` with the framework encoder.
"""

from __future__ import annotations

import json

from lib.context import Context

from da_vinci.core.client_base import AsyncClientBase
from da_vinci.core.json import DaVinciObjectEncoder
from da_vinci.event_bus.event import Event


def publish(
    ctx: Context,
    event_type: str,
    body: dict,
    callback_event_type: str | None = None,
) -> str:
    """Publish an event to the deployed bus and return its ``event_id``.

    Keyword Arguments:
        ctx: The deployed application to publish into.
        event_type: The event type subscribers are registered against.
        body: The event body payload.
        callback_event_type: Optional follow-up event type for callback chains.

    Returns:
        The ``event_id`` assigned to the published event, used by the read-side
        helpers to correlate the resulting response/exception rows.
    """
    event = Event(
        body=body,
        event_type=event_type,
        callback_event_type=callback_event_type,
    )

    publisher = AsyncClientBase(
        resource_name="event_bus",
        app_name=ctx.app_name,
        deployment_id=ctx.deployment_id,
        resource_discovery_storage=ctx.resource_discovery_storage,
    )

    publisher.publish(
        body=json.dumps(event.to_dict(), cls=DaVinciObjectEncoder),
    )

    return event.event_id
