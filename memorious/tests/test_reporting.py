import datetime
import time

from memorious.reporting import log_operation_start, log_operation_end


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
        # wait for 10 seconds
        time.sleep(10)
        assert crawler.is_running is False
        crawler.flush()
        assert crawler.op_count == 0
        assert len(list(crawler.runs)) == 0
