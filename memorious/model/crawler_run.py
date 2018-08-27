import logging

from memorious.model.common import Base, unpack_int, pack_now
from memorious.util import make_key

log = logging.getLogger(__name__)


class CrawlerRun(Base):
    """The current state of a running crawler instance"""

    @classmethod
    def record_operation_start(cls, crawler, run_id):
        if not cls.conn.sismember(make_key(crawler, "runs"), run_id):
            cls.conn.sadd(make_key(crawler, "runs"), run_id)
            cls.conn.lpush(make_key(crawler, "runs_list"), run_id)
            cls.conn.set(make_key("run", run_id, "start"), pack_now())
        cls.conn.incr(make_key("run", run_id))
        cls.conn.incr(make_key("run", run_id, "total_ops"))

    @classmethod
    def record_operation_end(cls, crawler, run_id):
        pending = cls.conn.decr(make_key("run", run_id))
        if unpack_int(pending) == 0:
            cls.conn.set(make_key("run", run_id, "end"), pack_now())

    @classmethod
    def flush(cls, crawler):
        pipe = cls.conn.pipeline()
        for run_id in cls.conn.smembers(make_key(crawler, "runs")):
            pipe.delete(make_key("run", run_id, "start"))
            pipe.delete(make_key("run", run_id, "end"))
            pipe.delete(make_key("run", run_id, "total_ops"))
            pipe.delete(make_key("run", run_id))
        pipe.delete(make_key(crawler, "runs"))
        pipe.delete(make_key(crawler, "runs_list"))
        pipe.execute()
