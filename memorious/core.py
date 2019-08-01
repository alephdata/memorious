import logging
import dataset
from servicelayer import settings as sls
from servicelayer.archive import init_archive
from servicelayer.rate_limit import RateLimit
from servicelayer.cache import get_redis, get_fakeredis
from servicelayer.extensions import get_extensions
from sqlalchemy.pool import NullPool
from werkzeug.local import LocalProxy

from memorious import settings

log = logging.getLogger(__name__)


def load_manager():
    if not hasattr(settings, '_manager'):
        from memorious.logic.manager import CrawlerManager
        settings._manager = CrawlerManager()
        if settings.CONFIG_PATH:
            settings._manager.load_path(settings.CONFIG_PATH)
    return settings._manager


def load_datastore():
    if not hasattr(settings, '_datastore'):
        if not settings.DATASTORE_URI:
            raise RuntimeError("No $MEMORIOUS_DATASTORE_URI.")
        # do not pool connections for the datastore
        engine_kwargs = {'poolclass': NullPool}
        settings._datastore = dataset.connect(settings.DATASTORE_URI,
                                              engine_kwargs=engine_kwargs)
        # Use bigint to store integers by default
        settings._datastore.types.integer = settings._datastore.types.bigint
    return settings._datastore


def is_sync_mode():
    if settings.TESTING or settings.DEBUG:
        return True
    return sls.REDIS_URL is None


def connect_redis():
    if settings.TESTING:
        return get_fakeredis()
    return get_redis()


manager = LocalProxy(load_manager)
datastore = LocalProxy(load_datastore)
conn = LocalProxy(connect_redis)

# File storage layer for blobs on local file system or S3
storage = init_archive()


def init_memorious():
    for func in get_extensions('memorious.plugins'):
        func()


def get_rate_limit(resource, limit=100, interval=60, unit=1):
    return RateLimit(conn, resource, limit=limit, interval=interval, unit=unit)
