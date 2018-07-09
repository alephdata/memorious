from importlib import import_module

from memorious.model import CrawlerState


class CrawlerStage(object):
    """A single step in a data processing crawler."""

    def __init__(self, crawler, name, config):
        self.crawler = crawler
        self.name = name
        self.config = config
        self.method_name = config.get('method')
        self.params = config.get('params') or {}
        self.handlers = config.get('handle') or {}
        self.rate_limit = None
        if 'rate_limit' in config:
            self.rate_limit = float(config.get('rate_limit'))

    @property
    def method(self):
        method = self.method_name
        package = 'memorious.operations'
        if ':' in method:
            package, method = method.rsplit(':', 1)
        module = import_module(package)
        return getattr(module, method)

    @property
    def op_count(self):
        """Total operations performed for this stage"""
        return CrawlerState.op_count(self.crawler, self)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<CrawlerStage(%r, %s)>' % (self.crawler, self.name)
