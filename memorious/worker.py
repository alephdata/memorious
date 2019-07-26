import logging
from servicelayer.worker import Worker

from memorious.logic.context import Context
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
        context.execute(data)

    def after_task(self, task):
        stage = task.stage.stage
        state = task.context
        context = Context.from_state(state, stage)

        def aggregate(context):
            context.crawler.aggregate(context)

        task.job.execute_if_done(aggregate, context)

    def get_stages(self):
        return list({str(stage) for _, stage in manager.stages})


def get_worker():
    return MemoriousWorker(conn=conn)
