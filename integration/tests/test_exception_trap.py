"""pytest-bdd step definitions for features/exception_trap.feature."""

from __future__ import annotations

from lib import events, exceptions, responses
from pytest_bdd import parsers, scenarios, then, when

scenarios("../features/exception_trap.feature")


@when(parsers.parse('I publish an "{event_type}" event with marker "{marker}"'))
def publish_event(ctx, scenario_state: dict, event_type: str, marker: str) -> None:
    event_id = events.publish(ctx, event_type=event_type, body={"marker": marker})

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


@then(parsers.parse('the response failure_reason equals "{reason}"'))
def check_failure_reason(scenario_state: dict, reason: str) -> None:
    item = scenario_state["response_item"]

    assert (
        item.get("FailureReason") == reason
    ), f"Expected FailureReason {reason!r}, got {item.get('FailureReason')!r}"


@then(parsers.parse('a TrappedException is recorded for "{logical_name}"'))
def check_trapped(ctx, scenario_state: dict, logical_name: str) -> None:
    # Framework records the explicit ``function_name`` from
    # ``@fn_event_response``, not the prefixed Lambda function name.
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
