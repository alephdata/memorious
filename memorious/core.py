import logging
from pkg_resources import iter_entry_points

import redis
import fakeredis
import dataset
import storagelayer
from sqlalchemy.pool import NullPool
from werkzeug.local import LocalProxy

from memorious import settings


log = logging.getLogger(__name__)


redis_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)

# File storage layer for blobs on local file system or S3
storage = storagelayer.init(settings.ARCHIVE_TYPE,
                            path=settings.ARCHIVE_PATH,
                            aws_key_id=settings.ARCHIVE_AWS_KEY_ID,
                            aws_secret=settings.ARCHIVE_AWS_SECRET,
                            aws_region=settings.ARCHIVE_AWS_REGION,
                            bucket=settings.ARCHIVE_BUCKET)


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


manager = LocalProxy(load_manager)
datastore = LocalProxy(load_datastore)


def connect_redis():
    if not settings.REDIS_HOST:
        return fakeredis.FakeRedis(decode_responses=True)
    return redis.Redis(connection_pool=redis_pool, decode_responses=True)


def load_extensions():
    for ep in iter_entry_points('memorious.plugins'):
        func = ep.load()
        func()


def init_memorious():
    load_extensions()
