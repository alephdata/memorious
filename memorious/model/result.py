import logging
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey

from memorious.core import session
from memorious.model.common import Base, JSON

log = logging.getLogger(__name__)


class Result(Base):
    """A resource that has been retrieved, or that failed to retrieve."""
    __tablename__ = 'result'

    id = Column(Integer, primary_key=True)
    crawler = Column(String, nullable=False, index=True)
    prev_stage = Column(String, nullable=False, index=True)
    next_stage = Column(String, nullable=False, index=True)
    data = Column(JSON, nullable=False, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def save(cls, crawler, prev_stage, next_stage, data):
        obj = cls()
        obj.crawler = crawler.name
        obj.prev_stage = prev_stage
        obj.next_stage = next_stage
        obj.data = data
        session.add(obj)
        return obj

    @classmethod
    def delete(cls, crawler):
        pq = session.query(cls)
        pq = pq.filter(cls.crawler == crawler)
        pq.delete(synchronize_session=False)

    def __repr__(self):
        return '<Result(%s,%s)>' % (self.crawler, self.next_stage)
