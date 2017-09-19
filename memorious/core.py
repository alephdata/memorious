import storagelayer
from celery import Celery
from celery.schedules import crontab
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.local import LocalProxy

from funes import settings

celery = Celery('funes')
celery.conf.update(
    imports=('funes.tasks'),
    broker_url=settings.BROKER_URI,
    broker_transport_options={'fanout_prefix': True},
    task_always_eager=settings.EAGER,
    task_eager_propagates=True,
    # task_ignore_result=True,
    result_persistent=False,
    # ultra-high time limit to shoot hung tasks:
    worker_max_tasks_per_child=200,
    worker_hijack_root_logger=False,
    beat_schedule={
        'scheduled-crawlers': {
            'task': 'funes.tasks.process_schedule',
            'schedule': crontab(minute='*/1')
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
        from funes.crawler import CrawlerManager
        settings._manager = CrawlerManager(settings.CRAWLERS_PATH)
    return settings._manager


manager = LocalProxy(load_manager)
