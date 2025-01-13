'''Event Bus Clients'''
import json
import logging
import traceback

from collections.abc import Callable
from dataclasses import asdict, dataclass
from enum import auto, StrEnum
from functools import wraps
from typing import Dict, Optional, Union

from da_vinci.core.client_base import AsyncClientBase, RESTClientBase
from da_vinci.core.immutable_object import ObjectBodySchema
from da_vinci.core.json import DaVinciObjectEncoder
from da_vinci.core.logging import Logger

from da_vinci.event_bus.event import Event

from da_vinci.exception_trap.client import ExceptionReporter


class EventPublisher(AsyncClientBase):
    def __init__(self):
        super().__init__(resource_name='event_bus')

    def submit(self, event: Event, delay: Optional[int] = None):
        """
        Publish an event to the event bus

        Keyword Arguments:
            event: Event to publish
        """
        _delay = delay or 0

        event_body_json = json.dumps(event.to_dict(), cls=DaVinciObjectEncoder)

        self.publish(body=event_body_json, delay=_delay)


class EventResponseStatus(StrEnum):
    FAILURE = 'FAILURE'
    INITIALIZED = 'INITIALIZED'
    NO_SUBSCRIPTIONS = 'NO_SUBSCRIPTIONS'
    SUCCESS = 'SUCCESS'


@dataclass
class EventResponse:
    """
    EventResponse is a dataclass that represents the response from an event
    handler.
    """
    event: Event
    status: EventResponseStatus
    failure_reason: Optional[str] = None
    failure_traceback: Optional[str] = None
    response_id: Optional[str] = None

    def to_dict(self) -> Dict:
        """
        Create a dictionary representation of the EventResponse

        Returns:
            Dict
        """

        return asdict(self)

    def to_json(self) -> str:
        """
        Create a JSON representation of the EventResponse

        Returns:
            str
        """

        return json.dumps(self.to_dict(), cls=DaVinciObjectEncoder)


class EventResponder(RESTClientBase):
    def __init__(self):
        super().__init__(resource_name='event_bus_responses')

    def response(self, event: Union[Event, Dict], status: Union[EventResponseStatus, str],
                 failure_reason: Optional[str] = None, failure_traceback: Optional[str] = None,
                 response_id: Optional[str] = None):
        """
        Publish an EventResponse

        Keyword Arguments:
            event: Event to respond to
            status: Status of the response
            failure_reason: Reason for failure (if applicable)
            failure_traceback: Traceback for failure (if applicable)
            response_id: ID of the response
        """

        if isinstance(event, Event):
            event = event.to_dict()

        response_body = EventResponse(
            event=event,
            status=status,
            failure_reason=failure_reason,
            failure_traceback=failure_traceback,
            response_id=response_id,
        )

        self.post(body=response_body.to_dict())


def fn_event_response(exception_reporter: Optional[ExceptionReporter] = None,
                      function_name: Optional[str] = None, handle_callbacks: Optional[bool] = False,
                      logger: Optional[Logger] = None, re_raise: Optional[bool] = False,
                      schema: Optional[ObjectBodySchema] = None):
    """
    Wraps a function that tracks event responses. When wrapped, the function
    will report any results to the event watcher. The function can optionally validate the entire event body
    using a provided ObjectBodySchema.

    Keyword Arguments:
        exception_reporter: ExceptionReporter to use for reporting exceptions, optional
        function_name: Name of the function to report exceptions for, defaults to the literal python function name
        handle_callbacks: Whether or not to handle callback event callback requests. This must be set to True for the function to send failure callbacks as well.
        logger: Logger to use for logging, optional
        re_raise: If True, the exception will be re-raised after reporting, optional
        schema: ObjectBodySchema-based object to use for validating the event body, optional. When provided, the event body will be validated
    """
    def event_response_wrapper(func: Callable):
        @wraps(func)
        def wrapper(event: Dict, context: Dict):
            logging.debug(f'Raw event {event}')

            _logger = logger or Logger('da_vinci.event_bus.response_wrapper')

            _function_name = function_name or func.__name__

            event_responder = EventResponder()

            event_obj = Event.from_lambda_event(event=event)

            _logger.s3_log_handler.put_metadata('originating_event', event_obj.to_dict())

            try:
                logging.debug(f'Executing function with event {event}')

                if schema:
                    logging.debug('Validating event body')

                    schema.validate_object(event_obj.body)

                fn_result = func(event, context)

                # If the function returns a result and we are handling callbacks
                # check if the event has a callback event type and publish the result
                if fn_result and handle_callbacks:
                    logging.debug('Function returned a result, checking for callback event type')

                    logging.debug(f'Event object {event_obj.to_dict()}')

                    if event_obj.callback_event_type:
                        logging.debug('Function has a callback event type, publishing result')

                        event_publisher = EventPublisher()

                        event_publisher.submit(
                            event=Event(
                                body=fn_result,
                                event_type=event_obj.callback_event_type,
                                previous_event_id=event_obj.event_id
                            )
                        )

                        logging.debug(f'Published callback event to {event_obj.callback_event_type}')

                event_responder.response(
                    event=event_obj,
                    status=EventResponseStatus.SUCCESS
                )

                return fn_result

            except Exception as exc:
                event_responder.response(
                    event=event_obj,
                    status=EventResponseStatus.FAILURE, 
                    failure_reason=str(exc),
                    failure_traceback=traceback.format_exc(),
                    response_id=event_obj.response_id
                )

                if exception_reporter:
                    # If the function name is not provided, use the function name
                    exception_reporter.report(
                        exception=str(exc),
                        exception_traceback=traceback.format_exc(),
                        function_name=_function_name,
                        originating_event=event,
                        log_execution_id=_logger.execution_id,
                        log_namespace=_logger.namespace,
                    )

                if handle_callbacks:
                    logging.debug('Checking for callback event type')

                    if event_obj.callback_event_type_on_failure:
                        logging.debug('Function has a callback event type, publishing failure')

                        event_publisher = EventPublisher()

                        event_publisher.submit(
                            event=Event(
                                body={
                                    'da_vinci_event_bus_response': {
                                        'status': 'failure',
                                        'reason': str(exc),
                                        'traceback': traceback.format_exc(),
                                    },
                                    'originating_event_details': {
                                        'event_id': event_obj.event_id,
                                        'response_id': event_obj.response_id,
                                        'event_type': event_obj.event_type,
                                        'event_body': event_obj.body,
                                    },
                                },
                                event_type=event_obj.callback_event_type_on_failure,
                                previous_event_id=event_obj.event_id
                            )
                        )

                        logging.debug(f'Published callback event to {event_obj.callback_event_type}')

                traceback.print_exc()

                if re_raise:
                    raise

            finally:
                _logger.finalize()

        return wrapper

    return event_response_wrapper