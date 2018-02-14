import datetime

import blinker

from memorious.signals import signals
from memorious.core import connect_redis


def log_operation_start(context):
    with connect_redis() as conn:
        if conn:
            crawler_name = context.crawler.name
            stage_name = context.stage.name
            conn.incr(crawler_name)
            conn.incr(crawler_name + ":" + stage_name)
            conn.incr(crawler_name + ":total_ops")
            conn.set(crawler_name + ":last_run", datetime.datetime.now())
            if not conn.sismember(crawler_name + ":runs", context.run_id):
                conn.sadd(crawler_name + ":runs", context.run_id)
                conn.set(
                    "run:" + context.run_id + ":start", datetime.datetime.now()
                )
            conn.incr("run:" + context.run_id)
            conn.incr("run:" + context.run_id + ":total_ops")
        else:
            pass


def log_operation_finish(context):
    with connect_redis() as conn:
        if conn:
            crawler_name = context.crawler.name
            conn.decr(crawler_name)
            conn.decr("run:" + context.run_id)
            if conn.get("run:" + context.run_id) == "0":
                conn.set(
                    "run:" + context.run_id + ":end", datetime.datetime.now()
                )
        else:
            pass


def flush_crawler(crawler):
    crawler_name = crawler.name
    with connect_redis() as conn:
        if conn:
            conn.delete(crawler_name)
            conn.delete(crawler_name + ":total_ops")
            conn.delete(crawler_name + ":last_run")
            for run_id in conn.smembers(crawler_name + ":runs"):
                conn.delete("run:" + run_id + ":start")
                conn.delete("run:" + run_id + ":end")
                conn.delete("run:" + run_id + ":total_ops")
                conn.delete("run:" + run_id)
            conn.delete(crawler_name + ":runs")
            for stage in crawler.stages:
                conn.delete(crawler_name + ":" + stage)
        else:
            pass


start_signal = blinker.signal(signals.CRAWLER_RUNNING)
start_signal.connect(log_operation_start)
stop_signal = blinker.signal(signals.CRAWLER_FINISHED)
start_signal.connect(log_operation_finish)
flushed_signal = blinker.signal(signals.CRAWLER_FLUSHED)
flushed_signal.connect(flush_crawler)
