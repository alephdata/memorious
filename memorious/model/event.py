import logging
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey

from memorious.core import session
from memorious.model.common import Base

log = logging.getLogger(__name__)


class Event(Base):
    """Document the start time, end time, type and outcome of a given task."""
    __tablename__ = 'event'

    LEVEL_WARNING = 'warning'
    LEVEL_ERROR = 'error'

    id = Column(Integer, primary_key=True)
    level = Column(String, nullable=False, index=True)
    crawler = Column(String, nullable=False, index=True)
    operation_id = Column(Integer, ForeignKey("operation.id"), nullable=False)
    error_type = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    error_details = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def save(cls, crawler, operation_id, level, error_type=None,
             error_message=None, error_details=None):
        """Create an event, possibly based on an exception."""
        event = cls()
        event.crawler = crawler
        event.operation_id = operation_id
        event.level = level
        event.error_type = error_type
        event.error_message = error_message
        event.error_details = error_details
        session.add(event)
        return event

    @classmethod
    def delete(cls, crawler):
        pq = session.query(cls)
        pq = pq.filter(cls.crawler == crawler)
        pq.delete(synchronize_session=False)

    def __repr__(self):
        return '<Event(%s,%s,%s,%s)>' % \
            (self.crawler, self.operation_id, self.error_type, self.level)
