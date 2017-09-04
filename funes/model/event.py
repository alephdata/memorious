import logging
import traceback
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.exc import SQLAlchemyError

from funes.core import session
from funes.model.common import Base

log = logging.getLogger(__name__)


class Event(Base):
    """Document the start time, end time, type and outcome of a given task."""
    __tablename__ = 'event'

    LEVEL_WARNING = 'warning'
    LEVEL_ERROR = 'error'

    id = Column(Integer, primary_key=True)
    crawler = Column(String, nullable=False, index=True)
    run_id = Column(String, nullable=False, index=True)
    level = Column(String, nullable=False, index=True)
    operation = Column(String, nullable=True)
    operation_id = Column(Integer, nullable=False)
    error_type = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    error_details = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def emit(cls, crawler, level=None, run_id=None, operation=None,
             error_type=None, error_message=None, error_details=None, exc=None,
             operation_id=None, timestamp=None):
        """Create an event, possibly based on an exception."""
        if isinstance(exc, SQLAlchemyError):
            log.exception(exc)
            return

        event = cls()
        event.crawler = crawler
        event.run_id = run_id
        event.level = level
        event.operation = operation
        event.operation_id = operation_id
        event.error_type = error_type
        event.error_message = error_message
        event.error_details = error_details
        if exc is not None:
            event.level = event.level or cls.LEVEL_ERROR
            event.error_type = event.error_type or exc.__class__.__name__
            event.error_message = event.error_message or unicode(exc)
            event.error_details = event.error_details or traceback.format_exc()
        session.add(event)
        session.flush()
        return event

    def __repr__(self):
        return '<Event(%s,%s,%s,%s)>' % \
            (self.crawler, self.level, self.operation, self.error_type)
