import logging

from servicelayer.jobs import JobStage, Progress, Job
from servicelayer.util import load_json, dump_json

from memorious.core import manager, conn

log = logging.getLogger(__name__)


class Queue(object):
    """Manage the execution of tasks in the system."""

    @classmethod
    def tasks(cls, stop_on_timeout=False):
        stages = list({str(stage) for _, stage in manager.stages})
        while True:
            job_stage, data, state = JobStage.get_stage_task(
                conn, stages, timeout=5
            )
            if not job_stage:
                if stop_on_timeout:
                    # Stop if timed out/ no task returned
                    return
                else:
                    continue
            yield (job_stage.operation, state, load_json(data))

    @classmethod
    def queue(cls, stage, state, data):
        crawler = state.get('crawler')
        job_stage = JobStage(conn, str(stage), state['run_id'], str(crawler))
        job_stage.queue_task(dump_json(data), state)

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

    @classmethod
    def task_done(cls, crawler, stage, state):
        job_stage = JobStage(
            conn, str(stage), str(state['run_id']), str(crawler)
        )
        job_stage.task_done()
