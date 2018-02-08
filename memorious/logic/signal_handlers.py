import blinker
import redis

from memorious import settings
from memorious.core import redis_pool


def log_operation_start(context):
    if settings.REDIS_HOST:
        r = redis.Redis(connection_pool=redis_pool)
        crawler_name = context.crawler.name
        r.incr(crawler_name)
        r.incr(crawler_name+":total_ops")
    else:
        pass


def log_operation_finish(context):
    if settings.REDIS_HOST:
        r = redis.Redis(connection_pool=redis_pool)
        crawler_name = context.crawler.name
        r.decr(crawler_name)
    else:
        pass


start_signal = blinker.signal("crawler:running")
start_signal.connect(log_operation_start)
stop_signal = blinker.signal("crawler:finished")
start_signal.connect(log_operation_finish)
