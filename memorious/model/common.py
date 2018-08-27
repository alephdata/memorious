import json
import logging
from banal.dicts import clean_dict
from datetime import datetime, date

from memorious.core import connect_redis

QUEUE_EXPIRE = 84600 * 14
log = logging.getLogger(__name__)


class Base(object):
    conn = connect_redis()


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


def unpack_datetime(value):
    if value is not None:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")


def delete_prefix(conn, prefix):
    # pipe = cls.conn.pipeline()
    # keys = cls.conn.scan_iter(make_key(crawler, "tag", "*"))
    # for idx, key in enumerate(keys):
    #     pipe.delete(key)
    #     if idx % 1000 == 0:
    #         log.info("Delete tags: %s...", idx)
    #         pipe.execute()
    #         pipe = cls.conn.pipeline()
    # pipe.execute()
    # log.info("Deleted %s tags", idx)
    keys = conn.scan_iter(prefix)
    batch = []
    for idx, key in enumerate(keys):
        batch.append(key)
        if len(batch) > 500:
            conn.delete(*batch)
            batch = []
    if len(batch):
        conn.delete(*batch)
    log.info("Delete prefix %s: %s", prefix, idx)


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
