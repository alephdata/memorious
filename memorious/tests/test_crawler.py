import os

from memorious.logic.manager import Crawler
from memorious.logic.stage import CrawlerStage


class TestCrawler(object):
    def test_crawler(self, crawler_dir, manager):
        source_file = os.path.join(crawler_dir, "simple_web_scraper.yml")
        crawler = Crawler(manager, source_file)
        assert crawler.name == "occrp_web_site"
        assert crawler.schedule == "weekly"
        assert set(crawler.stages.keys()) == {"init", "fetch", "parse", "store"}
        assert all(
            isinstance(stage, CrawlerStage) for stage in crawler.stages.values()
        )
