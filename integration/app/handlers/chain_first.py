"""First handler in a callback chain.

Subscribes to ``it.chain.start`` and returns a body that the framework
forwards to ``it.chain.end`` because ``handle_callbacks=True``. The published
chained event will carry ``previous_event_id`` linking it back to the
originating event.
"""

from da_vinci.event_bus.client import fn_event_response
from da_vinci.exception_trap.client import ExceptionReporter


@fn_event_response(
    function_name="chain_first",
    exception_reporter=ExceptionReporter(),
    handle_callbacks=True,
    re_raise=False,
)
def handler(event: dict, context: object) -> dict:
    body = event.get("body") or {}

    return {
        "step": "first",
        "marker": body.get("marker"),
    }
