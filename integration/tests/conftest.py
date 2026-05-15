"""pytest-bdd shared step definitions for the integration suite."""

from __future__ import annotations

import pytest
from lib.deployment import Deployment
from pytest_bdd import given


@pytest.fixture
def scenario_state() -> dict:
    """Per-scenario mutable bag passed between steps."""
    return {}


@given("a deployed Da Vinci application", target_fixture="ctx")
def a_deployed_da_vinci_application(deployment: Deployment):
    return deployment.context


@given("a deployed Da Vinci sidecar application", target_fixture="sidecar_ctx")
def a_deployed_da_vinci_sidecar_application(deployment: Deployment):
    return deployment.sidecar_context
