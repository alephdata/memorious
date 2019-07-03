import logging

from servicelayer.process import ServiceQueue, Progress

from memorious.core import manager, conn
from memorious.model.common import unpack_int, load_json, dump_json

log = logging.getLogger(__name__)


class Queue(object):
    """Manage the execution of tasks in the system."""

    @classmethod
    def tasks(cls):
        stages = list({str(stage) for _, stage in manager.stages})
        while True:
            queue, data, state = ServiceQueue.get_operation_task(
                conn, stages, timeout=5
            )
            if not queue:
                continue
            yield (queue.operation, state, load_json(data))

    @classmethod
    def queue(cls, stage, state, data):
        crawler = state.get('crawler')
        queue = ServiceQueue(conn, str(stage), state['run_id'], str(crawler))
        queue.queue_task(dump_json(data), state)

    @classmethod
    def size(cls, crawler):
        """Total operations pending for this crawler"""
        total = 0
        for stage in crawler.stages.keys():
            queue = ServiceQueue(conn, str(stage), str(crawler))
            total += unpack_int(queue.progress.get()['pending'])
        return total

    @classmethod
    def is_running(cls, crawler):
        """Is the crawler currently running?"""
        if crawler.disabled:
            return False
        status = Progress.get_dataset_status(conn, str(crawler))
        return status.get('pending') > 0

    @classmethod
    def flush(cls, crawler):
        ServiceQueue.remove_dataset(conn, str(crawler))

    @classmethod
    def task_done(cls, crawler, stage):
        queue = ServiceQueue(
            conn, str(stage), str(stage['run_id']), str(crawler)
        )
        queue.task_done()
