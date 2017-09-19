from importlib import import_module


class CrawlerStage(object):
    """A single step in a data processing crawler."""

    def __init__(self, crawler, name, config):
        self.crawler = crawler
        self.name = name
        self.config = config
        self.params = config.get('params') or {}
        self.handlers = config.get('handle') or {}

        method = config.get('method')
        package = 'memorious.operations'
        if ':' in method:
            package, method = method.rsplit(':', 1)
        module = import_module(package)
        self.method = getattr(module, method)

    def __repr__(self):
        return '<CrawlerStage(%r, %s)>' % (self.crawler, self.name)
