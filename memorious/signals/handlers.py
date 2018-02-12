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
        if not r.sismember(crawler_name + ":runs", context.run_id):
            r.sadd(crawler_name + ":runs", context.run_id)
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


def flush_crawler(crawler):
    crawler_name = crawler.name
    if settings.REDIS_HOST:
        r = redis.Redis(connection_pool=redis_pool)
        r.delete(crawler_name)
        r.delete(crawler_name + ":total_ops")
        r.delete(crawler_name + ":last_run")
        for run_id in r.smembers(crawler_name + ":runs"):
            r.delete("run:" + run_id + ":start")
            r.delete("run:" + run_id + ":end")
            r.delete("run:" + run_id + ":total_ops")
            r.delete("run:" + run_id)
        r.delete(crawler_name + ":runs")
        for stage in crawler.stages:
            r.delete(crawler_name + ":" + stage)
    else:
        pass


start_signal = blinker.signal(signals.CRAWLER_RUNNING)
start_signal.connect(log_operation_start)
stop_signal = blinker.signal(signals.CRAWLER_FINISHED)
start_signal.connect(log_operation_finish)
flushed_signal = blinker.signal(signals.CRAWLER_FLUSHED)
flushed_signal.connect(flush_crawler)
