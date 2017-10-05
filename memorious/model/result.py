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
    operation_id = Column(Integer, ForeignKey("operation.id"), nullable=True)
    prev_stage = Column(String, nullable=False, index=True)
    next_stage = Column(String, nullable=False, index=True)
    data = Column(JSON, nullable=False, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def save(cls, crawler, operation_id, prev_stage, next_stage, data):
        obj = cls()
        obj.crawler = crawler.name
        obj.operation_id = operation_id
        obj.prev_stage = prev_stage
        obj.next_stage = next_stage
        obj.data = data
        session.add(obj)
        session.flush()
        return obj

    @classmethod
    def delete(cls, crawler):
        from memorious.model.operation import Operation
        op_ids = session.query(Operation.id)
        op_ids = op_ids.filter(Operation.crawler == crawler)
        pq = session.query(cls)
        pq = pq.filter(cls.operation_id.in_(op_ids.subquery()))
        pq.delete(synchronize_session=False)
        session.flush()

    @classmethod
    def by_crawler_next_stage(cls, crawler, next_stage):
        q = session.query(cls)
        q = q.filter(cls.crawler == crawler)
        q = q.filter(cls.next_stage == next_stage)
        return q

    def __repr__(self):
        return '<Result(%s,%s)>' % (self.crawler, self.next_stage)
