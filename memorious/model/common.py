from datetime import datetime

from memorious.core import connect_redis


class Base(object):
    conn = connect_redis()

    @classmethod
    def pack_datetime(cls, value):
        if value is not None:
            return str(value)

    @classmethod
    def unpack_datetime(cls, value):
        if value is not None:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
