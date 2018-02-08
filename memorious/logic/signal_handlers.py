import datetime

import blinker
import redis

from memorious import settings, signals
from memorious.core import redis_pool


def log_operation_start(context):
    if settings.REDIS_HOST:
        r = redis.Redis(connection_pool=redis_pool)
        crawler_name = context.crawler.name
        r.incr(crawler_name)
        r.incr(crawler_name + ":total_ops")
        r.set(crawler_name + ":last_run", datetime.datetime.now())
    else:
        pass


def log_operation_finish(context):
    if settings.REDIS_HOST:
        r = redis.Redis(connection_pool=redis_pool)
        crawler_name = context.crawler.name
        r.decr(crawler_name)
    else:
        pass


def flush_crawler(crawler_name):
    if settings.REDIS_HOST:
        r = redis.Redis(connection_pool=redis_pool)
        r.delete(crawler_name)
        r.delete(crawler_name + ":total_ops")
        r.delete(crawler_name + ":last_run")
    else:
        pass


start_signal = blinker.signal(signals.CRAWLER_RUNNING)
start_signal.connect(log_operation_start)
stop_signal = blinker.signal(signals.CRAWLER_FINISHED)
start_signal.connect(log_operation_finish)
flushed_signal = blinker.signal(signals.CRAWLER_FLUSHED)
flushed_signal.send(flush_crawler)
