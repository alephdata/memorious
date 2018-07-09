import json
import logging

from memorious.model.common import Base

log = logging.getLogger(__name__)


class Tag(Base):
    """A simple key/value table used to store interim results."""

    @classmethod
    def save(cls, crawler, key, value):
        cls.conn.set(crawler.name + ":tag:" + key,
                     json.dumps(value),
                     ex=crawler.expire)

    @classmethod
    def find(cls, crawler, key):
        value = cls.conn.get(crawler.name + ":tag:" + key)
        if value is not None:
            return json.loads(value)

    @classmethod
    def exists(cls, crawler, key):
        return cls.conn.exists(crawler.name + ":tag:" + key)

    @classmethod
    def delete(cls, crawler):
        for key in cls.conn.scan_iter(crawler.name + ":tag:*"):
            cls.conn.delete(key)
