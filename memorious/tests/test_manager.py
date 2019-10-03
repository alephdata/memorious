import os
from collections.abc import Iterable

from memorious.logic.manager import Crawler, CrawlerManager


class TestManager(object):
    def test_manager(self):
        file_path = os.path.realpath(__file__)
        crawler_dir = os.path.normpath(os.path.join(
            file_path, "../testdata/config"
        ))
        manager = CrawlerManager()
        assert len(manager) == 0
        manager.load_path(crawler_dir)
        assert isinstance(manager.crawlers, dict)
        assert all(
            isinstance(crawler, Crawler) for crawler in manager
        )
        assert len(manager) == 3
        assert isinstance(manager.get("book_scraper"), Crawler)
        assert isinstance(manager["book_scraper"], Crawler)
        assert isinstance(manager, Iterable)
