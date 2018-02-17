import logging
import contextlib
import datetime

from redis_rate_limit import RateLimit, TooManyRequests

from memorious import settings
from memorious.core import redis_pool
from memorious.exc import RateLimitException

log = logging.getLogger(__name__)
global_call_log = {}


@contextlib.contextmanager
def rate_limiter(context):
    resource = "%s:%s" % (context.crawler.name, context.stage.name)
    rate_limit = context.stage.rate_limit
    if settings.REDIS_HOST:
        try:
            with RateLimit(resource=resource,
                           client='memorious',
                           max_requests=rate_limit,
                           redis_pool=redis_pool):
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
