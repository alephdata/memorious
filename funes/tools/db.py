import dataset
from funes.core import config


def db_connect():
    return dataset.connect(config.get('locker_database_uri'))
