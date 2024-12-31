import json
import logging
import traceback

from collections.abc import Callable
from dataclasses import asdict, dataclass
from functools import wraps
from os import getenv
from typing import Dict, Optional

from da_vinci.core.client_base import RESTClientBase
from da_vinci.core.json import DateTimeEncoder
from da_vinci.core.logging import Logger


EXCEPTION_TRAP_ENV_VAR = 'DaVinciFramework_ExceptionTrapEnabled'


def exception_trap_enabled() -> bool:
    """
    Determine if the exception trap is enabled

    Returns:
        bool
    """

    return getenv(EXCEPTION_TRAP_ENV_VAR, 'false').lower() == 'true'


@dataclass
class ReportedException:
    """
    ReportedException is a dataclass that represents an exception that was
    reported to the exception trap
    """
    exception: str
    exception_traceback: str
    function_name: str
    originating_event: Dict
    log_execution_id: Optional[str] = None
    log_namespace: Optional[str] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """
        Create a dictionary representation of the ReportedException

        Returns:
            Dict
        """

        return asdict(self)

    def to_json(self) -> str:
        """
        Create a JSON representation of the ReportedException

        Returns:
            str
        """

        return json.dumps(self.to_dict(), cls=DateTimeEncoder)

class ExceptionReporter(RESTClientBase):
    def __init__(self):
        super().__init__(resource_name='exceptions_trap')

    def report(self, function_name: str, exception: str, exception_traceback: str,
                originating_event: Dict, metadata: Optional[Dict] = None,
                 log_execution_id: Optional[str] = None, log_namespace: Optional[str] = None):
        """
        Report an exception to the exception trap

        Keyword Arguments:
            function_name: The name of the function that raised the exception
            exception: The exception that was raised
            exception_traceback: The traceback of the exception
            log_execution_id: The execution ID to track the logging
            log_namespace: The namespace for the logger
            metadata: Any additional metadata about the exception
            originating_event: The event that caused the exception
        """
        req_body = ReportedException(
            exception=exception,
            exception_traceback=exception_traceback,
            function_name=function_name,
            originating_event=originating_event,
            metadata=metadata,
            log_execution_id=log_execution_id,
            log_namespace=log_namespace,
        )

        logging.debug(f'Reporting exception: {req_body.to_dict()}')

        self.post(body=req_body.to_dict())


def fn_exception_reporter(func: Optional[Callable] = None, *, function_name: str = Optional[None],
                          metadata: Optional[Dict] = None, logger: Optional[Logger] = None, re_raise: bool = False):
    """
    Wraps a function that handles an event and reports any exception
    
    Keyword Arguments:
        function_name: The name of the function that raised the exception, if not provided, the function name will be used
        metadata: Any additional metadata about the exception
        logger: The logger to use for logging
        re_raise: If True, the exception will be re-raised after reporting
    """
    def reporter_wrapper(func: Callable):

        @wraps(func)
        def wrapper(event: Dict, context: Dict):
            _function_name = function_name or func.__name__

            _logger = logger or Logger(namespace='da_vinci.exception_trap_client')

            try:
                _logger.debug(f'Executing function {_function_name}({event})')

                return func(event, context)
            except Exception as exc:
                if exception_trap_enabled():
                    reporter = ExceptionReporter()

                    _logger.debug(f'Function threw exception: {traceback.format_exc()}')

                    reporter.report(
                        originating_event=event,
                        function_name=_function_name,
                        exception=str(exc),
                        exception_traceback=traceback.format_exc(),
                        metadata=metadata,
                        log_execution_id=_logger.execution_id,
                        log_namespace=_logger.namespace,
                    )

                traceback.print_exc()

                if re_raise:
                    raise

            finally:
                _logger.finalize()

        return wrapper

    if callable(func):
        return reporter_wrapper(func)

    return reporter_wrapper
