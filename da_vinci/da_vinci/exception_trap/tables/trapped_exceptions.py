from datetime import datetime, timedelta, UTC as utc_tz
from typing import List, Optional 
from uuid import uuid4

from da_vinci.core.orm import (
    TableClient,
    TableObject,
    TableObjectAttribute,
    TableObjectAttributeType,
    TableScanDefinition,
)


class TrappedException(TableObject):
    table_name = 'trapped_exceptions'

    description = 'Holds exceptions that have been trapped'

    partition_key_attribute = TableObjectAttribute(
        'function_name',
        TableObjectAttributeType.STRING,
        description='The name of the function that produced the exception',
    )

    sort_key_attribute = TableObjectAttribute(
        'exception_id',
        TableObjectAttributeType.STRING,
        description='The ID of the exception',
        default=lambda: str(uuid4()),
    )

    ttl_attribute = TableObjectAttribute(
        'time_to_live',
        TableObjectAttributeType.DATETIME,
        description='The TTL for the record',
        default=lambda: datetime.now(tz=utc_tz) + timedelta(days=2)
    )

    attributes = [
        TableObjectAttribute(
            'created',
            TableObjectAttributeType.DATETIME,
            description='The datetime the exception was created',
        ),

        TableObjectAttribute(
            'exception',
            TableObjectAttributeType.STRING,
            description='The exception that was trapped',
        ),

        TableObjectAttribute(
            'exception_traceback',
            TableObjectAttributeType.STRING,
            description='The traceback of the exception',
        ),

        TableObjectAttribute(
            'log_execution_id',
            TableObjectAttributeType.STRING,
            description='The execution ID of the log',
            optional=True,
        ),

        TableObjectAttribute(
            'log_namespace',
            TableObjectAttributeType.STRING,
            description='The namespace of the log',
            optional=True,
        ),

        TableObjectAttribute(
            'metadata',
            TableObjectAttributeType.JSON_STRING,
            description='Any additional information about the exception',
            default={},
            optional=True,
        ),

        TableObjectAttribute(
            'originating_event',
            TableObjectAttributeType.JSON_STRING,
            description='The originating event that caused the exception',
        ),

        TableObjectAttribute(
            'trapped_on',
            TableObjectAttributeType.DATETIME,
            default=lambda: datetime.now(tz=utc_tz),
            description='The datetime the exception was trapped',
        )
    ]


class TrappedExceptionsScanDefinition(TableScanDefinition):
    def __init__(self):
        """
        The scan definition for the TrappedExceptions table
        """
        super().__init__(
            table_object_class=TrappedException,
        )


class TrappedExceptions(TableClient):
    def __init__(self, app_name: Optional[str] = None, deployment_id: Optional[str] = None):
        """
        The client for the TrappedExceptions table

        Keyword Arguments:
            app_name: The name of the application
            deployment_id: The ID of the deployment
        """
        super().__init__(
            app_name=app_name,
            default_object_class=TrappedException,
            deployment_id=deployment_id,
        )

    def get(self, function_name: str, exception_id: str) -> TrappedException:
        """
        Get a trapped exception

        Keyword Arguments:
            function_name: The name of the function that produced the exception
            exception_id: The ID of the exception
        """
        return self.get_object(
            partition_key_value=function_name,
            sort_key_value=exception_id,
        )

    def delete(self, trapped_exception: TrappedException):
        """
        Delete a trapped exception

        Keyword Arguments:
            trapped_exception: The trapped exception to delete
        """
        self.delete_object(
            table_object=trapped_exception,
        )

    def put(self, trapped_exception: TrappedException) -> TrappedException:
        return self.put_object(
            table_object=trapped_exception,
        )

    def scan(self, scan_definition: TrappedExceptionsScanDefinition) -> List[TrappedException]:
        """
        Scan trapped exceptions

        Keyword Arguments:
            scan_definition: The scan definition
        """
        return self.full_scan(
            scan_definition=scan_definition,
        )