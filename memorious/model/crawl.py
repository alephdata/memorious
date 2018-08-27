import logging

from memorious.model.common import Base, unpack_int, unpack_datetime, pack_now
from memorious.model.common import delete_prefix
from memorious.util import make_key

log = logging.getLogger(__name__)


class Crawl(Base):
    """The current state of a running crawler instance"""

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
    def operation_start(cls, crawler, stage, run_id):
        if not cls.conn.sismember(make_key(crawler, "runs"), run_id):
            cls.conn.sadd(make_key(crawler, "runs"), run_id)
            cls.conn.lpush(make_key(crawler, "runs_list"), run_id)
            cls.conn.set(make_key("run", run_id, "start"), pack_now())
        cls.conn.incr(make_key("run", run_id))
        cls.conn.incr(make_key("run", run_id, "total_ops"))
        cls.conn.incr(make_key(crawler, stage))
        cls.conn.incr(make_key(crawler, "total_ops"))
        cls.conn.set(make_key(crawler, "last_run"), pack_now())

    @classmethod
    def operation_end(cls, crawler, run_id):
        cls.conn.set(make_key(crawler, "last_run"), pack_now())
        pending = cls.conn.decr(make_key("run", run_id))
        if unpack_int(pending) == 0:
            cls.conn.set(make_key("run", run_id, "end"), pack_now())

    @classmethod
    def flush(cls, crawler):
        cls.conn.delete(make_key(crawler, "runs"))
        cls.conn.delete(make_key(crawler, "runs_list"))
        cls.conn.delete(make_key(crawler, "total_ops"))
        cls.conn.delete(make_key(crawler, "last_run"))
        # cls.conn.delete(make_key(crawler, "runs_abort"))

        for stage in crawler.stages:
            cls.conn.delete(make_key(crawler, stage))

        runs = cls.conn.smembers(make_key(crawler, "runs"))
        for run_id in runs:
            delete_prefix(cls.conn, make_key("run", run_id, "*"))

    @classmethod
    def latest_runid(cls, crawler):
        return cls.conn.lindex(make_key(crawler, "runs_list"), 0)

    @classmethod
    def abort_run(cls, crawler, run_id):
        cls.conn.sadd(make_key(crawler, "runs_abort"), run_id)
        end_key = make_key("run", run_id, "end")
        if cls.conn.get(end_key) is None:
            cls.conn.set(end_key, pack_now())

    @classmethod
    def abort_all(cls, crawler):
        runs = cls.conn.smembers(make_key(crawler, "runs"))
        if runs:
            cls.conn.sadd(make_key(crawler, "runs_abort"), *runs)

    @classmethod
    def is_aborted(cls, crawler, run_id):
        key = make_key(crawler, "runs_abort")
        return cls.conn.sismember(key, run_id)
