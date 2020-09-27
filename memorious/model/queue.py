import logging
import math

from servicelayer.jobs import Job
from servicelayer.cache import make_key

from memorious.core import conn
from memorious.settings import MAX_QUEUE_LENGTH
from memorious.exc import QueueTooBigError

log = logging.getLogger(__name__)


class Queue(object):
    """Manage the execution of tasks in the system."""

    @classmethod
    def queue(cls, stage, state, data):
        crawler = state.get("crawler")
        job = Job(conn, str(crawler), state["run_id"])
        job_stage = job.get_stage(stage.namespaced_name)
        job_stage.sync()
        queue_length = job_stage.get_status().get("pending")
        if queue_length > MAX_QUEUE_LENGTH:
            msg = "queue for %s:%s too big."
            raise QueueTooBigError(msg % (str(crawler), stage))
        job_stage.queue(payload=data, context=state)

    @classmethod
    def timeout(cls, stage, rate_limit):
        stages_on_timeout = make_key("memorious", "timeout_stages")
        conn.sadd(stages_on_timeout, stage.namespaced_name)
        stage_timeout_key = make_key("memorious", "timeout", stage.namespaced_name)
        expiry = (rate_limit.interval * rate_limit.unit) / rate_limit.limit
        conn.set(stage_timeout_key, "true", ex=math.ceil(expiry))
        # Delay the current task without further adding to call count
        rate_limit.comply(amount=0)
