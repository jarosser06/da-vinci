'''
Exception Trap Service module
'''
from datetime import datetime, timedelta, UTC as utc_tz
from typing import Dict, Optional

from da_vinci.core.logging import Logger
from da_vinci.core.global_settings import setting_value
from da_vinci.core.rest_service_base import Route, SimpleRESTServiceBase

from da_vinci.exception_trap.tables.trapped_exceptions import (
    TrappedException,
    TrappedExceptions,
)


logging = Logger('da_vinci_framework::exception_trap')


class ExceptionTrapService(SimpleRESTServiceBase):
    def __init__(self):
        """
        Exception trap service
        """
        self.trapped_exceptions = TrappedExceptions()

        super().__init__(
            routes=[
                Route(handler=self.trap_exception, method='POST', path='/')
            ]
        )

    def trap_exception(self, function_name: str, exception: str, exception_traceback: str,
                       originating_event: Dict, log_execution_id: Optional[str] = None, 
                       log_namespace: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Trap an exception

        Keyword Arguments:
            function_name: The name of the function that raised the exception
            exception: The exception that was raised
            exception_traceback: The traceback of the exception
            originating_event: The event that caused the exception, stored as a JSON string
            log_execution_id: The execution ID to track the logging
            log_namespace: The namespace for the logger
            metadata: Any additional metadata about the exception
        """
        logging.debug(f'Trapping exception from {originating_event}')

        ttl_hours = setting_value('da_vinci_framework::exceptions_trap', 'exception_retention_hours')

        exception = TrappedException(
            created=datetime.now(tz=utc_tz),
            exception=exception,
            exception_traceback=exception_traceback,
            function_name=function_name,
            originating_event=originating_event,
            log_execution_id=log_execution_id,
            log_namespace=log_namespace,
            metadata=metadata,
            time_to_live=datetime.now(tz=utc_tz) + timedelta(hours=ttl_hours),
        )

        logging.debug(f'Trapped exception: {exception.to_dict()}')

        self.trapped_exceptions.put(exception)

        return self.respond(
            body={'message': 'exception noted'},
            status_code=201,
        )


def api(event: Dict, context: Dict):
    """
    API handler for the event bus watcher

    Keyword Arguments:
        event: The event
        context: The context, not used
    """
    logging.debug(f'Exception event: {event}')

    trapper = ExceptionTrapService()

    return trapper.handle(event=event)