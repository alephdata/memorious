import logging

from servicelayer.jobs import Job

from memorious.core import conn
from memorious.settings import MAX_QUEUE_LENGTH
from memorious.exc import QueueTooBigError

log = logging.getLogger(__name__)


class Queue(object):
    """Manage the execution of tasks in the system."""

    @classmethod
    def queue(cls, stage, state, data):
        crawler = state.get('crawler')
        job = Job(conn, str(crawler), state['run_id'])
        job_stage = job.get_stage(stage)
        job_stage.sync()
        queue_length = job_stage.get_status().get('pending')
        if queue_length > MAX_QUEUE_LENGTH:
            msg = "queue for %s:%s too big."
            raise QueueTooBigError(msg % (str(crawler), stage))
        job_stage.queue(payload=data, context=state)
