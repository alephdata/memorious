import logging
from datetime import timedelta, datetime

from funes.model.op import Operation

log = logging.getLogger(__name__)


class Schedule(object):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'

    def __init__(self, name, schedule):
        self.name = name

    @classmethod
    def check_due(cls, crawler, schedule):
        last_run = Operation.last_run(crawler)
        if last_run is None:
            return True
        now = datetime.now()
        delta = cls.calc_delta(schedule)
        if now > last_run + delta:
            return True
        return False

    @classmethod
    def calc_delta(cls, schedule):
        delta = None
        if schedule == cls.DAILY:
            delta = timedelta(days=1)
        elif schedule == cls.WEEKLY:
            delta = timedelta(weeks=1)
        elif schedule == cls.MONTHLY:
            delta = timedelta(weeks=4)
        return delta

    def __unicode__(self):
        return self.name.upper()
