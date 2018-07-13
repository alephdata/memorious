import logging

from memorious.model.common import Base, unpack_int, unpack_datetime, pack_now
from memorious.util import make_key

log = logging.getLogger(__name__)


class CrawlerState(Base):
    """The current state of a running crawler instance"""

    @classmethod
    def is_running(cls, crawler):
        """Is the crawler currently running?"""
        if crawler.disabled:
            return False
        return len(list(cls.conn.scan_iter(f"queue:{crawler.name}:*"))) > 0

    @classmethod
    def last_run(cls, crawler):
        last_run = cls.conn.get(make_key(crawler, "last_run"))
        return unpack_datetime(last_run)

    @classmethod
    def op_count(cls, crawler, stage=None):
        """Total operations performed for this crawler"""
        if stage:
            total_ops = cls.conn.get(make_key(crawler, stage))
        else:
            total_ops = cls.conn.get(make_key(crawler, "total_ops"))
        return unpack_int(total_ops)

    @classmethod
    def runs(cls, crawler):
        for run_id in cls.conn.lrange(make_key(crawler, "runs_list"), 0, -1):
            start = cls.conn.get(make_key("run", run_id, "start"))
            end = cls.conn.get(make_key("run", run_id, "end"))
            total_ops = cls.conn.get(make_key("run", run_id, "total_ops"))
            yield {
                'run_id': run_id,
                'total_ops': unpack_int(total_ops),
                'start': unpack_datetime(start),
                'end': unpack_datetime(end)
            }

    @classmethod
    def cleanup(cls, crawler):
        cls.conn.delete(crawler.name)

    @classmethod
    def record_operation_start(cls, crawler, stage):
        cls.conn.incr(make_key(crawler, stage))
        cls.conn.incr(make_key(crawler, "total_ops"))
        cls.conn.set(make_key(crawler, "last_run"), pack_now())

    @classmethod
    def record_operation_end(cls, crawler):
        cls.conn.set(make_key(crawler, "last_run"), pack_now())

    @classmethod
    def latest_runid(cls, crawler):
        return cls.conn.lindex(make_key(crawler, "runs_list"), 0)

    @classmethod
    def flush(cls, crawler):
        cls.conn.delete(make_key(crawler))
        cls.conn.delete(make_key(crawler, "total_ops"))
        cls.conn.delete(make_key(crawler, "last_run"))
        for stage in crawler.stages:
            cls.conn.delete(make_key(crawler, stage))
