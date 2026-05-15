"""pytest-bdd step definitions for features/event_bus.feature."""

from __future__ import annotations

from lib import events, exceptions, responses
from pytest_bdd import parsers, scenarios, then, when

scenarios("../features/event_bus.feature")


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


@then("the response has no failure_reason")
def check_no_failure_reason(scenario_state: dict) -> None:
    item = scenario_state["response_item"]

    # Framework ORM may serialize Python None as the literal string "None".
    assert item.get("FailureReason") in (
        None,
        "",
        "None",
    ), f"Expected FailureReason absent, got {item.get('FailureReason')!r}"


@then("the response has no failure_traceback")
def check_no_failure_traceback(scenario_state: dict) -> None:
    item = scenario_state["response_item"]

    assert item.get("FailureTraceback") in (
        None,
        "",
        "None",
    ), f"Expected FailureTraceback absent, got {item.get('FailureTraceback')!r}"


@then(parsers.parse('no TrappedException is recorded for "{logical_name}"'))
def check_no_trapped_exception(ctx, logical_name: str) -> None:
    # The framework records the explicit ``function_name`` passed to
    # ``@fn_event_response``, not the fully-prefixed Lambda function name.
    exceptions.assert_no_trapped(ctx, function_name=logical_name)
