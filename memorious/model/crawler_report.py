import logging
from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.event import listens_for
from sqlalchemy.orm import aliased

from memorious.core import session
from memorious.model.common import Base

from .operation import Operation


log = logging.getLogger(__name__)


class CrawlerReport(Base):
    """Crawler run count and last active info for faster access.

    This table has duplicate data that already exists in Operation table. If in
    conflict, treat the Operation table as the source of truth.
    """
    __tablename__ = 'crawler_report'

    id = Column(Integer, primary_key=True)
    crawler = Column(String, nullable=False, index=True, unique=True)
    op_count = Column(Integer, default=0)
    last_run = Column(DateTime, nullable=False)

    def __repr__(self):
        return '<CrawlerReport(%s,%s,%s,%s)>' % \
            (self.crawler, self.op_count, self.last_run)

    @classmethod
    def sync_crawler_stat(cls):
        """Update the crawler_report table based on current Operation data"""
        op = aliased(Operation)
        q = session.query(
            op.crawler,
            func.count(op.id),
            func.max(op.started_at),
        ).group_by(op.crawler)
        reports = []
        for (name, op_count, last_active) in q:
            q = session.query(cls)
            q = q.filter(cls.crawler == name)
            report = q.first()
            if report is None:
                report = CrawlerReport()
                report.crawler = name
            report.op_count = op_count
            report.last_run = last_active
            reports.append(report)
        session.add_all(reports)
        session.commit()


@listens_for(Operation, "after_insert")
def update_crawler_report(mapper, connection, op):
    """
    Update the report of a crawler when a new operation is added for that
    crawler.
    """
    # TODO:`after_insert` is called in batches. That probably means
    # last_run value can be slightly off if a bunch of operations for a single
    # crawler are quickfired in succession? The margin will be fairly small
    # though. There is a way to turn off batching but that degrades
    # performance.
    q = session.query(CrawlerReport)
    q = q.filter(CrawlerReport.crawler == op.crawler)
    report = q.first()
    crawler_report_table = CrawlerReport.__table__
    if report is None:
        connection.execute(
            crawler_report_table.insert().values({
                "crawler": op.crawler,
                "op_count": 1,
                "last_run": op.started_at
            })
        )
    else:
        connection.execute(
            crawler_report_table.update().
            where(crawler_report_table.c.crawler == op.crawler).
            values({
                "op_count": report.op_count + 1,
                "last_run": op.started_at
            })
        )
