import json
import logging
from banal.dicts import clean_dict
from datetime import datetime, date

QUEUE_EXPIRE = 84600 * 14
log = logging.getLogger(__name__)


def unpack_int(value):
    try:
        return int(value)
    except Exception:
        return 0


def pack_datetime(value):
        if value is not None:
            return str(value)


def pack_now():
    return pack_datetime(datetime.utcnow())


def unpack_datetime(value, default=None):
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
    except Exception:
        return default


class JSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        if isinstance(obj, set):
            return [o for o in obj]
        return json.JSONEncoder.default(self, obj)


def dump_json(data):
    if data is None:
        return
    data = clean_dict(data)
    return JSONEncoder().encode(data)


def load_json(encoded):
    if encoded is None:
        return
    return json.loads(encoded)
