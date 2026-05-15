"""Successful event-bus subscriber for the integration suite.

Subscribes to ``it.echo`` and returns ``{"echoed": <body>}``. Used to verify
that the event bus delivers events, that the wrapped handler reports SUCCESS
to EventBusResponses, and that no TrappedException row is produced.
"""

from da_vinci.event_bus.client import fn_event_response
from da_vinci.exception_trap.client import ExceptionReporter


@fn_event_response(
    function_name="successful_handler",
    exception_reporter=ExceptionReporter(),
    re_raise=False,
)
def handler(event: dict, context: object) -> dict:
    body = event.get("body") or {}

    return {"echoed": body}
