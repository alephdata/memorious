import logging
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey

from funes.core import session
from funes.model.common import Base

log = logging.getLogger(__name__)


class Result(Base):
    """A resource that has been retrieved, or that failed to retrieve."""
    __tablename__ = 'result'

    id = Column(Integer, primary_key=True)
    crawler = Column(String, nullable=False, index=True)
    operation_id = Column(Integer, ForeignKey("operation.id"), nullable=True)
    prev_stage = Column(String, nullable=False, index=True)
    next_stage = Column(String, nullable=False, index=True)
    data = Column(JSONB, nullable=False, default={})
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

    def __repr__(self):
        return '<Result(%s,%s)>' % (self.crawler, self.next_stage)
