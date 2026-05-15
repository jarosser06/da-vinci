"""Deliberately failing sidecar handler.

Subscribes to ``it.sidecar.boom`` and raises. Proves that a sidecar handler's
exception is routed to the PARENT application's shared exception trap (the
sidecar does not own a trap), recording an exact TrappedException row.
"""

from da_vinci.event_bus.client import fn_event_response
from da_vinci.exception_trap.client import ExceptionReporter


@fn_event_response(
    function_name="sidecar_boom",
    exception_reporter=ExceptionReporter(),
    re_raise=False,
)
def handler(event: dict, context: object) -> None:
    del context

    body = event.get("body") or {}

    marker = body.get("marker", "UNSET")

    raise RuntimeError(f"sidecar boom: {marker}")
