
import logging

from os import environ
from typing import Optional

from da_vinci.core.global_settings import (
    global_settings_available,
    setting_value,
)


DEFAULT_LOG_LEVEL_NAME = 'INFO'


class Logger:
    def __init__(self, namespace: str, log_level_name: Optional[str] = None):
        self.namespace = namespace

        log_level_name = log_level_name

        if not log_level_name:
            log_level_name = environ.get('LOG_LEVEL', DEFAULT_LOG_LEVEL_NAME)

        self.pylogger = logging.getLogger()

        self.log_level_name = log_level_name or DEFAULT_LOG_LEVEL_NAME

        self.pylogger.setLevel(level=self.log_level_name.upper())

    def debug(self, message: str):
        """Add a log message with level DEBUG."""

        self.pylogger.debug(message)

    def error(self, message: str):
        """Add a log message with level ERROR."""
        self.pylogger.error(message)

    def info(self, message: str):
        """Add a log message with level INFO."""
        self.pylogger.info(message)

    def warning(self, message: str):
        """Add a log message with level WARNING."""
        self.pylogger.warning(message)

    def exception(self, message: str):
        """Add a log message with level ERROR."""
        self.pylogger.exception(message)