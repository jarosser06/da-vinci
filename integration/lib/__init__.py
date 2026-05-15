"""Validation library for the da_vinci real-AWS integration suite.

Each module wraps one concern the pytest-bdd step definitions drive:

* :mod:`lib.deployment` — ``cdk deploy`` / ``cdk destroy`` lifecycle.
* :mod:`lib.events`     — publish events to a deployed application's bus.
* :mod:`lib.responses`  — read EventBusResponses rows written by handlers.
* :mod:`lib.exceptions` — read TrappedException rows written by the trap.
* :mod:`lib.rest`       — SigV4-signed calls to a deployed REST service.
* :mod:`lib.tables`     — read arbitrary ORM-backed DynamoDB tables.
* :mod:`lib.waiters`    — generic poll-until helper for eventual consistency.

Reads go straight to the deployed AWS resources via boto3 (exact validation),
and writes/invocations reuse the ``da_vinci`` core clients so the suite drives
the framework exactly the way application code does.
"""

from lib.context import Context

__all__ = ["Context"]
