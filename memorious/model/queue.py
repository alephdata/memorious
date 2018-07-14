import json
import time
import logging
from datetime import datetime, timedelta

from memorious.model.common import Base, pack_datetime, unpack_datetime
from memorious.model.common import unpack_int
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

        return json.dumps(task_data)

    @classmethod
    def next(cls):
        """Get the next task to execute or block.

        Goes over all the queues in a round robin order. Each queue corresponds
        to a crawler stage.
        """
        while True:
            queues = cls.conn.lrange("queues", 0, -1)
            if queues:
                break
            log.info("No queues found. Sleeping for 10 seconds ...")
            time.sleep(10)
        # shift queues around in round-robin manner
        cls.conn.brpoplpush("queues", "queues")
        task_data_tuple = cls.conn.blpop(queues)
        # blpop blocks until it finds something. But fakeredis has no blocking
        # support. So it justs returns None.
        if not task_data_tuple:
            return
        # we only need the data, not the list name
        _, next_task_data = task_data_tuple
        task_data = json.loads(next_task_data)
        stage = task_data["stage"]
        state = task_data["state"]
        data = task_data["data"]
        next_time = task_data.get("next_allowed_exec_time")
        next_time = unpack_datetime(next_time)
        crawler = state.get('crawler')
        cls.conn.decr(make_key('queue_pending', crawler))
        return (stage, state, data, next_time)

    @classmethod
    def tasks(cls):
        while True:
            task = cls.next()
            # Exit when done clause for fakeredis backed runs.
            # In case of actual redis, this condition should never arise
            if not task:
                break
            yield task

    @classmethod
    def queue(cls, stage, state, data, delay=None):
        crawler = state.get('crawler')
        queue_name = make_key('queue', crawler, stage)
        if not cls.conn.sismember("queues_set", queue_name):
            cls.conn.rpush("queues", queue_name)
            cls.conn.sadd("queues_set", queue_name)
        task_data = cls.serialize_task_data(stage, state, data, delay)
        cls.conn.rpush(queue_name, task_data)
        cls.conn.incr(make_key('queue_pending', crawler))
        # log.debug(f"Queues we have now: {cls.conn.lrange('queues', 0, -1)}")

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
    def flush(cls, crawler):
        prefix = make_key('queue', crawler, '*')
        for key in cls.conn.scan_iter(prefix):
            cls.conn.delete(key)
            cls.conn.ltrim(key, 0, -1)
            cls.conn.srem("queues_set", key)
        cls.conn.delete(make_key('queue_pending', crawler))
        cls.cleanup()

    @classmethod
    def cleanup(cls):
        # make sure that queues and queues_set are identical.
        cls.conn.ltrim("queues", 0, -1)
        for queue in cls.conn.sscan("queues_set"):
            cls.conn.rpush("queues", queue)
