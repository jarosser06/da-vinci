"""
JSON Utility functionality
"""

from datetime import datetime
from json import JSONEncoder
from typing import Any

from da_vinci.core.immutable_object import ObjectBody


class DateTimeEncoder(JSONEncoder):
    """
    JSONEncoder class that encodes datetime objects strings
    """

    def default(self, obj: Any) -> Any:
        """
        Encode datetime objects as ISO format strings

        Keyword Arguments:
        obj -- Object to encode

        Raises:
            TypeError -- If object is not JSON serializable
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        return JSONEncoder.default(self, obj)


class DaVinciObjectEncoder(JSONEncoder):
    """
    JSONEncoder class that encodes commonly used framework objects
    """

    def default(self, obj: Any) -> Any:
        """
        Encode Da Vinci framework objects and datetime objects

        Handles ObjectBody instances by converting to dictionaries and
        datetime objects by converting to ISO format strings.

        Keyword Arguments:
        obj -- Object to encode

        Raises:
            TypeError -- If object is not JSON serializable
        """
        if isinstance(obj, ObjectBody):
            return obj.to_dict()

        if isinstance(obj, datetime):
            return obj.isoformat()

        return JSONEncoder.default(self, obj)
