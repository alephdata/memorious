import os
import logging
from fnmatch import fnmatch

from memorious.logic.crawler import Crawler

log = logging.getLogger(__name__)


class CrawlerManager(object):
    """Crawl a directory of YAML files to load a set of crawler specs."""

    def __init__(self):
        self.crawlers = {}

    def load_path(self, path):
        if not os.path.isdir(path):
            log.warning("Crawler config path %s not found.", path)

        for root, _, file_names in os.walk(path):
            for file_name in file_names:
                if not (
                    fnmatch(file_name, "*.yaml") or fnmatch(file_name, "*.yml")
                ):  # noqa
                    continue
                source_file = os.path.join(root, file_name)
                try:
                    crawler = Crawler(self, source_file)
                except ValueError:
                    log.exception(
                        "Skipping %s due to the following error", file_name
                    )  # noqa
                    continue
                self.crawlers[crawler.name] = crawler

    def load_crawler(self, path):
        if path.is_file():
            if fnmatch(path.name, "*.yaml") or fnmatch(path.name, "*.yml"):
                try:
                    crawler = Crawler(self, path)
                    self.crawlers[crawler.name] = crawler
                    return crawler
                except ValueError:
                    log.exception(
                        "Could not load crawler %s due to the following error",
                        path.name,
                    )
            log.warning("Crawler path %s is not a yaml file", path)
        else:
            log.warning("Crawler path %s is not a valid file path", path)

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
