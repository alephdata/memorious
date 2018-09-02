import logging
from banal import ensure_list

from memorious.model.common import Base, unpack_int, unpack_datetime, pack_now
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
    def run_ids(cls, crawler):
        key = make_key(crawler, "runs")
        return ensure_list(cls.conn.smembers(key))

    @classmethod
    def runs(cls, crawler):
        for run_id in cls.run_ids(crawler):
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
            cls.conn.set(make_key("run", run_id, "start"), pack_now())
        cls.conn.incr(make_key("run", run_id))
        cls.conn.incr(make_key("run", run_id, "total_ops"))
        cls.conn.incr(make_key(crawler, stage))
        cls.conn.incr(make_key(crawler, "total_ops"))
        cls.conn.set(make_key(crawler, "last_run"), pack_now())
        cls.conn.set(make_key(crawler, "current_run"), run_id)

    @classmethod
    def operation_end(cls, crawler, run_id):
        cls.conn.set(make_key(crawler, "last_run"), pack_now())
        pending = cls.conn.decr(make_key("run", run_id))
        if unpack_int(pending) == 0:
            cls.conn.set(make_key("run", run_id, "end"), pack_now())

    @classmethod
    def flush(cls, crawler):
        for stage in crawler.stages:
            cls.conn.delete(make_key(crawler, stage))

        for run_id in cls.run_ids(crawler):
            cls.conn.delete(make_key(crawler, run_id))
            cls.conn.delete(make_key(crawler, run_id, "start"))
            cls.conn.delete(make_key(crawler, run_id, "end"))
            cls.conn.delete(make_key(crawler, run_id, "total_ops"))

        cls.conn.delete(make_key(crawler, "runs"))
        cls.conn.delete(make_key(crawler, "current_run"))
        cls.conn.delete(make_key(crawler, "total_ops"))
        cls.conn.delete(make_key(crawler, "last_run"))
        cls.conn.delete(make_key(crawler, "runs_abort"))

    @classmethod
    def latest_runid(cls, crawler):
        return cls.conn.get(make_key(crawler, "current_run"))

    @classmethod
    def abort_run(cls, crawler, run_id):
        cls.conn.sadd(make_key(crawler, "runs_abort"), run_id)
        if cls.conn.get(make_key("run", run_id, "end")) is None:
            cls.conn.set(make_key("run", run_id, "end"), pack_now())

    @classmethod
    def abort_all(cls, crawler):
        for run_id in cls.run_ids(crawler):
            cls.abort_run(crawler, run_id)

    @classmethod
    def is_aborted(cls, crawler, run_id):
        key = make_key(crawler, "runs_abort")
        return cls.conn.sismember(key, run_id)
