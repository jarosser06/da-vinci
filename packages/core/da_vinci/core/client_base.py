"""Base Client Classess"""

import json
from dataclasses import dataclass
from urllib.parse import urljoin

import boto3
import requests  # type: ignore[import-untyped]
from requests_auth_aws_sigv4 import AWSSigV4

from da_vinci.core.json import DaVinciObjectEncoder
from da_vinci.core.resource_discovery import (
    ResourceDiscovery,
    ResourceType,
)


@dataclass
class BaseClient:
    """
    Base client for Da Vinci service clients with automatic resource discovery

    Provides automatic endpoint discovery for AWS resources using the resource
    discovery system. Can be initialized with an explicit endpoint or use
    automatic discovery based on resource name and type.

    Keyword Arguments:
    resource_name -- Name of the resource to connect to
    resource_type -- Type of resource (e.g., REST_SERVICE, ASYNC_SERVICE)
    endpoint -- Explicit endpoint URL (optional, will be discovered if not provided)
    app_name -- Application name for resource discovery (optional)
    deployment_id -- Deployment identifier for resource discovery (optional)
    resource_discovery_storage -- Storage solution for resource discovery (optional)
    """

    resource_name: str
    resource_type: str
    endpoint: str | None = None
    app_name: str | None = None
    deployment_id: str | None = None
    resource_discovery_storage: str | None = None

    def __post_init__(self) -> None:
        """
        Initialize the client and discover endpoint if not explicitly provided

        Uses the resource discovery system to automatically locate the endpoint
        for the specified resource if an explicit endpoint was not provided.
        """
        if self.endpoint:
            return

        from da_vinci.core.resource_discovery import ResourceDiscoveryStorageSolution

        storage_solution = None
        if self.resource_discovery_storage:
            storage_solution = ResourceDiscoveryStorageSolution(self.resource_discovery_storage)

        resource_discovery = ResourceDiscovery(
            resource_type=self.resource_type,
            resource_name=self.resource_name,
            app_name=self.app_name,
            deployment_id=self.deployment_id,
            storage_solution=storage_solution,
        )

        self.endpoint = resource_discovery.endpoint_lookup()


@dataclass
class AsyncClientBase(BaseClient):
    """
    Base class for asynchronous clients. Natively supports resource discovery for the endpoint
    """

    resource_name: str
    endpoint: str | None = None
    app_name: str | None = None
    deployment_id: str | None = None
    resource_type: str = ResourceType.ASYNC_SERVICE
    resource_discovery_storage: str | None = None

    def __post_init__(self) -> None:
        """
        Initialize the async client and create SQS boto3 client

        Calls parent initialization for endpoint discovery and creates
        a boto3 SQS client for message publishing.
        """
        super().__post_init__()
        self.boto_client = boto3.client("sqs")

    def publish(self, body: dict | str, delay: int = 0) -> None:
        """
        Publish a message to the SQS queue

        Keyword Arguments:
        body -- Message body as dict or string (dict will be JSON-encoded)
        delay -- Delay in seconds before message becomes available (default: 0)

        Raises:
            ValueError -- If endpoint is not set
        """
        formatted_body: str
        if isinstance(body, dict):
            formatted_body = json.dumps(body, cls=DaVinciObjectEncoder)
        else:
            formatted_body = body

        if self.endpoint is None:
            raise ValueError("Endpoint is not set")

        self.boto_client.send_message(
            QueueUrl=self.endpoint,
            MessageBody=formatted_body,
            DelaySeconds=delay,
        )


@dataclass
class RESTClientResponse:
    """
    A response object for the DaVinci REST client. Contains the original requests.Response object,
    the status code, and the response body (if applicable)
    """

    response: requests.Response
    status_code: int
    response_body: dict | str | None = None


@dataclass
class RESTClientBase(BaseClient):
    """
    Base class for REST clients that utilize the AWS SigV4 authentication scheme.
    Natively supports resource discovery for the endpoint with DaVinci.
    """

    resource_name: str
    endpoint: str | None = None
    app_name: str | None = None
    deployment_id: str | None = None
    disable_auth: bool = False
    raise_on_failure: bool = True
    resource_type: str = ResourceType.REST_SERVICE
    resource_discovery_storage: str | None = None

    def __post_init__(self) -> None:
        """
        Initialize the REST client and configure AWS SigV4 authentication

        Calls parent initialization for endpoint discovery and sets up AWS SigV4
        authentication for Lambda function URLs unless authentication is disabled.
        """
        super().__post_init__()

        if self.disable_auth:
            self.aws_auth = None

        else:
            self.aws_auth = AWSSigV4("lambda")

    def _full_url(self, path: str | None = None) -> str:
        """
        Given a path, return the full URL for the API
        """
        if path:
            return urljoin(self.endpoint, path)

        return self.endpoint

    def _response(
        self, response: requests.Response, expect_body: bool = True
    ) -> RESTClientResponse:
        """
        Generate a RESTClientResponse object from a requests.Response object. If expect_body is True,
        the response body will be parsed as JSON and included in the response object.

        If the response status code is not 2xx, an exception will be raised.

        Keyword Arguments:
            response: requests.Response object
            expect_body: Whether or not to expect a response body (default: True)
        """
        if expect_body:
            if response.status_code < 200 or response.status_code >= 300:
                if self.raise_on_failure:
                    raise ValueError(f"Failed to make request: {response.text}")

                else:
                    return RESTClientResponse(
                        response=response,
                        status_code=response.status_code,
                        response_body=response.content,
                    )

            try:
                response_body = response.json()

            except json.JSONDecodeError:
                response_body = None

        else:
            response_body = None

        return RESTClientResponse(
            response=response,
            status_code=response.status_code,
            response_body=response_body,
        )

    def get(
        self, headers: dict | None = None, params: dict | None = None, path: str | None = None
    ) -> RESTClientResponse:
        """
        Perform a GET request

        Keyword Arguments:
            headers: Headers to include in the request
            params: Query parameters to include in the request (default: None)
            path: Path to append to the endpoint (default: None)
        """
        result = requests.request(
            "GET",
            url=self._full_url(path),
            auth=self.aws_auth,
            headers=headers,
            params=params,
        )

        return self._response(result)

    def put(
        self, body: str, headers: dict | None = None, path: str | None = None
    ) -> RESTClientResponse:
        """
        Perform a PUT request

        Keyword Arguments:
            body: Body of the request
            headers: Headers to include in the request
            path: Path to append to the endpoint (default: None)
        """
        result = requests.request(
            "PUT",
            url=self._full_url(path),
            auth=self.aws_auth,
            headers=headers,
            json=body,
        )

        return self._response(result)

    def post(
        self, body: dict, headers: dict | None = None, path: str | None = None
    ) -> RESTClientResponse:
        """
        Perform a POST request

        Keyword Arguments:
            body: Body of the request
            headers: Headers to include in the request
            path: Path to append to the endpoint (default: None)
        """
        result = requests.request(
            "POST",
            url=self._full_url(path),
            auth=self.aws_auth,
            headers=headers,
            json=body,
        )

        return self._response(result)
