from datetime import datetime

from memorious.core import connect_redis


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


class Base(object):
    conn = connect_redis()
