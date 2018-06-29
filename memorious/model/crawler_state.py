import logging
from datetime import datetime, timedelta

import attr

from memorious.model.common import Base

log = logging.getLogger(__name__)


@attr.s
class CrawlerState(Base):
    """The current state of a running crawler instance"""
    crawler = attr.ib(default=None)

    @classmethod
    def is_running(cls, crawler):
        """Is the crawler currently running?"""
        active_ops = cls.conn.get(crawler.name)
        if active_ops is None:
            return False
        delta = timedelta(seconds=10)
        # current active ops is 0 and there hasn't been any op in last 10 secs
        if int(active_ops) <= 0:
            now = datetime.utcnow()
            if crawler.last_run and (now - crawler.last_run > delta):
                return False
        return True

    @classmethod
    def last_run(cls, crawler):
        last_run = cls.conn.get(crawler.name + ":last_run")
        if last_run:
            return datetime.strptime(last_run, "%Y-%m-%d %H:%M:%S.%f")

    @classmethod
    def op_count(cls, crawler, stage=None):
        """Total operations performed for this crawler"""
        if stage:
            total_ops = cls.conn.get(crawler.name + ":" + stage.name)
        else:
            total_ops = cls.conn.get(crawler.name + ":total_ops")
        if total_ops:
            return int(total_ops)
        return 0

    @classmethod
    def runs(cls, crawler):
        for run_id in cls.conn.lrange(crawler.name + ":runs_list", 0, -1):
            start = cls.conn.get("run:" + run_id + ":start")
            if start:
                start = datetime.strptime(start, "%Y-%m-%d %H:%M:%S.%f")
            else:
                start = None
            end = cls.conn.get("run:" + run_id + ":end")
            if end:
                end = datetime.strptime(end, "%Y-%m-%d %H:%M:%S.%f")
            else:
                end = None
            total_ops = cls.conn.get("run:" + run_id + ":total_ops")
            if total_ops:
                total_ops = int(total_ops)
            else:
                total_ops = 0
            yield {
                'run_id': run_id,
                'total_ops': total_ops,
                'start': start,
                'end': end
            }

    @classmethod
    def cleanup(cls, crawler):
        cls.conn.delete(crawler.name)

    @classmethod
    def record_operation_start(cls, crawler, stage):
        now = datetime.utcnow()
        cls.conn.incr(crawler.name)
        cls.conn.incr(crawler.name + ":" + stage.name)
        cls.conn.incr(crawler.name + ":total_ops")
        cls.conn.set(crawler.name + ":last_run", now)

    @classmethod
    def record_operation_end(cls, crawler):
        cls.conn.decr(crawler.name)

    @classmethod
    def latest_runid(cls, crawler):
        return cls.conn.lindex(crawler.name + ":runs_list", 0)

    @classmethod
    def flush(cls, crawler):
        cls.conn.delete(crawler.name)
        cls.conn.delete(crawler.name + ":total_ops")
        cls.conn.delete(crawler.name + ":last_run")
        for stage in crawler.stages:
            cls.conn.delete(crawler.name + ":" + stage)

    def __repr__(self):
        return '<CrawlerState(%s)>' % (self.crawler)
