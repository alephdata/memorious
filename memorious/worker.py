import structlog

from servicelayer.worker import Worker
from servicelayer.logs import apply_task_context

from memorious.logic.context import Context
from memorious.logic.stage import CrawlerStage
from memorious.core import conn, crawler

log = structlog.get_logger(__name__)


class MemoriousWorker(Worker):
    def handle(self, task):
        apply_task_context(task)
        data = task.payload
        stage = CrawlerStage.detach_namespace(task.stage.stage)
        state = task.context
        context = Context.from_state(state, stage)
        context.execute(data)

    def after_task(self, task):
        if task.job.is_done():
            stage = CrawlerStage.detach_namespace(task.stage.stage)
            state = task.context
            context = Context.from_state(state, stage)
            context.crawler.aggregate(context)

    def get_stages(self):
        return [stage.namespaced_name for stage in crawler.stages.values()]


def get_worker(num_threads=None):
    return MemoriousWorker(conn=conn, num_threads=num_threads)
