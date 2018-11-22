import logging
from collections import deque
from datetime import datetime, timedelta

from memorious.core import manager
from memorious.model.common import Base, pack_datetime, unpack_datetime
from memorious.model.common import unpack_int, load_json, dump_json
from memorious.model.common import QUEUE_EXPIRE
from memorious.util import make_key

log = logging.getLogger(__name__)


class Queue(Base):
    """Manage the execution of tasks in the system."""

    @classmethod
    def serialize_task_data(cls, stage, state, data, delay):
        task_data = {}
        task_data["stage"] = stage
        task_data["state"] = state
        task_data["data"] = data
        if delay:
            if isinstance(delay, (int, float)):
                delay = timedelta(seconds=int(delay))

            if isinstance(delay, timedelta):
                delay = datetime.utcnow() + delay

            if isinstance(delay, datetime):
                task_data["next_allowed_exec_time"] = pack_datetime(delay)

        return dump_json(task_data)

    @classmethod
    def tasks(cls):
        queues = [make_key('queue', c, s) for c, s in manager.stages]
        while True:
            task_data_tuple = cls.conn.blpop(queues)
            # blpop blocks until it finds something. But fakeredis has no
            # blocking support. So it justs returns None.
            if not task_data_tuple:
                return

            key, json_data = task_data_tuple
            # Shift the queues list so that the matching key is at the
            # very end of the list, priorising all other crawlers.
            # queues = list(reversed(queues))
            deq = deque(queues)
            deq.rotate((queues.index(key) * -1) - 1)
            queues = list(deq)

            task_data = load_json(json_data)
            stage = task_data["stage"]
            state = task_data["state"]
            data = task_data["data"]
            next_time = task_data.get("next_allowed_exec_time")
            next_time = unpack_datetime(next_time)
            yield (stage, state, data, next_time)

    @classmethod
    def queue(cls, stage, state, data, delay=None):
        crawler = state.get('crawler')
        task_data = cls.serialize_task_data(stage, state, data, delay)
        cls.conn.rpush(make_key('queue', crawler, stage), task_data)
        cls.conn.expire(make_key('queue', crawler, stage), QUEUE_EXPIRE)
        cls.conn.incr(make_key('queue_pending', crawler))

    @classmethod
    def size(cls, crawler):
        """Total operations pending for this crawler"""
        key = make_key('queue_pending', crawler)
        return unpack_int(cls.conn.get(key))

    @classmethod
    def is_running(cls, crawler):
        """Is the crawler currently running?"""
        if crawler.disabled:
            return False
        return cls.size(crawler) > 0

    @classmethod
    def decr_pending(cls, crawler):
        cls.conn.decr(make_key('queue_pending', crawler))

    @classmethod
    def flush(cls, crawler):
        cls.conn.delete(make_key('queue_pending', crawler))
        for name in crawler.stages.keys():
            cls.conn.delete(make_key('queue', crawler, name))
