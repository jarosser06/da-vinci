"""Root conftest for the integration test suite.

Defines CLI flags (``--keep`` / ``--reuse`` / ``--region``) and the session-
scoped ``deployment`` fixture that drives ``cdk deploy`` / ``cdk destroy``
around the test run.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from lib.deployment import Deployment


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--keep",
        action="store_true",
        default=False,
        help="Skip cdk destroy after the test session (for troubleshooting).",
    )
    parser.addoption(
        "--reuse",
        action="store_true",
        default=False,
        help=(
            "Skip cdk deploy; reuse an existing deployment identified by DA_VINCI_IT_INSTALL_ID."
        ),
    )
    parser.addoption(
        "--region",
        default=None,
        help="AWS region to deploy into (default: $AWS_REGION or us-east-1).",
    )


@pytest.fixture(scope="session")
def deployment(pytestconfig: pytest.Config) -> Iterator[Deployment]:
    """Deploy the integration app + sidecar for the session, then tear down."""
    keep = bool(pytestconfig.getoption("--keep"))

    reuse = bool(pytestconfig.getoption("--reuse"))

    region = pytestconfig.getoption("--region") or os.getenv("AWS_REGION")

    install_id = os.environ.get("DA_VINCI_IT_INSTALL_ID")

    dep = Deployment(
        install_id=install_id,
        region=region,
        keep=keep,
        reuse=reuse,
    )

    # Make the chosen install id discoverable to the caller and to nested
    # subprocesses (e.g. a follow-up ``--reuse`` run).
    os.environ["DA_VINCI_IT_INSTALL_ID"] = dep.install_id

    dep.deploy()

    try:
        yield dep
    finally:
        dep.destroy()
