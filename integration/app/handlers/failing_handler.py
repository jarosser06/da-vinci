"""Deliberately failing handler for the exception-trap integration scenario.

Subscribes to ``it.boom``. Raises ``RuntimeError("intentional boom: <marker>")``
where ``marker`` comes from the incoming event body. The framework wrapper
must:
  * record a FAILURE row in EventBusResponses with the exact failure_reason
  * record a TrappedException row whose ``exception`` field equals the message
"""

from da_vinci.event_bus.client import fn_event_response
from da_vinci.exception_trap.client import ExceptionReporter


@fn_event_response(
    function_name="failing_handler",
    exception_reporter=ExceptionReporter(),
    re_raise=False,
)
def handler(event: dict, context: object) -> None:
    body = event.get("body") or {}

    marker = body.get("marker", "UNSET")

    raise RuntimeError(f"intentional boom: {marker}")
