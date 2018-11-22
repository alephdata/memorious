import queue
import random
import logging
import threading
from datetime import datetime

from memorious import settings
from memorious.logic.rate_limit import rate_limiter, RateLimitException
from memorious.logic.context import Context
from memorious.model.queue import Queue

log = logging.getLogger(__name__)


class TaskRunner(object):
    """A long running task runner that uses Redis as a task queue"""

    @classmethod
    def execute(cls, stage, state, data, next_allowed_exec_time=None):
        """Execute the operation, rate limiting allowing."""
        try:
            context = Context.from_state(state, stage)
            now = datetime.utcnow()
            if next_allowed_exec_time and now < next_allowed_exec_time:
                # task not allowed to run yet; put it back in the queue
                Queue.queue(stage, state, data, delay=next_allowed_exec_time)
            elif context.crawler.disabled:
                pass
            elif context.stage.rate_limit:
                try:
                    with rate_limiter(context):
                        context.execute(data)
                except RateLimitException:
                    delay = max(1, 1.0/context.stage.rate_limit)
                    delay = random.randint(1, int(delay))
                    context.log.info(
                        "Rate limit exceeded, delaying %d sec.", delay
                    )
                    Queue.queue(stage, state, data, delay=delay)
            else:
                context.execute(data)
        except Exception:
            log.exception("Task failed to execute:")
        finally:
            # Decrease the pending task count after excuting a task.
            Queue.decr_pending(context.crawler)
            # If we don't have anymore tasks to execute, time to clean up.
            if not context.crawler.is_running:
                context.crawler.cleanup()

    @classmethod
    def process(cls, q):
        while True:
            item = q.get()
            if item is None:
                q.task_done()
                return
            try:
                cls.execute(*item)
            except Exception:
                log.exception("Task failed to execute:")
            q.task_done()

    @classmethod
    def run(cls):
        if settings.DEBUG:
            log.info("DEBUG mode. Disabling task threading.")
            for task in Queue.tasks():
                cls.execute(*task)
            return

        log.info("Processing queue (%s threads)", settings.THREADS)
        q = queue.Queue(maxsize=settings.THREADS)
        threads = []
        for i in range(settings.THREADS):
            t = threading.Thread(target=cls.process, args=(q,))
            t.daemon = True
            t.start()
            threads.append(t)

        while True:
            # This is to handle fakeredis. It terminates the iterator
            # in Queue.tasks() when it "temporarily" runs out of tasks
            # during the execution of the initial task. So we have to
            # restart Queue.tasks() after q.join() to make sure that
            # no child tasks were queued.
            tasks_processed = 0
            for item in Queue.tasks():
                tasks_processed += 1
                q.put(item)

            # block until all tasks are done
            q.join()

            if tasks_processed == 0:
                break

        # stop workers
        for i in range(settings.THREADS):
            q.put(None)
        for t in threads:
            t.join()
