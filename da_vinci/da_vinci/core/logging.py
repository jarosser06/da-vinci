import json
import logging

from datetime import datetime, UTC as utc_tz
from os import environ
from typing import List, Optional
from uuid import uuid4

import boto3

DEFAULT_LOG_LEVEL_NAME = 'INFO'

S3_BUCKET_ENV_VAR = 'DA_VINCI_S3_LOGGING_BUCKET'


class S3LogHandler(logging.Handler):
    """Custom log handler to store logs in memory and offload them to S3."""
    def __init__(self, execution_id: str, namespace: str):
        super().__init__()

        self.execution_id = execution_id

        self.namespace = namespace

        self.log_entries = []

    def emit(self, record) -> None:
        """Capture log records and store them in memory."""
        log_entry = {
            'timestamp': datetime.now(tz=utc_tz).isoformat(),
            'level': record.levelname,
            'namespace': self.namespace,
            'message': record.getMessage(),
            'execution_id': self.execution_id
        }

        self.log_entries.append(log_entry)

    def get_log_entries(self) -> List:
        """
        Return the collected log entries.
        """
        return self.log_entries


class Logger:
    def __init__(self, namespace: str, log_level_name: Optional[str] = None, s3_logging_enabled: bool = True,
                 s3_logging_bucket_name: Optional[str] = None):
        """
        Initialize the logger with the namespace and log level name.

        Keyword Arguments:
        namespace -- The namespace for the logger
        log_level_name -- The log level name (default: INFO)
        s3_logging_enabled -- Enable logging to S3 (default: True)
        s3_logging_bucket_name -- The S3 bucket name for logging (default: None)
        """
        self.namespace = namespace

        self.execution_id = str(uuid4())  # Unique ID for each execution

        log_level_name = log_level_name or environ.get('LOG_LEVEL', DEFAULT_LOG_LEVEL_NAME)

        self.pylogger = logging.getLogger()

        self.log_level_name = log_level_name.upper()

        self.pylogger.setLevel(self.log_level_name)

        # Custom handler to collect logs in memory
        self.s3_log_handler = S3LogHandler(self.execution_id, namespace)

        self.pylogger.addHandler(self.s3_log_handler)

        # S3 logging configuration
        self.s3_logging_enabled = s3_logging_enabled and S3_BUCKET_ENV_VAR in environ

        if self.s3_logging_enabled:
            self.s3_bucket = s3_logging_bucket_name or environ.get(S3_BUCKET_ENV_VAR)

        else:
            self.s3_bucket = None

        self.s3_client = boto3.client('s3') if self.s3_logging_enabled else None

        if self.s3_logging_enabled:
            logging.info(f"S3 logging enabled: {self.s3_bucket}")

        logging.info(f"Logger initialized with execution ID: {self.execution_id}")

    def dump_to_s3(self) -> None:
        """
        Dump the collected logs to an S3 bucket as a JSON file.
        """
        if not self.s3_logging_enabled:
            self.pylogger.warning("S3 logging is disabled. Skipping S3 log upload.")
            return

        log_filename = f"logs/{self.namespace}/{self.execution_id}.json"
        try:
            log_data = json.dumps(self.s3_log_handler.get_log_entries(), indent=4)
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=log_filename,
                Body=log_data
            )
            self.pylogger.info(f"Log successfully uploaded to S3: {log_filename}")
        except Exception as e:
            self.pylogger.error(f"Failed to upload log to S3: {e}")

    def finalize(self) -> None:
        """
        Call this method to finalize logging and upload logs to S3 if enabled.
        """
        self.dump_to_s3()

    def debug(self, message: str) -> None:
        """
        Add a log message with level DEBUG.

        Keyword Arguments:
        message -- The log message
        """
        self._log('DEBUG', message)

    def info(self, message: str) -> None:
        """
        Add a log message with level INFO.
        
        Keyword Arguments:
        message -- The log message
        """
        self.pylogger.info(message)

    def warning(self, message: str) -> None:
        """
        Add a log message with level WARNING.

        Keyword Arguments:
        message -- The log message 
        """
        self.pylogger.warning(message)

    def error(self, message: str) -> None:
        """
        Add a log message with level ERROR.

        Keyword Arguments:
        message -- The log message
        """
        self.pylogger.error(message)