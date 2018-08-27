import logging

from memorious.model.common import Base, dump_json, load_json
from memorious.model.common import delete_prefix
from memorious.util import make_key

log = logging.getLogger(__name__)


class Tag(Base):
    """A simple key/value table used to store interim results."""

    @classmethod
    def save(cls, crawler, key, value):
        data = dump_json(value)
        key = make_key(crawler, "tag", key)
        cls.conn.set(key, data, ex=crawler.expire)

    @classmethod
    def find(cls, crawler, key):
        value = cls.conn.get(make_key(crawler, "tag", key))
        if value is not None:
            return load_json(value)

    @classmethod
    def exists(cls, crawler, key):
        return cls.conn.exists(make_key(crawler, "tag", key))

    @classmethod
    def delete(cls, crawler):
        delete_prefix(cls.conn, make_key(crawler, "tag", "*"))
