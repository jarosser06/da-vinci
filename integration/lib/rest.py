"""SigV4-signed calls to a deployed SimpleRESTService.

Reuses the framework's ``RESTClientBase`` so endpoint discovery and request
signing are identical to how application clients reach the service. The
Function URL is IAM-authenticated, so botocore signs each request with the
caller's ambient AWS credentials.
"""

from __future__ import annotations

from typing import Any

from lib.context import Context

from da_vinci.core.client_base import RESTClientBase


def invoke(
    ctx: Context,
    service_name: str,
    method: str,
    path: str,
    body: dict | None = None,
) -> tuple[int, Any]:
    """Call ``method path`` on the named REST service and return (status, body).

    Keyword Arguments:
        ctx: The deployed application owning the service.
        service_name: The ``service_name`` the SimpleRESTService registered.
        method: ``GET`` or ``POST``.
        path: Request path, including any query string.
        body: JSON body for ``POST`` requests.

    Returns:
        A ``(status_code, parsed_body)`` tuple. ``parsed_body`` is the decoded
        JSON for 2xx responses, or the raw bytes/None otherwise.
    """
    client = RESTClientBase(
        resource_name=service_name,
        app_name=ctx.app_name,
        deployment_id=ctx.deployment_id,
        resource_discovery_storage=ctx.resource_discovery_storage,
        raise_on_failure=False,
    )

    upper = method.upper()

    if upper == "GET":
        response = client.get(path=path)
    elif upper == "POST":
        response = client.post(body=body or {}, path=path)
    else:
        raise ValueError(f"Unsupported method for integration REST helper: {method!r}")

    return response.status_code, response.response_body
