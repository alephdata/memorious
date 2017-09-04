import storagelayer
from os import environ
from celery import Celery
from collections import Mapping
from normality import stringify
from celery.schedules import crontab

from funes.store import CrawlerStore


class Config(Mapping):
    """Configuration seings, derived from the OS environment."""

    PREFIX = 'FUNES_'
    ENTRY_POINT = 'funes.crawlers'
    DEFAULTS = {
        'incremental': True,
        'name': 'funes',
        'archive_path': 'data',
        'modules_path': 'modules'
    }

    def __init__(self):
        self.config = self.DEFAULTS

        for key, value in environ.items():
            key = key.upper()
            if not key.startswith(self.PREFIX):
                continue
            key = key[len(self.PREFIX):].lower()
            self.config[key] = value

    def set(self, key, value):
        self.config[key] = value

    def get_bool(self, key, default=False):
        value = stringify(self.get(key))
        if value is None:
            return default
        return value.lower() in ['t', '1', 'y', 'true', 'yes', 'enabled']

    def __getitem__(self, name):
        return self.config.get(name)

    def __iter__(self):
        return iter(self.config)

    def __len__(self):
        return len(self.config)


def get_config():
    if not hasattr(Config, 'instance'):
        Config.instance = Config()
    return Config.instance


def get_session():
    if not hasattr(Config, 'session'):
        from funes.model import create_session
        Config.session = create_session(get_config())
    return Config.session


def get_celery():
    if not hasattr(Config, 'celery'):
        config = get_config()
        app = Celery('funes')
        app.conf.update(
            imports=('funes.tasks'),
            broker_url=config.get('celery_broker_url'),
            broker_transport_options={'fanout_prefix': True},
            result_backend=config.get('celery_result_backend'),
            task_always_eager=config.get_bool('eager'),
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
        Config.celery = app
    return Config.celery

def get_storage():
    if not hasattr(Config, 'storage'):
        config = get_config()
        Config.storage = storagelayer.init(config.get('archive_type'),
                                           path=config.get('archive_path'),
                                           aws_key_id=config.get('archive_aws_key_id'), # noqa
                                           aws_secret=config.get('archive_aws_secret'), # noqa
                                           aws_region=config.get('archive_aws_region'),  # noqa
                                           bucket=config.get('archive_bucket'))
    return Config.storage


def get_crawler_store():
    if not hasattr(Config, 'crawler_store'):
        config = get_config()
        Config.store = CrawlerStore(crawlers_path=config.get('crawlers_path'), # noqa
                                    modules_path=config.get('modules_path'))
    return Config.store


config = get_config()
celery = get_celery()
session = get_session()
storage = get_storage()
store = get_crawler_store()
