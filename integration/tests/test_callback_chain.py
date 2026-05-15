"""pytest-bdd step definitions for features/callback_chain.feature."""

from __future__ import annotations

from lib import events, responses, tables, waiters
from pytest_bdd import parsers, scenarios, then, when

scenarios("../features/callback_chain.feature")

PEOPLE_TABLE = "people"


@when(
    parsers.parse(
        'I publish an "{event_type}" event with marker "{marker}" and callback "{callback}"'
    )
)
def publish_chain_event(
    ctx, scenario_state: dict, event_type: str, marker: str, callback: str
) -> None:
    event_id = events.publish(
        ctx,
        event_type=event_type,
        body={"marker": marker},
        callback_event_type=callback,
    )

    scenario_state["event_type"] = event_type

    scenario_state["event_id"] = event_id

    scenario_state["marker"] = marker


@then(parsers.parse('the event response status is exactly "{status}"'))
def check_response_status(ctx, scenario_state: dict, status: str) -> None:
    item = responses.wait_for_response(
        ctx,
        event_type=scenario_state["event_type"],
        event_id=scenario_state["event_id"],
    )

    scenario_state["response_item"] = item

    assert (
        item["ResponseStatus"] == status
    ), f"Expected ResponseStatus {status!r}, got {item.get('ResponseStatus')!r}"


@then(
    parsers.parse(
        'within {timeout:d} seconds a PersonTable row with person_id "{person_id}" exists'
    )
)
def wait_for_person_row(ctx, scenario_state: dict, timeout: int, person_id: str) -> None:
    row = waiters.poll_until(
        lambda: tables.get_item(
            ctx,
            logical_table_name=PEOPLE_TABLE,
            key={"PersonId": person_id},
        ),
        timeout=timeout,
        description=f"PersonTable row {person_id!r}",
    )

    scenario_state["person_row"] = row


@then(parsers.parse("the PersonTable row tags equal {expected}"))
def check_tags(scenario_state: dict, expected: str) -> None:
    import json

    expected_list = json.loads(expected)

    actual = scenario_state["person_row"].get("Tags")

    assert list(actual) == expected_list, f"Expected Tags {expected_list!r}, got {actual!r}"
