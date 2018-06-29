import datetime

from memorious.reporting import (
    log_operation_start, log_operation_end, flush_crawler
)


class TestReporting(object):
    def test_operation_reporting(self, crawler, context):
        log_operation_start(context)
        assert crawler.latest_runid == context.run_id
        assert crawler.is_running
        assert len(list(crawler.runs)) == 1
        assert crawler.op_count == 1
        assert isinstance(crawler.last_run, datetime.datetime)

        # if crawler hasn't finished running or ran recently, cleanup doesn't
        # do anything
        crawler.cleanup()
        assert crawler.is_running

        log_operation_end(context)
        assert crawler.is_running is False
        crawler.flush()
        flush_crawler(crawler)
        assert crawler.op_count == 0
        assert len(list(crawler.runs)) == 0
