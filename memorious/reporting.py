import logging
import datetime

from memorious import settings
from memorious.core import connect_redis
from memorious.signals import operation_start
from memorious.signals import operation_end
from memorious.signals import crawler_flush

log = logging.getLogger(__name__)


def log_operation_start(context):
    conn = connect_redis()
    crawler_name = context.crawler.name
    stage_name = context.stage.name
    now = datetime.datetime.utcnow()
    conn.incr(crawler_name)
    conn.incr(crawler_name + ":" + stage_name)
    conn.incr(crawler_name + ":total_ops")
    conn.set(crawler_name + ":last_run", now)
    if not conn.sismember(crawler_name + ":runs", context.run_id):
        conn.sadd(crawler_name + ":runs", context.run_id)
        conn.set("run:" + context.run_id + ":start", now)
    conn.incr("run:" + context.run_id)
    conn.incr("run:" + context.run_id + ":total_ops")


def log_operation_end(context):
    conn = connect_redis()
    crawler_name = context.crawler.name
    conn.decr(crawler_name)
    conn.decr("run:" + context.run_id)
    if conn.get("run:" + context.run_id) == "0":
        now = datetime.datetime.utcnow()
        conn.set("run:" + context.run_id + ":end", now)


def flush_crawler(crawler):
    conn = connect_redis()
    crawler_name = crawler.name
    conn.delete(crawler_name)
    conn.delete(crawler_name + ":total_ops")
    conn.delete(crawler_name + ":last_run")
    for run_id in conn.smembers(crawler_name + ":runs"):
        run_id = str(run_id)
        conn.delete("run:" + run_id + ":start")
        conn.delete("run:" + run_id + ":end")
        conn.delete("run:" + run_id + ":total_ops")
        conn.delete("run:" + run_id)
    conn.delete(crawler_name + ":runs")
    for stage in crawler.stages:
        conn.delete(crawler_name + ":" + stage)


def init():
    if settings.REDIS_HOST:
        log.info("redis available, configuring reporting...")
        operation_start.connect(log_operation_start)
        operation_end.connect(log_operation_end)
        crawler_flush.connect(flush_crawler)
