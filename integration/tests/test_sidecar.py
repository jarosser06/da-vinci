"""pytest-bdd step definitions for features/sidecar.feature."""

from __future__ import annotations

import json

from lib import events, exceptions, responses, tables, waiters
from pytest_bdd import parsers, scenarios, then, when

scenarios("../features/sidecar.feature")

PEOPLE_TABLE = "people"


@when(parsers.parse('I publish an "{event_type}" event with marker "{marker}"'))
def publish_event(ctx, scenario_state: dict, event_type: str, marker: str) -> None:
    # Sidecar subscribes to events on the PARENT bus (ctx is parent's context)
    event_id = events.publish(ctx, event_type=event_type, body={"marker": marker})

    scenario_state["event_type"] = event_type

    scenario_state["event_id"] = event_id


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


@then(parsers.parse('no TrappedException is recorded for "{logical_name}"'))
def check_no_trapped(ctx, logical_name: str) -> None:
    # Sidecar shares the parent application's exception trap. Check the
    # parent's table (``ctx``), and look up by the logical function_name
    # passed to ``@fn_event_response`` (not the fully-prefixed Lambda name).
    exceptions.assert_no_trapped(ctx, function_name=logical_name)


@then(parsers.parse('the response failure_reason equals "{reason}"'))
def check_failure_reason(scenario_state: dict, reason: str) -> None:
    item = scenario_state["response_item"]

    assert (
        item.get("FailureReason") == reason
    ), f"Expected FailureReason {reason!r}, got {item.get('FailureReason')!r}"


@then(parsers.parse('a TrappedException is recorded for "{logical_name}"'))
def check_trapped(ctx, scenario_state: dict, logical_name: str) -> None:
    # The sidecar shares the PARENT's exception trap, so the trapped row lands
    # in the parent's table (``ctx``), keyed by the logical function_name.
    item = exceptions.wait_for_trapped(ctx, function_name=logical_name)

    scenario_state["trapped_item"] = item


@then(parsers.parse('the trapped exception field equals "{value}"'))
def check_trapped_field(scenario_state: dict, value: str) -> None:
    item = scenario_state["trapped_item"]

    assert (
        item["Exception"] == value
    ), f"Expected Exception field {value!r}, got {item.get('Exception')!r}"


@then(parsers.parse('the trapped exception originating event body marker equals "{value}"'))
def check_originating_marker(scenario_state: dict, value: str) -> None:
    item = scenario_state["trapped_item"]

    body = exceptions.originating_event_body(item)

    assert (
        body.get("marker") == value
    ), f"Expected originating body marker {value!r}, got {body.get('marker')!r}"


@then(
    parsers.parse(
        'within {timeout:d} seconds a parent PersonTable row with person_id "{person_id}" exists'
    )
)
def wait_for_parent_person_row(ctx, scenario_state: dict, timeout: int, person_id: str) -> None:
    row = waiters.poll_until(
        lambda: tables.get_item(
            ctx,
            logical_table_name=PEOPLE_TABLE,
            key={"PersonId": person_id},
        ),
        timeout=timeout,
        description=f"parent PersonTable row {person_id!r} written by sidecar",
    )

    scenario_state["person_row"] = row


@then(parsers.parse("the parent PersonTable row tags equal {expected}"))
def check_parent_person_tags(scenario_state: dict, expected: str) -> None:
    expected_list = json.loads(expected)

    actual = scenario_state["person_row"].get("Tags")

    assert list(actual) == expected_list, f"Expected Tags {expected_list!r}, got {actual!r}"
