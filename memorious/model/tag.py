import json
import logging

from memorious.model.common import Base

log = logging.getLogger(__name__)


class Tag(Base):
    """A simple key/value table used to store interim results."""

    @classmethod
    def tag(cls, crawler, key):
        return crawler.name + ":tag:" + key

    @classmethod
    def save(cls, crawler, key, value):
        data = json.dumps(value)
        cls.conn.set(cls.tag(crawler, key), data, ex=crawler.expire)

    @classmethod
    def find(cls, crawler, key):
        value = cls.conn.get(cls.tag(crawler, key))
        if value is not None:
            return json.loads(value)

    @classmethod
    def exists(cls, crawler, key):
        return cls.conn.exists(cls.tag(crawler, key))

    @classmethod
    def delete(cls, crawler):
        for key in cls.conn.scan_iter(cls.tag(crawler, '*')):
            cls.conn.delete(key)
