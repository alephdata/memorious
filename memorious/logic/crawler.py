import yaml
import logging

from datetime import timedelta, datetime

from memorious.core import session
from memorious.model import Tag, Operation
from memorious.logic.context import handle
from memorious.logic.stage import CrawlerStage

log = logging.getLogger(__name__)


class Crawler(object):
    """A processing graph that constitutes a crawler."""
    SCHEDULES = {
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1),
        'monthly': timedelta(weeks=4)
    }

    def __init__(self, manager, source_file):
        self.manager = manager
        self.source_file = source_file
        with open(source_file) as fh:
            self.config = yaml.load(fh)

        self.name = self.config.get('name')
        self.description = self.config.get('description')
        self.schedule = self.config.get('schedule')
        self.init_stage = self.config.get('init', 'init')
        self.delta = Crawler.SCHEDULES.get(self.schedule)
        self.delay = int(self.config.get('delay', 0))

        self.stages = {}
        for name, stage in self.config.get('pipeline', {}).items():
            self.stages[name] = CrawlerStage(self, name, stage)

    def check_due(self):
        if self.delta is None:
            return False
        last_run = Operation.last_run(self.name)
        if last_run is None:
            return True
        now = datetime.now()
        if now > last_run + self.delta:
            return True
        return False

    def flush(self):
        Tag.delete(self.name)
        Operation.delete(self.name)
        session.commit()

    def run(self):
        state = {'crawler': self.name}
        stage = self.get(self.init_stage)
        handle.delay(state, stage.name, {})

    def get(self, name):
        return self.stages.get(name)

    def __repr__(self):
        return '<Crawler(%s)>' % self.name
