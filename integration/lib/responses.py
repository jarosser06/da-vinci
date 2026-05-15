"""Read EventBusResponses rows written by the framework's handler wrapper.

When ``fn_event_response`` finishes (success or failure) it records a row in
the ``da_vinci_event_bus_responses`` table keyed by ``event_type`` (partition)
and a generated ``response_id`` (sort). The originating event's id is stored in
the ``OriginatingEventId`` column, so we locate a published event's response by
querying the partition and filtering on that column.
"""

from __future__ import annotations

from typing import Any

from lib import aws, waiters
from lib.context import Context

RESPONSES_TABLE = "da_vinci_event_bus_responses"

DEFAULT_TIMEOUT_SECONDS = 120

# A handler's row is first written as INITIALIZED (and may pass through ROUTED)
# before the wrapper records the outcome. Only these statuses are terminal, so
# the suite must wait for one of them rather than returning the in-flight row.
TERMINAL_STATUSES = frozenset({"SUCCESS", "FAILURE", "NO_ROUTE", "NO_SUBSCRIPTIONS"})


def find_response(
    ctx: Context,
    event_type: str,
    event_id: str,
) -> dict[str, Any] | None:
    """Return the terminal response row for ``event_id``, or ``None`` if not ready.

    Filters by ``OriginatingEventId`` to correlate with the published event and
    only returns once the row has reached a terminal ``ResponseStatus`` — an
    in-flight ``INITIALIZED``/``ROUTED`` row counts as "not ready yet".
    """
    items = aws.query_partition(
        ctx,
        logical_table_name=RESPONSES_TABLE,
        partition_key_name="EventType",
        partition_key_value=event_type,
    )

    for item in items:
        if (
            item.get("OriginatingEventId") == event_id
            and item.get("ResponseStatus") in TERMINAL_STATUSES
        ):
            return item

    return None


def wait_for_response(
    ctx: Context,
    event_type: str,
    event_id: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Block until the response row for ``event_id`` appears and return it."""
    return waiters.poll_until(
        lambda: find_response(ctx, event_type=event_type, event_id=event_id),
        timeout=timeout,
        description=(f"EventBusResponses row for event_type={event_type!r} event_id={event_id!r}"),
    )
