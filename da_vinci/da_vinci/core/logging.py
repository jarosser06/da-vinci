import logging

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

        if not log_level_name and global_settings_available():
            ll_setting = setting_value(
                key='log_level',
                namespace='core',
            )

            log_level_name = ll_setting.setting_value

        self.pylogger = logging.getLogger()

        self.log_level_name = log_level_name or DEFAULT_LOG_LEVEL_NAME

        self.pylogger.setLevel(level=self.log_level_name.upper())

    def log(self, level: str, message: str):
        level_fn = getattr(self.pylogger, level)

        level_fn(
            level=level,
            msg=f'{self.namespace}: {message}',
        )

    def debug(self, message: str):
        """Add a log message with level DEBUG."""

        self.log(level='debug', message=message)

    def error(self, message: str):
        """Add a log message with level ERROR."""
        self.log(level='error', message=message)

    def info(self, message: str):
        """Add a log message with level INFO."""
        self.log(level='info', message=message)

    def warning(self, message: str):
        """Add a log message with level WARNING."""
        self.log(level='warn', message=message)