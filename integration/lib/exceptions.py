"""Read TrappedException rows written by the framework's exception trap.

A failing wrapped handler reports to the trap, which records a row in
``da_vinci_trapped_exceptions`` partitioned by the logical ``function_name``
passed to ``fn_event_response`` (not the prefixed Lambda name). The full
originating event is stored as a JSON string in the ``OriginatingEvent``
column.
"""

from __future__ import annotations

import json
import time
from typing import Any

from lib import aws, waiters
from lib.context import Context

TRAPPED_TABLE = "da_vinci_trapped_exceptions"

DEFAULT_TIMEOUT_SECONDS = 120

# Grace period before asserting that NO exception was trapped: trapping is
# asynchronous, so we must give a would-be failure time to land before
# concluding it never will.
NEGATIVE_SETTLE_SECONDS = 20


def _trapped_rows(ctx: Context, function_name: str) -> list[dict[str, Any]]:
    return aws.query_partition(
        ctx,
        logical_table_name=TRAPPED_TABLE,
        partition_key_name="FunctionName",
        partition_key_value=function_name,
    )


def wait_for_trapped(
    ctx: Context,
    function_name: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Block until a TrappedException for ``function_name`` exists; return the latest."""

    def _latest() -> dict[str, Any] | None:
        rows = _trapped_rows(ctx, function_name)

        if not rows:
            return None

        return max(rows, key=lambda row: str(row.get("Created", "")))

    return waiters.poll_until(
        _latest,
        timeout=timeout,
        description=f"TrappedException row for function_name={function_name!r}",
    )


def assert_no_trapped(
    ctx: Context,
    function_name: str,
    settle: int = NEGATIVE_SETTLE_SECONDS,
) -> None:
    """Assert no TrappedException is recorded for ``function_name``.

    Waits ``settle`` seconds first so an asynchronously-trapped exception has
    time to land before we conclude the trap is empty.
    """
    time.sleep(settle)

    rows = _trapped_rows(ctx, function_name)

    assert rows == [], (
        f"Expected no TrappedException for {function_name!r}, found {len(rows)}: "
        f"{[row.get('Exception') for row in rows]!r}"
    )


def originating_event_body(item: dict[str, Any]) -> dict[str, Any]:
    """Parse the ``OriginatingEvent`` JSON column and return its ``body``."""
    raw = item.get("OriginatingEvent")

    if raw is None:
        raise AssertionError("TrappedException row has no OriginatingEvent column")

    event = json.loads(raw) if isinstance(raw, str) else raw

    return event.get("body") or {}
