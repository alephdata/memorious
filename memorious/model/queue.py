import logging

from servicelayer.jobs import Stage, Job, Dataset

from memorious.core import conn
from memorious.settings import MAX_QUEUE_LENGTH

log = logging.getLogger(__name__)


class Queue(object):
    """Manage the execution of tasks in the system."""

    @classmethod
    def queue(cls, stage, state, data):
        crawler = state.get('crawler')
        job = Job(conn, str(crawler), state['run_id'])
        job_stage = Stage(job, str(stage))
        queue_length = job_stage.get_status().get('pending')
        if queue_length > MAX_QUEUE_LENGTH:
            msg = "queue for %s:%s too big."
            raise QueueTooBigError(msg % (str(crawler), str(stage)))
        job_stage.queue(payload=data, context=state)

    @classmethod
    def size(cls, crawler):
        """Total operations pending for this crawler"""
        dataset = Dataset(conn, str(crawler))
        status = dataset.get_status()
        return status.get('pending')

    @classmethod
    def is_running(cls, crawler):
        """Is the crawler currently running?"""
        if crawler.disabled:
            return False
        dataset = Dataset(conn, str(crawler))
        for job in dataset.get_jobs():
            if not job.is_done():
                return True
        return False

    @classmethod
    def flush(cls, crawler):
        dataset = Dataset(conn, str(crawler))
        dataset.cancel()


class QueueTooBigError(Exception):
    pass
