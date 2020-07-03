import logging
from servicelayer.worker import Worker
from servicelayer.cache import make_key

from memorious import settings
from memorious.logic.context import Context
from memorious.logic.stage import CrawlerStage
from memorious.core import manager, conn, get_rate_limit

log = logging.getLogger(__name__)


class MemoriousWorker(Worker):
    def boot(self):
        self.scheduler = get_rate_limit('scheduler',
                                        unit=60,
                                        interval=settings.SCHEDULER_INTERVAL,
                                        limit=1)
        self.hourly = get_rate_limit('hourly', unit=3600, interval=1, limit=1)

    def periodic(self):
        if self.hourly.check():
            self.hourly.update()
            log.info("Running hourly tasks...")
            for crawler in manager:
                if crawler.should_timeout:
                    crawler.timeout()
        if self.scheduler.check() and not settings.DEBUG:
            log.info("Running scheduled crawlers ...")
            self.scheduler.update()
            manager.run_scheduled()
        self.timeout_expiration_check()

    def handle(self, task):
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
        self.timeout_expiration_check()

    def get_stages(self):
        all_stages = set({stage.namespaced_name for _, stage in manager.stages})  # noqa
        stages_on_timeout_key = make_key('memorious', 'timeout_stages')
        stages_on_timeout = conn.smembers(stages_on_timeout_key)
        if stages_on_timeout:
            return list(all_stages - set(stages_on_timeout))
        return all_stages

    def timeout_expiration_check(self):
        stages_on_timeout_key = make_key('memorious', 'timeout_stages')
        stages_on_timeout = conn.smembers(stages_on_timeout_key)
        for stage in stages_on_timeout:
            key = make_key('memorious', 'timeout', stage)
            if not conn.get(key):
                conn.srem(stages_on_timeout_key, stage)


def get_worker():
    return MemoriousWorker(conn=conn)
