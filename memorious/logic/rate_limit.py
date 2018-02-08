import logging
import threading
import contextlib
import datetime

import redis
from redis_rate_limit import RateLimit, TooManyRequests

from memorious.settings import REDIS_HOST, REDIS_PORT

log = logging.getLogger(__name__)
lock = threading.RLock()
global_call_log = {}


class RateLimitException(Exception):
    pass


@contextlib.contextmanager
def rate_limiter(context):
    resource = "%s:%s" % (context.crawler.name, context.stage.name)
    rate_limit = context.stage.rate_limit
    if REDIS_HOST:
        pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT)
        try:
            with RateLimit(resource=resource, client='memorious',
                           max_requests=rate_limit, redis_pool=pool):
                yield
        except TooManyRequests:
            raise RateLimitException
    else:
        if resource in global_call_log:
            last_called = global_call_log[resource]
            diff = (datetime.datetime.now() - last_called).total_seconds()
            if diff < (1.0/rate_limit):
                raise RateLimitException
        global_call_log[resource] = datetime.datetime.now()
        yield

