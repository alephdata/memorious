import os
import logging
from pkg_resources import iter_entry_points

import redis
import dataset
import storagelayer
from celery import Celery
from celery.schedules import crontab
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.local import LocalProxy
from raven import Client
from raven.contrib.celery import register_signal, register_logger_signal

from memorious import settings
from memorious.logic.queue import CrawlerExecutionQueue


log = logging.getLogger(__name__)

celery = Celery('memorious')
celery.conf.update(
    imports=('memorious.tasks'),
    broker_url=settings.BROKER_URI,
    broker_transport_options={'fanout_prefix': True},
    task_always_eager=settings.EAGER,
    task_eager_propagates=True,
    task_ignore_result=True,
    task_default_queue=settings.APP_NAME,
    task_default_routing_key='%s.process' % settings.APP_NAME,
    result_persistent=False,
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=10,
    # worker_hijack_root_logger=False,
    beat_schedule={
        'scheduled-crawlers': {
            'task': 'memorious.tasks.process_schedule',
            'schedule': crontab(minute='*/30')
        },
        'cleanup-crawlers': {
            'task': 'memorious.tasks.run_cleanup',
            'schedule': crontab(hour='*')
        },
    },
)

redis_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT
)

# set up a task queue using a Queue if celery is set to eager mode.
local_queue = CrawlerExecutionQueue()

# set up raven for error reporting
if settings.SENTRY_DSN:
    client = Client(settings.SENTRY_DSN)
    register_logger_signal(client)
    register_signal(client, ignore_expected=True)


# File storage layer for blobs on local file system or S3
storage = storagelayer.init(settings.ARCHIVE_TYPE,
                            path=settings.ARCHIVE_PATH,
                            aws_key_id=settings.ARCHIVE_AWS_KEY_ID,
                            aws_secret=settings.ARCHIVE_AWS_SECRET,
                            aws_region=settings.ARCHIVE_AWS_REGION,
                            bucket=settings.ARCHIVE_BUCKET)


# Configure the SQLAlechemy database connection engine
engine = create_engine(settings.DATABASE_URI)
session_factory = sessionmaker(bind=engine)
session = scoped_session(session_factory)


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
        settings._datastore = dataset.connect(settings.DATASTORE_URI)
        # Use bigint to store integers by default
        settings._datastore.types.integer = settings._datastore.types.bigint
    return settings._datastore


manager = LocalProxy(load_manager)
datastore = LocalProxy(load_datastore)


def connect_redis():
    if not settings.REDIS_HOST:
        # raise RuntimeError("No $MEMORIOUS_REDIS_HOST is set.")
        return None
    return redis.Redis(connection_pool=redis_pool)


def ensure_db():
    if settings.DATABASE_FILE in settings.DATABASE_URI:
        try:
            os.makedirs(os.path.dirname(settings.DATABASE_FILE))
        except Exception:
            pass
        log.info("Built-in database: %s", settings.DATABASE_URI)
        upgrade_db()


def upgrade_db():
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "memorious:migrate")
    with session.bind.begin() as connection:
        alembic_cfg.attributes['connection'] = connection
        command.upgrade(alembic_cfg, "head")


def load_extensions():
    for ep in iter_entry_points('memorious.plugins'):
        func = ep.load()
        func()


def init_memorious():
    ensure_db()
    load_extensions()
