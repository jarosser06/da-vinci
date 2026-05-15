"""Sidecar handler that writes to the PARENT application's ORM table.

Subscribes to ``it.sidecar.write`` and writes a row to the parent's ``people``
table — a resource the sidecar does not own. This exercises the full
cross-application path: a ResourceAccessRequest (declared in the stack) grants
the sidecar Lambda IAM access to the parent table, and resource discovery
resolves the parent's physical table name at runtime.
"""

from handlers.shared.person import PersonTableClient, PersonTableObject

from da_vinci.event_bus.client import fn_event_response
from da_vinci.exception_trap.client import ExceptionReporter


@fn_event_response(
    function_name="sidecar_writer",
    exception_reporter=ExceptionReporter(),
    re_raise=False,
)
def handler(event: dict, context: object) -> dict:
    del context

    body = event.get("body") or {}

    marker = body.get("marker")

    people = PersonTableClient()

    # age is set to a concrete value because the framework's ORM rejects a
    # None NUMBER attribute when writing to DynamoDB.
    person = PersonTableObject(
        person_id=marker,
        name=f"sidecar-{marker}",
        age=0,
        tags=["sidecar", "write"],
    )

    people.put(person)

    return {"written_person_id": marker}
