"""pytest-bdd step definitions for features/rest_service_orm.feature."""

from __future__ import annotations

import json

from lib import rest
from pytest_bdd import parsers, scenarios, then, when

scenarios("../features/rest_service_orm.feature")

SERVICE_NAME = "it_people"


@when(parsers.parse('I POST to /people with name "{name}" age {age:d}'))
def post_person(ctx, scenario_state: dict, name: str, age: int) -> None:
    status, body = rest.invoke(
        ctx,
        service_name=SERVICE_NAME,
        method="POST",
        path="/people",
        body={"name": name, "age": age},
    )

    scenario_state["rest_status"] = status

    scenario_state["rest_body"] = body


@when(parsers.parse('I GET person "{person_id}"'))
def get_missing_person(ctx, scenario_state: dict, person_id: str) -> None:
    status, body = rest.invoke(
        ctx,
        service_name=SERVICE_NAME,
        method="GET",
        path=f"/people/get?person_id={person_id}",
    )

    scenario_state["rest_status"] = status

    scenario_state["rest_body"] = body


@when("I GET the greeting setting")
def get_greeting(ctx, scenario_state: dict) -> None:
    status, body = rest.invoke(
        ctx,
        service_name=SERVICE_NAME,
        method="GET",
        path="/settings/greeting",
    )

    scenario_state["rest_status"] = status

    scenario_state["rest_body"] = body


@then(parsers.parse("the REST response status is exactly {status:d}"))
def check_rest_status(scenario_state: dict, status: int) -> None:
    actual = scenario_state["rest_status"]

    assert actual == status, f"Expected status {status}, got {actual}"


@then(parsers.parse('the REST response body has a "{field}"'))
def check_body_field_present(scenario_state: dict, field: str) -> None:
    body = scenario_state["rest_body"]

    assert isinstance(body, dict), f"Expected dict body, got {type(body).__name__}"

    inner = body.get("body") if "body" in body else body

    if isinstance(inner, str):
        inner = json.loads(inner)

    assert (
        field in inner and inner[field]
    ), f"Expected response body to contain non-empty {field!r}, got {inner!r}"


@then(parsers.parse("the REST response body equals {expected}"))
def check_body_equals(scenario_state: dict, expected: str) -> None:
    expected_obj = json.loads(expected)

    body = scenario_state["rest_body"]

    inner = body.get("body") if isinstance(body, dict) and "body" in body else body

    if isinstance(inner, str):
        inner = json.loads(inner)

    assert inner == expected_obj, f"Expected body {expected_obj!r}, got {inner!r}"
