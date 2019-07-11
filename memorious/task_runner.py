import queue
import logging
import threading

from memorious import settings
from memorious.logic.rate_limit import get_rate_limit
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
            if context.crawler.disabled:
                return
            if context.stage.rate_limit:
                resource = "%s:%s" % (context.crawler.name, context.stage.name)
                rate_limit = get_rate_limit(
                    resource, limit=context.stage.rate_limit
                )
                if rate_limit.check():
                    context.execute(data)
                    rate_limit.update()
                else:
                    Queue.queue(stage, state, data)
            else:
                context.execute(data)
        except Exception:
            log.exception("Task failed to execute:")
        finally:
            Queue.task_done(context.crawler, stage, state)
            # If we don't have anymore tasks to execute, time to clean up.
            if not context.crawler.is_running:
                context.crawler.aggregate(context)

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
    def run_sync(cls):
        for task in Queue.tasks(stop_on_timeout=True):
            cls.execute(*task)

    @classmethod
    def run(cls):
        log.info("Processing queue (%s threads)", settings.THREADS)
        q = queue.Queue(maxsize=settings.THREADS)
        threads = []
        for _ in range(settings.THREADS):
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
        for _ in range(settings.THREADS):
            q.put(None)
        for t in threads:
            t.join()
