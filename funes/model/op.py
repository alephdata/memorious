import logging
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime

from funes.core import session
from funes.model.common import Base

log = logging.getLogger(__name__)


class Operation(Base):
    """Document the start time, end time, type and outcome of a given task."""
    __tablename__ = 'operation'

    STATUS_PENDING = 'pending'
    STATUS_FAILED = 'failed'
    STATUS_SUCCESS = 'success'

    SCOPE_RUN = 'run'
    SCOPE_EXIT = 'exit'
    SCOPE_METHOD = 'method'

    id = Column(Integer, primary_key=True)
    crawler = Column(String, nullable=False, index=True)
    run_id = Column(String, nullable=False, index=True)
    scope = Column(String, nullable=False, index=True)
    operation = Column(String, nullable=True)
    status = Column(String, nullable=True, default=STATUS_PENDING)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, default=None)

    def update(self, status):
        self.status = status
        self.ended_at = datetime.utcnow()

    @classmethod
    def last_run(cls, crawler):
        q = session.query(cls)
        q = q.filter(cls.crawler == crawler)
        q = q.order_by(cls.started_at.desc())
        op = q.first()
        if op is None:
            return None
        return op.started_at

    @classmethod
    def last_status(cls, crawler):
        q = session.query(cls)
        q = q.filter(cls.crawler == crawler)
        q = q.order_by(cls.started_at.desc())
        op = q.first()
        if op is None:
            return None
        return op.status

    @classmethod
    def get(cls, **kwargs):
        q = session.query(cls)
        q = q.filter_by(**kwargs)
        return q.all()

    def __repr__(self):
        return '<Operation(%s,%s,%s)>' % \
            (self.crawler, self.operation, self.status)
