import dataset
from memorious import settings


def db_connect():
    return dataset.connect(settings.ODS_DATABASE_URI)
