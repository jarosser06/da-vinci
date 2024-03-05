from datetime import datetime
from typing import Dict, Optional

from da_vinci.core.logging import Logger
from da_vinci.core.rest_service_base import (
    Route,
    SimpleRESTServiceBase,
)

from da_vinci.exception_trap.tables.trapped_exceptions import (
    TrappedException,
    TrappedExceptions,
)


class ExceptionTrapService(SimpleRESTServiceBase):
    def __init__(self):
        self.trapped_exceptions = TrappedExceptions()

        super().__init__(
            routes=[
                Route(
                    handler=self.trap_exception,
                    method='POST',
                    path='/',
                )
            ]
        )

        self.logger = Logger('da_vinci.exception_trap_service')

    def trap_exception(self, function_name: str, exception: str, exception_traceback: str,
                       originating_event: Dict, metadata: Optional[Dict] = None):
        """
        Trap an exception

        Keyword Arguments:
            function_name: The name of the function that raised the exception
            exception: The exception that was raised
            exception_traceback: The traceback of the exception
            originating_event: The event that caused the exception
            metadata: Any additional metadata about the exception
        """
        self.logger.debug(f'Trapping exception from {originating_event}')

        exception = TrappedException(
            created=datetime.now(),
            exception=exception,
            exception_traceback=exception_traceback,
            function_name=function_name,
            originating_event=originating_event,
            metadata=metadata,
        )

        self.logger.debug(f'Trapped exception: {exception.to_dict()}')

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
        context: The context
    """
    logger = Logger('da_vinci.exception_trap_service')

    logger.debug(f'Exception event: {event}')

    trapper = ExceptionTrapService()

    return trapper.handle(event=event)