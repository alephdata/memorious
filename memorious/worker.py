import logging
from servicelayer.worker import Worker

from memorious import settings
from memorious.logic.context import Context
from memorious.core import manager, conn, get_rate_limit

log = logging.getLogger(__name__)


class MemoriousWorker(Worker):

    def periodic(self):
        rate_limit = get_rate_limit('scheduler', unit=60, interval=10, limit=1)
        if rate_limit.check() and not settings.DEBUG:
            manager.run_scheduled()
            rate_limit.update()

    def handle(self, task):
        data = task.payload
        stage = task.stage.stage
        state = task.context
        context = Context.from_state(state, stage)
        if context.crawler.disabled:
            return
        context.execute(data)

    def after_task(self, task):
        stage = task.stage.stage
        state = task.context
        context = Context.from_state(state, stage)
        if task.job.is_done():
            context.crawler.aggregate(context)

    def get_stages(self):
        return list({str(stage) for _, stage in manager.stages})


def get_worker():
    return MemoriousWorker(conn=conn)
