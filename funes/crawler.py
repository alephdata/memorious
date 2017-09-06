import os
import six
import yaml
import logging
from fnmatch import fnmatch
from importlib import import_module
from datetime import timedelta, datetime

log = logging.getLogger(__name__)


class CrawlerStage(object):
    """A single step in a data processing crawler."""

    def __init__(self, crawler, name, config):
        self.crawler = crawler
        self.name = name
        if isinstance(config, six.string_types):
            config = {'method': config}
        self.config = config
        self.params = config.get('params', {})
        self.handlers = config.get('handle', {})

        method = config.get('method')
        package = 'funes.modules'
        if ':' in method:
            package, method = method.rsplit(':', 1)
        module = import_module(package)
        self.method = getattr(module, method)

    def __repr__(self):
        return '<CrawlerStage(%r, %s)>' % (self.crawler, self.name)


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
        self.init_stage = self.config.get('init')
        self.delta = Crawler.SCHEDULES.get(self.schedule)
        self.delay = int(self.config.get('delay', 0))

        self.stages = {}
        for name, stage in self.config.get('pipeline', {}).items():
            self.stages[name] = CrawlerStage(self, name, stage)

    def check_due(self):
        from funes.model import Operation
        if self.delta is None:
            return False
        last_run = Operation.last_run(self.name)
        if last_run is None:
            return True
        now = datetime.now()
        if now > last_run + self.delta:
            return True
        return False

    def run(self):
        from funes.context import Context
        stage = self.get(self.init_stage)
        context = Context(self, stage, {})
        context.emit(stage=stage.name)

    def get(self, name):
        return self.stages.get(name)

    def __repr__(self):
        return '<Crawler(%s)>' % self.name


class CrawlerManager(object):
    """Crawl a directory of YAML files to load a set of crawler specs."""

    def __init__(self, path):
        self.path = path

        self.crawlers = {}
        for root, _, file_names in os.walk(self.path):
            for file_name in file_names:
                if not fnmatch(file_name, '*.yaml'):
                    continue
                source_file = os.path.join(root, file_name)
                crawler = Crawler(self, source_file)
                self.crawlers[crawler.name] = crawler

    def run_scheduled(self):
        for crawler in self:
            if crawler.delta is None:
                log.info('[%s] has no schedule.', crawler.name)
                return
            if crawler.check_due():
                log.info('[%s] due.', crawler.name)
                crawler.run()
            else:
                log.info('[%s] not due.', crawler.name)

    def __getitem__(self, name):
        return self.crawlers.get(name)

    def __iter__(self):
        return iter(self.crawlers.values())

    def get(self, name):
        return self.crawlers.get(name)
