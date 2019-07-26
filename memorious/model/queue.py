import logging

from servicelayer.jobs import JobStage, Progress, Job, Task

from memorious.core import conn

log = logging.getLogger(__name__)


class Queue(object):
    """Manage the execution of tasks in the system."""

    @classmethod
    def queue(cls, stage, state, data):
        crawler = state.get('crawler')
        job_stage = JobStage(conn, str(stage), state['run_id'], str(crawler))
        task = Task(job_stage, payload=data, context=state)
        task.queue()

    @classmethod
    def size(cls, crawler):
        """Total operations pending for this crawler"""
        status = Progress.get_dataset_status(conn, str(crawler))
        return status.get('pending')

    @classmethod
    def is_running(cls, crawler):
        """Is the crawler currently running?"""
        if crawler.disabled:
            return False
        return cls.size(crawler) > 0

    @classmethod
    def flush(cls, crawler):
        Job.remove_dataset(conn, str(crawler))
