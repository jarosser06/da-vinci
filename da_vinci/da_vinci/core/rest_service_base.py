'''
Provides the base class for constructing a REST service using the DaVinci framework
'''
import logging
import json
import traceback

from dataclasses import asdict, dataclass
from collections.abc import Callable
from typing import Any, Dict, List, Optional, Union

from da_vinci.core.exceptions import DuplicateRouteDefinitionError

from da_vinci.exception_trap.client import ExceptionReporter


LOG = logging.getLogger(__name__)


@dataclass
class SimpleRESTServiceResponse:
    '''
    A response object for the DaVinci REST service. Contains the original requests.Response object,
    as well as the response body
    '''
    body: Any
    status_code: int
    headers: Dict = None

    def to_dict(self) -> Dict:
        '''
        Return the response as a dictionary expected by AWS Lambda for REST responses
        '''
        resp_dikt = {
            'body': self.body,
            'statusCode': self.status_code,
        }

        if self.headers:
            resp_dikt['headers'] = self.headers

        return resp_dikt 


class ErrorResponse(SimpleRESTServiceResponse):
    '''
    Return a 400 response for an error
    '''
    def __init__(self, response_message: str, status_code: int = 400):
        super().__init__(
            body={'message': response_message, 'ok': False},
            status_code=status_code,
        )


class NotFoundResponse(ErrorResponse):
    '''
    Return a 404 response
    '''
    def __init__(self, resource: str):
        super().__init__(
            response_message=f'Resource {resource} not found',
            status_code=404,
        )


class InvalidRequestResponse(ErrorResponse):
    '''
    Return a 400 response for an invalid request
    '''
    def __init__(self, response_message: str):
        super().__init__(
            response_message=response_message,
            status_code=400,
        )


@dataclass
class Route:
    handler: Callable
    method: str
    path: str
    required_arguments: List[str] = None

    def validate_request(self, parameters: Dict = None) -> SimpleRESTServiceResponse:
        '''
        Validate that the request contains all required parameters

        Keyword Arguments:
            parameters: Parameters to validate
        '''
        if not self.required_arguments:
            return

        missing_arguments = list(set(self.required_arguments).difference(set(parameters.keys())))

        if missing_arguments:
            request_dikt = asdict(self)

            LOG.info(f'Request {request_dikt} missing arguments: {missing_arguments}')

            return InvalidRequestResponse(f'Request missing arguments: {missing_arguments}')

        return None


class SimpleRESTServiceBase:
    def __init__(self, routes: List[Route], exception_function_name: Optional[str] = None,
                 exception_reporter: Optional[ExceptionReporter] = None):
        """
        Enabling the creation of a simple REST service using the DaVinci framework

        Keyword Arguments:
            routes: List of Route objects
            exception_function_name: Name of the function to call when an exception occurs (default: None)
            exception_reporter: ExceptionReporter object (default: None)
        """
        self.routes = routes

        self.exception_function_name = exception_function_name

        if exception_reporter:
            self.exception_reporter = exception_reporter()

        # The current request being handled
        # not my favorite way to do this, but it works for now - JR
        self.current_request = None

        self._route_map = self._build_route_map()

        self._base_headers = {'Content-Type': 'application/json'}

    def _build_route_map(self) -> Dict[str, Route]:
        '''
        Build a map of routes
        '''
        route_map = {}

        for route in self.routes:
            if route.method not in route_map:
                route_map[route.method] = {}

                if route.path in route_map[route.method]:
                    raise DuplicateRouteDefinitionError(route.path)

            route_map[route.method][route.path] = route

        return route_map

    def handle(self, event: Dict):
        '''
        Handle an incoming event

        Takes an AWS Lambda event and returns a response

        Keyword Arguments:
            event: AWS Lambda event
        '''
        req_info = event['requestContext']['http']

        self.current_event = event
        self.current_request = req_info

        method = req_info['method']
        path = req_info['path']

        if method not in self._route_map or path not in self._route_map[method]:
            return NotFoundResponse(f'{path} - {method}')

        params = {}
        if 'queryStringParameters' in event:
            params = event['queryStringParameters']

        elif 'body' in event:
            params = json.loads(event['body'])

        route = self._route_map[method][path]

        validation_response = route.validate_request(parameters=params)

        if validation_response:
            return validation_response

        try:
            return route.handler(**params)

        except Exception as err:
            LOG.info(f'Exception occurred: {traceback.format_exc()}')

            report_fn_name = self.exception_function_name or route.handler.__name__

            if self.exception_reporter:
                self.exception_reporter.report(
                    exception=str(err),
                    exception_traceback=traceback.format_exc(),
                    function_name=report_fn_name,
                    originating_event=event,
                )

            return self.respond(
                body='Internal server error',
                status_code=500,
            )

    def respond(self, body: Union[Dict, str], status_code: int,
                headers: Dict = None) -> Dict:
        '''
        Respond to a request

        Keyword Arguments:
            body: Body of the response
            status_code: HTTP status code of the response
            headers: Headers to include in the response (default: None)
        '''
        headers = self._base_headers

        if headers:
            headers.update(headers)

        response = SimpleRESTServiceResponse(
            body=body,
            headers=headers,
            status_code=status_code,
        )

        return response.to_dict()