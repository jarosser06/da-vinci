"""
JSON Utility functionality
"""

from datetime import datetime
from json import JSONEncoder

from da_vinci.core.immutable_object import ObjectBody


class DateTimeEncoder(JSONEncoder):
    """
    JSONEncoder class that encodes datetime objects strings
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return JSONEncoder.default(self, obj)


class DaVinciObjectEncoder(JSONEncoder):
    """
    JSONEncoder class that encodes commonly used framework objects
    """

    def default(self, obj):
        if isinstance(obj, ObjectBody):
            return obj.to_dict()

        if isinstance(obj, datetime):
            return obj.isoformat()

        return JSONEncoder.default(self, obj)
