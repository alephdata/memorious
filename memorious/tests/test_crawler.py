import os

from memorious.logic.manager import Crawler
from memorious.logic.stage import CrawlerStage


class TestCrawler(object):
    def test_crawler(self, crawler_dir, manager):
        source_file = os.path.join(crawler_dir, "simple_web_scraper.yml")
        crawler = Crawler(manager, source_file)
        assert crawler.name == "occrp_web_site"
        assert crawler.schedule == "weekly"
        names = crawler.stages.keys()
        assert set(names) == {"init", "fetch", "parse", "store"}
        stages = crawler.stages.values()
        assert all(isinstance(s, CrawlerStage) for s in stages)

    def test_check_due(self, crawler_dir, manager):
        source_file = os.path.join(crawler_dir, "simple_web_scraper_2.yml")
        crawler = Crawler(manager, source_file)
        assert crawler.schedule == "disabled"
        assert crawler.check_due() == False