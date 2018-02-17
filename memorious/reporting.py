import logging
import datetime

import redis

from memorious import settings
from memorious.core import redis_pool
from memorious.signals import operation_start
from memorious.signals import operation_end
from memorious.signals import crawler_flush
from memorious.helpers.dates import parse_date

log = logging.getLogger(__name__)


def connect_redis():
    if not settings.REDIS_HOST:
        raise RuntimeError("No $MEMORIOUS_REDIS_HOST is set.")
    return redis.Redis(connection_pool=redis_pool)


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
        conn.delete("run:" + run_id + ":start")
        conn.delete("run:" + run_id + ":end")
        conn.delete("run:" + run_id + ":total_ops")
        conn.delete("run:" + run_id)
    conn.delete(crawler_name + ":runs")
    for stage in crawler.stages:
        conn.delete(crawler_name + ":" + stage)


def get_last_run(crawler):
    if not settings.REDIS_HOST:
        return None
    conn = connect_redis()
    last_run = conn.get(crawler.name+":last_run")
    if last_run:
        return parse_date(last_run)


def get_crawler_op_count(crawler):
    """Total operations performed for this crawler"""
    if not settings.REDIS_HOST:
        return None
    conn = connect_redis()
    total_ops = conn.get(crawler.name+":total_ops")
    if total_ops:
        return int(total_ops)


def get_stage_op_count(self):
    """Total operations performed for this stage"""
    if not settings.REDIS_HOST:
        return None
    conn = connect_redis()
    total_ops = conn.get(self.crawler.name + ":" + self.name)
    if total_ops:
        return int(total_ops)


def is_running(crawler):
    """Is the crawler currently running?"""
    if not settings.REDIS_HOST:
        return False
    conn = connect_redis()
    active_ops = conn.get(crawler.name)
    if active_ops and int(active_ops) > 0:
        return True
    return False


def get_crawler_runs(crawler):
    if not settings.REDIS_HOST:
        return []
    conn = connect_redis()
    runs = []
    for run_id in conn.smembers(crawler.name + ":runs"):
        runs.append({
            'run_id': run_id,
            'total_ops': conn.get("run:" + run_id + ":total_ops"),
            'start': parse_date(conn.get("run:" + run_id + ":start")),
            'end': parse_date(conn.get("run:" + run_id + ":end"))
        })
    return runs


def init():
    if settings.REDIS_HOST:
        log.info("redis available, configuring reporting...")
        operation_start.connect(log_operation_start)
        operation_end.connect(log_operation_end)
        crawler_flush.connect(flush_crawler)
