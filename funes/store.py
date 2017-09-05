import os
import yaml
import logging
from os import path
from copy import deepcopy
from fnmatch import fnmatch

log = logging.getLogger(__name__)


class CrawlerStore(object):
    """Keeps track of available crawlers and allows access to crawler
       pipeline."""

    DEFAULT_PARAMS = {
        'delay': 0
    }

    def __init__(self, crawlers_path=None, modules_path=None):
        self.crawlers = {}
        self.crawlers_path = crawlers_path
        self.modules_path = modules_path
        for root, dirs, files in os.walk(crawlers_path):
            for fn in files:
                if not fnmatch(fn, '*.yaml'):
                    continue
                with open(path.join(root, fn)) as fh:
                    crawler = yaml.load(fh.read())
                    params = self.DEFAULT_PARAMS.copy()
                    params.update(crawler.get('params'))
                    crawler['params'] = params
                    self.crawlers[crawler.get('name')] = crawler

    def __getitem__(self, key):
        return self.crawlers.get(key)

    def get(self, key):
        return self.crawlers.get(key)

    def rule_target(self, crawler, method_name, rule):
        crawler = self.crawlers.get(crawler)
        pipeline = deepcopy(crawler.get('pipeline'), {})
        method_path = pipeline.get(method_name)
        if method_name != 'init':
            method_path = method_path.get('handle').get(rule)
        if ':' not in method_path:
            method_path = ':'.join([self.modules_path, method_path])
        else:
            method_path = '.'.join([self.crawlers_path, method_path])
        mod_path, method = method_path.split(':')
        try:
            module = __import__(mod_path, globals(), locals(), [''], -1) # noqa
            return getattr(module, method)
        except ImportError:
            log.exception('Method path %s is not valid', method)
            raise
