import dataset
from funes import settings


def db_connect():
    return dataset.connect(settings.ODS_DATABASE_URI)
