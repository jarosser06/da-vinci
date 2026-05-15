"""Second handler in the callback chain.

Subscribes to ``it.chain.end``. When invoked it writes a row to PersonTable
with ``person_id`` equal to the marker carried through the chain — this row
is what the test asserts against to prove the chain executed end-to-end.
"""

from handlers.shared.person import PersonTableClient, PersonTableObject

from da_vinci.event_bus.client import fn_event_response
from da_vinci.exception_trap.client import ExceptionReporter


@fn_event_response(
    function_name="chain_second",
    exception_reporter=ExceptionReporter(),
    re_raise=False,
)
def handler(event: dict, context: object) -> dict:
    body = event.get("body") or {}

    marker = body.get("marker")

    previous_event_id = event.get("previous_event_id")

    people = PersonTableClient()

    # ``age`` is given a non-None value because the framework's ORM
    # serializes optional NUMBER attributes as the literal None — which
    # DynamoDB rejects with "cannot be converted to a numeric value".
    person = PersonTableObject(
        person_id=marker,
        name=f"chained-{marker}",
        age=0,
        tags=["chain", "second"],
    )

    people.put(person)

    return {
        "step": "second",
        "marker": marker,
        "previous_event_id": previous_event_id,
    }
