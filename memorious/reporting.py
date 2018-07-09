import logging

from memorious.model import CrawlerState, CrawlerRun
from memorious.signals import operation_start
from memorious.signals import operation_end

log = logging.getLogger(__name__)


def log_operation_start(context):
    crawler = context.crawler
    stage = context.stage
    run_id = context.run_id
    CrawlerState.record_operation_start(crawler, stage)
    CrawlerRun.record_operation_start(crawler, run_id)


def log_operation_end(context):
    crawler = context.crawler
    run_id = context.run_id
    CrawlerState.record_operation_end(crawler)
    CrawlerRun.record_operation_end(crawler, run_id)


def init():
    operation_start.connect(log_operation_start)
    operation_end.connect(log_operation_end)
