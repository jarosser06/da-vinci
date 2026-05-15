"""Polling helper for the eventually-consistent AWS resources under test.

Event delivery, response recording, and exception trapping all happen
asynchronously after a publish. Steps that assert on those side effects poll
until the expected state appears or a timeout elapses.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

DEFAULT_INTERVAL_SECONDS = 3.0


def poll_until(
    fn: Callable[[], T | None],
    timeout: int | float,
    description: str,
    interval: float = DEFAULT_INTERVAL_SECONDS,
) -> T:
    """Call ``fn`` until it returns a truthy value or ``timeout`` elapses.

    Keyword Arguments:
        fn: Zero-arg callable; a falsy/``None`` result means "not ready yet".
        timeout: Maximum seconds to wait.
        description: Human-readable subject, used in the timeout message.
        interval: Seconds to sleep between attempts.

    Returns:
        The first truthy value returned by ``fn``.

    Raises:
        AssertionError: If ``timeout`` elapses without a truthy result.
    """
    deadline = time.monotonic() + timeout

    while True:
        result = fn()

        if result:
            return result

        if time.monotonic() >= deadline:
            raise AssertionError(f"Timed out after {timeout}s waiting for {description}")

        time.sleep(interval)
