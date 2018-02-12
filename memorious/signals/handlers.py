import datetime

import blinker
import redis

from memorious import settings
from memorious.signals import signals
from memorious.core import redis_pool


def log_operation_start(context):
    if settings.REDIS_HOST:
        r = redis.Redis(connection_pool=redis_pool)
        crawler_name = context.crawler.name
        stage_name = context.stage.name
        r.incr(crawler_name)
        r.incr(crawler_name + ":" + stage_name)
        r.incr(crawler_name + ":total_ops")
        r.set(crawler_name + ":last_run", datetime.datetime.now())
        if not r.sismember("runs", context.run_id):
            r.sadd("runs", context.run_id)
            r.set("run:" + context.run_id + ":start", datetime.datetime.now())
        r.incr("run:" + context.run_id)
        r.incr("run:" + context.run_id + ":total_ops")
    else:
        pass


def log_operation_finish(context):
    if settings.REDIS_HOST:
        r = redis.Redis(connection_pool=redis_pool)
        crawler_name = context.crawler.name
        r.decr(crawler_name)
        r.decr("run:" + context.run_id)
        if r.get("run:" + context.run_id) == "0":
            r.set("run:" + context.run_id + ":end", datetime.datetime.now())
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
flushed_signal.connect(flush_crawler)
