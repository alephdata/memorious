import logging
import json
import random
import datetime
import time

from memorious.core import connect_redis
from memorious.logic.rate_limit import rate_limiter, RateLimitException
from memorious.model.common import pack_datetime, unpack_datetime

log = logging.getLogger(__name__)


class TaskRunner(object):
    """A long running task runner that uses Redis as a task queue"""
    conn = connect_redis()

    @classmethod
    def get_queue_name(cls, stage, state):
        return f"queue:{state.get('crawler')}:{stage}"

    @classmethod
    def serialize_task_data(cls, stage, state, data, delay):
        task_data = {}
        task_data["stage"] = stage
        task_data["state"] = state
        task_data["data"] = data
        if delay:
            if isinstance(delay, int):
                task_data["next_allowed_exec_time"] = pack_datetime(
                    datetime.datetime.now() + datetime.timedelta(seconds=delay)
                )
            elif isinstance(delay, datetime.datetime):
                task_data["next_allowed_exec_time"] = pack_datetime(delay)
            elif isinstance(delay, datetime.timedelta):
                task_data["next_allowed_exec_time"] = pack_datetime(
                    datetime.datetime.now() + delay
                )
        return json.dumps(task_data)

    @classmethod
    def deserialize_task_data(cls, task_data):
        task_data = json.loads(task_data)
        stage = task_data["stage"]
        state = task_data["state"]
        data = task_data["data"]
        next_allowed_exec_time = unpack_datetime(
            task_data.get("next_allowed_exec_time")
        )
        return (stage, state, data, next_allowed_exec_time)

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
        next_task = cls.deserialize_task_data(next_task_data)
        return next_task

    @classmethod
    def queue(cls, stage, state, data, delay=None):
        queue_name = cls.get_queue_name(stage, state)
        if not cls.conn.sismember("queues_set", queue_name):
            cls.conn.rpush("queues", queue_name)
            cls.conn.sadd("queues_set", queue_name)
        task_data = cls.serialize_task_data(stage, state, data, delay)
        cls.conn.rpush(queue_name, task_data)
        # log.debug(f"Queues we have now: {cls.conn.lrange('queues', 0, -1)}")

    @classmethod
    def execute(cls, stage, state, data, next_allowed_exec_time=None):
        """Execute the operation, rate limiting allowing."""
        now = datetime.datetime.now()
        if next_allowed_exec_time and now < next_allowed_exec_time:
            # task not allowed to run yet; put it back in the queue
            cls.queue(stage, state, data, delay=next_allowed_exec_time)
            return
        from memorious.logic.context import Context
        context = Context.from_state(state, stage)
        if context.crawler.disabled:
            return

        if context.stage.rate_limit:
            try:
                with rate_limiter(context):
                    context.execute(data)
                    return
            except RateLimitException:
                delay = max(1, 1.0/context.stage.rate_limit)
                delay = random.randint(1, int(delay))
                context.log.info(
                    "Rate limit exceeded, delaying %d sec.", delay
                )
                cls.queue(stage, state, data, delay=delay)
        context.execute(data)

    @classmethod
    def cleanup(cls):
        # make sure that queues and queues_set are identical.
        cls.conn.ltrim("queues", 0, -1)
        for queue in cls.conn.sscan("queues_set"):
            cls.conn.rpush("queues", queue)

    @classmethod
    def run(cls):
        cls.cleanup()
        while True:
            try:
                task = cls.next()
                # Exit when done clause for fakeredis backed runs.
                # In case of actual redis, this condition should never arise
                if not task:
                    break
                cls.execute(*task)
            except Exception as exc:
                log.exception(exc)
