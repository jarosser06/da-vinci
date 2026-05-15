"""Sidecar event handler.

Subscribes to ``it.sidecar.ping`` (published by the test). Calls into the
parent application's exception_trap REST service via the shared
ExceptionReporter to prove the sidecar can reach parent-owned resources via
the shared service discovery store. Returns a body that the framework records
as the SUCCESS response.
"""

from da_vinci.event_bus.client import fn_event_response
from da_vinci.exception_trap.client import ExceptionReporter


@fn_event_response(
    function_name="sidecar_echo",
    exception_reporter=ExceptionReporter(),
    re_raise=False,
)
def handler(event: dict, context: object) -> dict:
    del context

    body = event.get("body") or {}

    return {"sidecar_ack": body.get("marker")}
