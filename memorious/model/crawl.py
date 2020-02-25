import logging
from banal import ensure_list
from datetime import datetime

from servicelayer.jobs import Job
from servicelayer.util import unpack_int, unpack_datetime, pack_now
from servicelayer.cache import make_key
from servicelayer.settings import REDIS_LONG

from memorious.core import conn

log = logging.getLogger(__name__)


class Crawl(object):
    """The current state of a running crawler instance"""

    @classmethod
    def last_run(cls, crawler):
        last_run = conn.get(make_key(crawler, "last_run"))
        return unpack_datetime(last_run)

    @classmethod
    def heartbeat(cls, crawler):
        conn.set(make_key(crawler, "last_run"), pack_now())

    @classmethod
    def op_count(cls, crawler, stage=None):
        """Total operations performed for this crawler"""
        if stage:
            total_ops = conn.get(make_key(crawler, stage))
        else:
            total_ops = conn.get(make_key(crawler, "total_ops"))
        return unpack_int(total_ops)

    @classmethod
    def run_ids(cls, crawler):
        key = make_key(crawler, "runs")
        return ensure_list(conn.smembers(key))

    @classmethod
    def runs(cls, crawler):
        runs = []
        for run_id in cls.run_ids(crawler):
            start = conn.get(make_key(crawler, "run", run_id, "start"))
            end = conn.get(make_key(crawler, "run", run_id, "end"))
            total_ops = conn.get(make_key(crawler, "run", run_id, "total_ops"))
            runs.append({
                'run_id': run_id,
                'total_ops': unpack_int(total_ops),
                'start': unpack_datetime(start, datetime.utcnow()),
                'end': unpack_datetime(end)
            })
        return runs

    @classmethod
    def operation_start(cls, crawler, stage, run_id):
        if not conn.sismember(make_key(crawler, "runs"), run_id):
            conn.sadd(make_key(crawler, "runs"), run_id)
            conn.expire(make_key(crawler, "runs"), REDIS_LONG)
            conn.set(make_key(crawler, "run", run_id, "start"), pack_now(), ex=REDIS_LONG)  # noqa
        conn.incr(make_key(crawler, "run", run_id))
        conn.incr(make_key(crawler, "run", run_id, "total_ops"))
        conn.incr(make_key(crawler, stage))
        conn.incr(make_key(crawler, "total_ops"))
        conn.set(make_key(crawler, "last_run"), pack_now(), ex=REDIS_LONG)
        conn.set(make_key(crawler, "current_run"), run_id, ex=REDIS_LONG)

    @classmethod
    def operation_end(cls, crawler, run_id):
        conn.set(make_key(crawler, "last_run"), pack_now(), ex=REDIS_LONG)
        pending = conn.decr(make_key(crawler, "run", run_id))
        if unpack_int(pending) == 0:
            conn.set(make_key(crawler, "run", run_id, "end"), pack_now(), ex=REDIS_LONG)  # noqa

    @classmethod
    def flush(cls, crawler):
        for stage in crawler.stages:
            conn.delete(make_key(crawler, stage))

        for run_id in cls.run_ids(crawler):
            conn.delete(make_key(crawler, run_id))
            conn.delete(make_key(crawler, run_id, "start"))
            conn.delete(make_key(crawler, run_id, "end"))
            conn.delete(make_key(crawler, run_id, "total_ops"))

        conn.delete(make_key(crawler, "runs"))
        conn.delete(make_key(crawler, "current_run"))
        conn.delete(make_key(crawler, "total_ops"))
        conn.delete(make_key(crawler, "last_run"))
        conn.delete(make_key(crawler, "runs_abort"))

    @classmethod
    def latest_runid(cls, crawler):
        return conn.get(make_key(crawler, "current_run"))

    @classmethod
    def abort_run(cls, crawler, run_id):
        conn.sadd(make_key(crawler, "runs_abort"), run_id)
        conn.expire(make_key(crawler, "runs_abort"), REDIS_LONG)
        conn.setnx(make_key(crawler, "run", run_id, "end"), pack_now())
        job = Job(conn, crawler.queue, run_id)
        job.remove()

    @classmethod
    def abort_all(cls, crawler):
        for run_id in cls.run_ids(crawler):
            cls.abort_run(crawler, run_id)

    @classmethod
    def is_aborted(cls, crawler, run_id):
        key = make_key(crawler, "runs_abort")
        return conn.sismember(key, run_id)
