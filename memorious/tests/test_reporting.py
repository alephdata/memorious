import datetime
import time

from memorious.reporting import log_operation_start, log_operation_end


class TestReporting(object):
    def test_operation_reporting(self, crawler, context):
        log_operation_start(context)
        assert crawler.latest_runid == context.run_id
        assert len(list(crawler.runs)) == 1
        assert crawler.op_count == 1
        assert isinstance(crawler.last_run, datetime.datetime)
        log_operation_end(context)
        crawler.flush()
        assert crawler.op_count == 0
        assert len(list(crawler.runs)) == 0
