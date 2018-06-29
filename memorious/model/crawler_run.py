import logging
import datetime

import attr

from memorious.model.common import Base

log = logging.getLogger(__name__)


@attr.s
class CrawlerRun(Base):
    """The current state of a running crawler instance"""
    crawler = attr.ib(default=None)
    run_id = attr.ib(default=None)

    @classmethod
    def record_operation_start(cls, crawler, run_id):
        now = datetime.datetime.utcnow()
        if not cls.conn.sismember(crawler.name + ":runs", run_id):
            cls.conn.sadd(crawler.name + ":runs", run_id)
            cls.conn.lpush(crawler.name + ":runs_list", run_id)
            cls.conn.set("run:" + run_id + ":start", now)
        cls.conn.incr("run:" + run_id)
        cls.conn.incr("run:" + run_id + ":total_ops")

    @classmethod
    def record_operation_end(cls, crawler, run_id):
        cls.conn.decr("run:" + run_id)
        if int(cls.conn.get("run:" + run_id)) == 0:
            now = datetime.datetime.utcnow()
            cls.conn.set("run:" + run_id + ":end", now)

    @classmethod
    def flush(cls, crawler):
        for run_id in cls.conn.smembers(crawler.name + ":runs"):
            cls.conn.delete("run:" + run_id + ":start")
            cls.conn.delete("run:" + run_id + ":end")
            cls.conn.delete("run:" + run_id + ":total_ops")
            cls.conn.delete("run:" + run_id)
        cls.conn.delete(crawler.name + ":runs")
        cls.conn.delete(crawler.name + ":runs_list")

    def __repr__(self):
        return '<CrawlerRun(%s, %s)>' % (self.crawler, self.run_id)
