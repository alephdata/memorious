import logging
from funes.core import store
from funes.context import Context
from funes.tools.schedule import Schedule

log = logging.getLogger(__name__)


def run_scheduled():
    for name, spec in store.crawlers.items():
        schedule = spec.get('schedule')
        if schedule is None:
            log.info('[%s] has no schedule.', name)
            return
        if Schedule.check_due(name, schedule):
            log.info('[%s] due.', name)
            run_crawler(name)
        else:
            log.info('[%s] not due.', name)


def run_crawler(name):
    crawler = store.crawlers.get(name)
    context = Context(name=name, description=crawler.get('description'),
                      params=crawler.get('params'))
    context.log.info('[Initializing]: %s', name)
    context.emit(sender='init')
