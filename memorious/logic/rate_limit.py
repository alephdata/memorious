import logging
from servicelayer.process import RateLimit
from memorious.core import conn

log = logging.getLogger(__name__)


def get_rate_limit(resource, limit=100, interval=60, unit=1):
    return RateLimit(conn, resource, limit=limit, interval=interval, unit=unit)
