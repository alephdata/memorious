import datetime

from memorious.model import Crawl


class TestReporting(object):

    def test_operation_reporting(self, crawler, context):
        stage = list(crawler.stages)[0]
        Crawl.operation_start(crawler, stage, context.run_id)
        assert crawler.latest_runid == context.run_id
        assert len(list(crawler.runs)) == 1
        assert crawler.op_count == 1
        assert isinstance(crawler.last_run, datetime.datetime)
        Crawl.operation_end(crawler, context.run_id)
        crawler.flush()
        assert crawler.op_count == 0
        assert len(list(crawler.runs)) == 0
