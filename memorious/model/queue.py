import logging

from servicelayer.jobs import JobOp, Progress, Job
from servicelayer.util import unpack_int, load_json, dump_json

from memorious.core import manager, conn

log = logging.getLogger(__name__)


class Queue(object):
    """Manage the execution of tasks in the system."""

    @classmethod
    def tasks(cls):
        stages = list({str(stage) for _, stage in manager.stages})
        while True:
            job_op, data, state = JobOp.get_operation_task(
                conn, stages, timeout=5
            )
            if not job_op:
                continue
            yield (job_op.operation, state, load_json(data))

    @classmethod
    def queue(cls, stage, state, data):
        crawler = state.get('crawler')
        job_op = JobOp(conn, str(stage), state['run_id'], str(crawler))
        job_op.queue_task(dump_json(data), state)

    @classmethod
    def size(cls, crawler):
        """Total operations pending for this crawler"""
        total = 0
        for stage in crawler.stages.keys():
            job_op = JobOp(conn, str(stage), state['run_id'], str(crawler))
            total += unpack_int(job_op.progress.get()['pending'])
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
        Job.remove_dataset(conn, str(crawler))

    @classmethod
    def task_done(cls, crawler, stage, state):
        job_op = JobOp(
            conn, str(stage), str(state['run_id']), str(crawler)
        )
        job_op.task_done()
