import logging
import random
from datetime import datetime

from memorious.logic.rate_limit import rate_limiter, RateLimitException
from memorious.logic.context import Context
from memorious.model.queue import Queue

log = logging.getLogger(__name__)


class TaskRunner(object):
    """A long running task runner that uses Redis as a task queue"""

    @classmethod
    def execute(cls, stage, state, data, next_allowed_exec_time=None):
        """Execute the operation, rate limiting allowing."""
        now = datetime.utcnow()
        if next_allowed_exec_time and now < next_allowed_exec_time:
            # task not allowed to run yet; put it back in the queue
            Queue.queue(stage, state, data, delay=next_allowed_exec_time)
            return

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
                Queue.queue(stage, state, data, delay=delay)
        context.execute(data)

    @classmethod
    def run(cls):
        Queue.cleanup()
        while True:
            try:
                task = Queue.next()
                # Exit when done clause for fakeredis backed runs.
                # In case of actual redis, this condition should never arise
                if not task:
                    break
                cls.execute(*task)
            except Exception as exc:
                log.exception(exc)
