'''Base Client Classess'''
import json

from dataclasses import dataclass
from urllib.parse import urljoin
from typing import Dict, Optional, Union

import boto3
import requests

from requests_auth_aws_sigv4 import AWSSigV4

from da_vinci.core.resource_discovery import (
    resource_endpoint_lookup,
    ResourceType,
)


@dataclass
class BaseClient:
    resource_name: str
    resource_type: str
    endpoint: str = None
    app_name: str = None
    deployment_id: str = None

    def __post_init__(self):
        if self.endpoint:
            return

        self.endpoint = resource_endpoint_lookup(
            resource_type=self.resource_type,
            resource_name=self.resource_name,
            app_name=self.app_name,
            deployment_id=self.deployment_id,
        )


@dataclass
class AsyncClientBase(BaseClient):
    '''
    Base class for asynchronous clients. Natively supports resource discovery for the endpoint
    '''
    resource_name: str
    endpoint: str = None
    app_name: str = None
    deployment_id: str = None
    resource_type: str = ResourceType.ASYNC_SERVICE

    def __post_init__(self):
        super().__post_init__()
        self.boto_client = boto3.client('sqs')

    def publish(self, body: Union[Dict, str], delay: int = 0):
        formatted_body = body

        if isinstance(body, dict):
            formatted_body = json.dumps(body) 

        self.boto_client.send_message(
            QueueUrl=self.endpoint,
            MessageBody=formatted_body,
            DelaySeconds=delay,
        )


@dataclass
class RESTClientResponse:
    '''
    A response object for the DaVinci REST client. Contains the original requests.Response object,
    the status code, and the response body (if applicable)
    '''
    response: requests.Response
    status_code: int
    response_body: Dict = None


@dataclass
class RESTClientBase(BaseClient):
    '''
    Base class for REST clients that utilize the AWS SigV4 authentication scheme.
    Natively supports resource discovery for the endpoint with DaVinci.
    '''
    resource_name: str
    endpoint: str = None
    app_name: str = None
    deployment_id: str = None
    disable_auth: bool = False
    resource_type: str = ResourceType.REST_SERVICE

    def __post_init__(self):
        super().__post_init__()

        if self.disable_auth:
            self.aws_auth = None
        else:
            self.aws_auth = AWSSigV4('lambda')

    def _full_url(self, path: str = None) -> str:
        '''
        Given a path, return the full URL for the API
        '''
        if path:
            return urljoin(self.endpoint, path)

        return self.endpoint

    def _response(self, response: requests.Response, expect_body: bool = True) -> RESTClientResponse:
        '''
        Generate a RESTClientResponse object from a requests.Response object. If expect_body is True,
        the response body will be parsed as JSON and included in the response object.

        If the response status code is not 2xx, an exception will be raised.

        Keyword Arguments:
            response: requests.Response object
            expect_body: Whether or not to expect a response body (default: True)
        '''
        response.raise_for_status()

        if expect_body:
            response_body = response.json()
        else:
            response_body = None

        return RESTClientResponse(
            response=response,
            status_code=response.status_code,
            response_body=response_body,
        )

    def get(self, headers: Optional[Dict] = None, params: Optional[Dict] = None,
            path: Optional[str] = None) -> RESTClientResponse:
        '''
        Perform a GET request

        Keyword Arguments:
            headers: Headers to include in the request
            params: Query parameters to include in the request (default: None)
            path: Path to append to the endpoint (default: None)
        '''
        result = requests.request(
            'GET',
            url=self._full_url(path),
            auth=self.aws_auth,
            headers=headers,
            params=params,
        )

        return self._response(result)

    def put(self, body: Dict, headers: Optional[Dict] = None,
            path: Optional[str] = None) -> RESTClientResponse:
        '''
        Perform a PUT request

        Keyword Arguments:
            body: Body of the request
            headers: Headers to include in the request
            path: Path to append to the endpoint (default: None)
        '''
        result = requests.request(
            'PUT',
            url=self._full_url(path),
            auth=self.aws_auth,
            headers=headers,
            json=body,
        )

        return self._response(result)

    def post(self, body: Dict, headers: Optional[Dict] = None,
             path: Optional[str] = None) -> RESTClientResponse:
        '''
        Perform a POST request

        Keyword Arguments:
            body: Body of the request
            headers: Headers to include in the request
            path: Path to append to the endpoint (default: None)
        '''
        result = requests.request(
            'POST',
            url=self._full_url(path),
            auth=self.aws_auth,
            headers=headers,
            json=body,
        )

        return self._response(result)