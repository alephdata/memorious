import os
import logging
from fnmatch import fnmatch

from memorious import settings
from memorious.logic.crawler import Crawler

log = logging.getLogger(__name__)


class CrawlerManager(object):
    """Crawl a directory of YAML files to load a set of crawler specs."""

    def __init__(self):
        self.crawlers = {}

    def load_path(self, path):
        if not os.path.isdir(path):
            log.warning('Crawler config path %s not found.', path)

        for root, _, file_names in os.walk(path):
            for file_name in file_names:
                if not (fnmatch(file_name, '*.yaml') or fnmatch(file_name, '*.yml')):  # noqa
                    continue
                source_file = os.path.join(root, file_name)
                crawler = Crawler(self, source_file)
                self.crawlers[crawler.name] = crawler

    def run_scheduled(self):
        num_running = self.num_running
        log.info('Checking schedule: %s crawlers.' % len(self.crawlers))
        for crawler in self:
            if crawler.delta is None:
                continue
            if not crawler.check_due():
                continue
            if num_running >= settings.MAX_SCHEDULED:
                continue
            log.info('[%s] due, queueing...', crawler.name)
            crawler.run()
            num_running += 1

    @property
    def num_running(self):
        num = 0
        for crawler in self:
            if crawler.is_running:
                num += 1
        return num

    @property
    def stages(self):
        for crawler in self:
            for stage in crawler:
                yield crawler, stage

    def __getitem__(self, name):
        return self.crawlers.get(name)

    def __iter__(self):
        crawlers = list(self.crawlers.values())
        crawlers.sort(key=lambda c: c.name)
        return iter(crawlers)

    def __len__(self):
        return len(self.crawlers)

    def get(self, name):
        return self.crawlers.get(name)
