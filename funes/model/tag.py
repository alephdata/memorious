import logging
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, String, Integer, DateTime

from funes.core import session
from funes.model.common import Base

log = logging.getLogger(__name__)


class Tag(Base):
    """A simple key/value table used to store interim results."""
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    crawler = Column(String, nullable=False, index=True)
    key = Column(String, nullable=False, index=True)
    value = Column(JSONB, nullable=False, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def save(cls, crawler, key, value):
        obj = cls.find(crawler, key)
        if obj is None:
            obj = cls()
            obj.crawler = crawler.name
            obj.key = key
        obj.value = value
        session.add(obj)
        session.flush()
        return obj

    @classmethod
    def find(cls, crawler, key):
        q = session.query(cls)
        q = q.filter(cls.crawler == crawler.name)
        q = q.filter(cls.key == key)
        q = q.order_by(cls.timestamp.desc())
        return q.first()

    @classmethod
    def exists(cls, crawler, key):
        q = session.query(cls)
        q = q.filter(cls.crawler == crawler.name)
        q = q.filter(cls.key == key)
        return q.count() > 0

    def __repr__(self):
        return '<Tag(%s,%s)>' % (self.crawler, self.key)
