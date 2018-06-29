import logging
import json
from datetime import datetime

import attr

from memorious.model.common import Base

log = logging.getLogger(__name__)
unset = type('Unset', (object,), {})


@attr.s
class Tag(Base):
    """A simple key/value table used to store interim results."""
    value = attr.ib(default=attr.Factory(dict))

    @classmethod
    def save(cls, crawler, key, value):
        obj = cls()
        obj.value = value
        obj.crawler = crawler.name
        obj.key = key
        cls.conn.set(crawler.name + ":tag:" + key, json.dumps(value))
        cls.conn.set(
            crawler.name + ":tag:timestamp:" + key, datetime.utcnow().timestamp()
        )
        return obj

    @classmethod
    def find(cls, crawler, key):
        obj = cls()
        val = cls.conn.get(crawler.name + ":tag:" + key)
        if val:
            obj.value = json.loads(val)
            obj.crawler = crawler.name
            obj.key = key
            return obj

    @classmethod
    def exists(cls, crawler, key, since=None):
        tag = cls.conn.get(crawler.name + ":tag:" + key)
        if tag is None:
            return False
        if since:
            ts = float(cls.conn.get(crawler.name + ":tag:timestamp:" + key))
            if ts < since.timestamp():
                return False
        return True

    @classmethod
    def delete(cls, crawler):
        for key in cls.conn.scan_iter(crawler.name + ":tag:*"):
            cls.conn.delete(key)

    def __repr__(self):
        return '<Tag(%s,%s)>' % (self.crawler, self.key)
