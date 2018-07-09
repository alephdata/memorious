import json
import logging

from memorious.model.common import Base
from memorious.util import make_key

log = logging.getLogger(__name__)


class Tag(Base):
    """A simple key/value table used to store interim results."""

    @classmethod
    def save(cls, crawler, key, value):
        data = json.dumps(value)
        cls.conn.set(make_key(crawler, "tag", key), data, ex=crawler.expire)

    @classmethod
    def find(cls, crawler, key):
        value = cls.conn.get(make_key(crawler, "tag", key))
        if value is not None:
            return json.loads(value)

    @classmethod
    def exists(cls, crawler, key):
        return cls.conn.exists(make_key(crawler, "tag", key))

    @classmethod
    def delete(cls, crawler):
        for key in cls.conn.scan_iter(make_key(crawler, "tag", "*")):
            cls.conn.delete(key)
