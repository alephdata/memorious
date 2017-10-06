import os
import logging
import dataset
import storagelayer
from celery import Celery
from celery.schedules import crontab
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.local import LocalProxy

from memorious import settings

log = logging.getLogger(__name__)

celery = Celery('memorious')
celery.conf.update(
    imports=('memorious.tasks'),
    broker_url=settings.BROKER_URI,
    broker_transport_options={'fanout_prefix': True},
    task_always_eager=settings.EAGER,
    task_eager_propagates=True,
    task_ignore_result=True,
    result_persistent=False,
    # ultra-high time limit to shoot hung tasks:
    worker_max_tasks_per_child=200,
    worker_hijack_root_logger=False,
    beat_schedule={
        'scheduled-crawlers': {
            'task': 'memorious.tasks.process_schedule',
            'schedule': crontab(minute='*/30')
        },
    },
)

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
        settings._manager = CrawlerManager(settings.CONFIG_PATH)
    return settings._manager


def load_datastore():
    if not hasattr(settings, '_datastore'):
        if not settings.DATASTORE_URI:
            raise RuntimeError("No $MEMORIOUS_DATASTORE_URI.")
        settings._datastore = dataset.connect(settings.DATASTORE_URI)
    return settings._datastore


manager = LocalProxy(load_manager)
datastore = LocalProxy(load_datastore)


def ensure_db():
    if settings.DATABASE_FILE in settings.DATABASE_URI:
        try:
            os.makedirs(os.path.dirname(settings.DATABASE_FILE))
        except:
            pass
        log.info("Built-in database: %s", settings.DATABASE_URI)
        upgrade_db()


def upgrade_db():
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "memorious:migrate")
    with session.bind.begin() as connection:
        alembic_cfg.attributes['connection'] = connection
        command.upgrade(alembic_cfg, "head")
