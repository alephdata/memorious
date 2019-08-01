import logging
from servicelayer.worker import Worker

from memorious import settings
from memorious.logic.context import Context
from memorious.core import manager, conn, get_rate_limit

log = logging.getLogger(__name__)


class MemoriousWorker(Worker):
    def boot(self):
        self.scheduler = get_rate_limit('scheduler',
                                        unit=60,
                                        interval=settings.SCHEDULER_INTERVAL,
                                        limit=1)

    def periodic(self):
        if self.scheduler.check() and not settings.DEBUG:
            log.info("Running scheduled crawlers ...")
            self.scheduler.update()
            manager.run_scheduled()

    def handle(self, task):
        data = task.payload
        stage = task.stage.stage
        state = task.context
        context = Context.from_state(state, stage)
        if context.crawler.disabled:
            return
        context.execute(data)

    def after_task(self, task):
        if task.job.is_done():
            stage = task.stage.stage
            state = task.context
            context = Context.from_state(state, stage)
            context.crawler.aggregate(context)

    def get_stages(self):
        return list({str(stage) for _, stage in manager.stages})


def get_worker():
    return MemoriousWorker(conn=conn)
