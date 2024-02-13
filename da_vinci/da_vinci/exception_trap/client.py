import json
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
                 originating_event: Dict, metadata: Optional[Dict] = None):
        """
        Report an exception to the exception trap

        Keyword Arguments:
            function_name: The name of the function that raised the exception
            exception: The exception that was raised
            exception_traceback: The traceback of the exception
            originating_event: The event that caused the exception
            metadata: Any additional metadata about the exception
        """

        req_body = ReportedException(
            exception=exception,
            exception_traceback=exception_traceback,
            function_name=function_name,
            originating_event=originating_event,
            metadata=metadata,
        )

        logger = Logger(namespace='da_vinci.exception_trap_client')

        logger.debug(f'Reporting exception: {req_body.to_dict()}')

        self.post(body=req_body.to_dict())


def fn_exception_reporter(function_name: str, metadata: Optional[Dict] = None):
    """Wraps a function that handles an event and reports any exception"""
    def reporter_wrapper(func: Callable):
        @wraps(func)
        def wrapper(event: Dict, context: Dict):
            logger = Logger(namespace='da_vinci.exception_trap_client')
            try:
                logger.debug(f'Executing function {function_name}({event})')

                return func(event, context)
            except Exception as exc:
                if exception_trap_enabled():
                    reporter = ExceptionReporter()

                    logger.debug(f'Function threw exception: {traceback.format_exc()}')

                    reporter.report(
                        originating_event=event,
                        function_name=function_name,
                        exception=str(exc),
                        exception_traceback=traceback.format_exc(),
                        metadata=metadata,
                    )

                traceback.print_exc()
        return wrapper
    return reporter_wrapper
