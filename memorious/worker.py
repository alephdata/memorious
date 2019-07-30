import logging
from servicelayer.worker import Worker

from memorious.logic.context import Context
from memorious.logic.rate_limit import get_rate_limit
from memorious.core import manager, conn

log = logging.getLogger(__name__)


class MemoriousWorker(Worker):

    def handle(self, task):
        data = task.payload
        stage = task.stage.stage
        state = task.context
        context = Context.from_state(state, stage)
        if context.crawler.disabled:
            return
        if context.stage.rate_limit:
            resource = "%s:%s" % (context.crawler.name, context.stage.name)
            rate_limit = get_rate_limit(
                resource, limit=context.stage.rate_limit
            )
            if rate_limit.check():
                context.execute(data)
                rate_limit.update()
            else:
                Queue.queue(stage, state, data)
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
