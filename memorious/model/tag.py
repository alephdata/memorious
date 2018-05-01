import logging
from datetime import datetime
from sqlalchemy import func
from sqlalchemy import Column, String, Integer, DateTime

from memorious.core import session
from memorious.model.common import Base, JSON

log = logging.getLogger(__name__)
unset = type('Unset', (object,), {})


class Tag(Base):
    """A simple key/value table used to store interim results."""
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    crawler = Column(String(255), nullable=False, index=True)
    key = Column(String, nullable=False, index=True)
    value = Column(JSON, nullable=False, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def save(cls, crawler, key, value):
        obj = cls.find(crawler, key)
        if obj is None:
            obj = cls()
            obj.crawler = crawler.name
            obj.key = key
        obj.value = value
        obj.timestamp = datetime.utcnow()
        session.add(obj)
        return obj

    @classmethod
    def find(cls, crawler, key, since=None):
        q = session.query(cls)
        q = q.filter(cls.crawler == crawler.name)
        q = q.filter(cls.key == key)
        if since is not None:
            q = q.filter(cls.timestamp >= since)
        q = q.order_by(cls.timestamp.desc())
        return q.first()

    @classmethod
    def exists(cls, crawler, key, since=None, value=unset):
        q = session.query(cls)
        q = q.filter(cls.crawler == crawler.name)
        q = q.filter(cls.key == key)
        if since is not None:
            q = q.filter(cls.timestamp >= since)
        if value is not unset:
            q = q.filter(cls.value == value)
        return q.count() > 0

    @classmethod
    def latest(cls, crawler):
        q = session.query(func.max(cls.timestamp))
        q = q.filter(cls.crawler == crawler.name)
        for (timestamp,) in q:
            return timestamp

    @classmethod
    def delete(cls, crawler):
        pq = session.query(cls)
        pq = pq.filter(cls.crawler == crawler)
        pq.delete(synchronize_session=False)

    def __repr__(self):
        return '<Tag(%s,%s)>' % (self.crawler, self.key)
