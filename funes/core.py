import storagelayer
from celery import Celery
from celery.schedules import crontab
from werkzeug.local import LocalProxy

from funes import settings
from funes.store import CrawlerStore

celery = Celery('funes')
celery.conf.update(
    imports=('funes.tasks'),
    broker_url=settings.BROKER_URI,
    broker_transport_options={'fanout_prefix': True},
    task_always_eager=settings.ALWAYS_EAGER,
    task_eager_propagates=True,
    # task_ignore_result=True,
    result_persistent=False,
    # ultra-high time limit to shoot hung tasks:
    worker_max_tasks_per_child=200,
    worker_hijack_root_logger=False,
    beat_schedule={
        'scheduled-crawlers': {
            'task': 'funes.task.process_schedule',
            'schedule': crontab(minute='*/1')
        },
    },
)

storage = storagelayer.init(settings.ARCHIVE_TYPE,
                            path=settings.ARCHIVE_PATH,
                            aws_key_id=settings.ARCHIVE_AWS_KEY_ID,
                            aws_secret=settings.ARCHIVE_AWS_SECRET,
                            aws_region=settings.ARCHIVE_AWS_REGION,
                            bucket=settings.ARCHIVE_BUCKET)


store = CrawlerStore(crawlers_path=settings.CRAWLERS_PATH, # noqa
                     modules_path=settings.MODULES_PATH)


def get_session():
    if not hasattr(settings, '_session'):
        from funes.model.common import create_session
        settings._session = create_session()
    return settings._session


session = LocalProxy(get_session)
