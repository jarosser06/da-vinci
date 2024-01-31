'''
JSON Utility

The existence of this pains me :facepalm:
'''

from datetime import datetime
from json import JSONEncoder


class DateTimeEncoder(JSONEncoder):
    '''
    JSONEncoder class that encodes datetime objects strings
    '''
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return JSONEncoder.default(self, obj)