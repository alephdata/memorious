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
    crawler = Column(String(255), nullable=False, index=True)
    run_id = Column(String(50), nullable=True, index=True)
    key = Column(String, nullable=False, index=True)
    value = Column(JSONB, nullable=False, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def save(cls, crawler, key, value, run_id=None):
        obj = cls.find(crawler, key, run_id=run_id)
        if obj is None:
            obj = cls()
            obj.crawler = crawler.name
            obj.run_id = run_id
            obj.key = key
        obj.value = value
        session.add(obj)
        session.flush()
        return obj

    @classmethod
    def find(cls, crawler, key, run_id=None):
        q = session.query(cls)
        q = q.filter(cls.crawler == crawler.name)
        q = q.filter(cls.run_id == run_id)
        q = q.filter(cls.key == key)
        q = q.order_by(cls.timestamp.desc())
        return q.first()

    @classmethod
    def exists(cls, crawler, key, run_id=None):
        q = session.query(cls)
        q = q.filter(cls.crawler == crawler.name)
        q = q.filter(cls.run_id == run_id)
        q = q.filter(cls.key == key)
        return q.count() > 0

    @classmethod
    def delete(cls, crawler):
        pq = session.query(cls)
        pq = pq.filter(cls.crawler == crawler)
        pq.delete(synchronize_session=False)
        session.flush()

    def __repr__(self):
        return '<Tag(%s,%s)>' % (self.crawler, self.key)
