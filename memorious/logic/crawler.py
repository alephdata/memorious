import os
import io
import yaml
import logging
import time
from datetime import timedelta, datetime

from memorious import settings, signals
from memorious.core import session, local_queue, connect_redis
from memorious.model import Tag, Event, Result
from memorious.logic.context import handle
from memorious.logic.stage import CrawlerStage

log = logging.getLogger(__name__)


class Crawler(object):
    """A processing graph that constitutes a crawler."""
    SCHEDULES = {
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1),
        'monthly': timedelta(weeks=4)
    }

    def __init__(self, manager, source_file):
        self.manager = manager
        self.source_file = source_file
        with io.open(source_file, encoding='utf-8') as fh:
            self.config_yaml = fh.read()
            self.config = yaml.load(self.config_yaml)

        self.name = os.path.basename(source_file)
        self.name = self.config.get('name', self.name)
        self.description = self.config.get('description', self.name)
        self.category = self.config.get('category', 'scrape')
        self.schedule = self.config.get('schedule')
        self.disabled = self.config.get('disabled', False)
        self.init_stage = self.config.get('init', 'init')
        self.delta = Crawler.SCHEDULES.get(self.schedule)
        self.delay = int(self.config.get('delay', 0))
        self.expire = int(self.config.get('expire', settings.EXPIRE))
        self.stealthy = self.config.get('stealthy', False)

        self.stages = {}
        for name, stage in self.config.get('pipeline', {}).items():
            self.stages[name] = CrawlerStage(self, name, stage)

    def check_due(self):
        """Check if the last execution of this crawler is older than
        the scheduled interval."""
        if self.disabled:
            return False
        if self.delta is None:
            return False
        last_run = self.last_run
        if last_run is None:
            return True
        now = datetime.utcnow()
        if now > last_run + self.delta:
            return True
        return False

    def flush(self):
        """Delete all run-time data generated by this crawler."""
        Tag.delete(self.name)
        Event.delete(self.name)
        Result.delete(self.name)
        session.commit()
        signals.crawler_flush.send(self)

    def run(self, incremental=None, run_id=None):
        """Queue the execution of a particular crawler."""
        state = {
            'crawler': self.name,
            'run_id': run_id,
            'incremental': settings.INCREMENTAL
        }
        if incremental is not None:
            state['incremental'] = incremental

        # Run the first task straight so that scheduled runs aren't summed
        # up when queue runs get longer.
        stage = self.get(self.init_stage)
        handle(state, stage.name, {})

        # If running in eager mode, we need to block until all the queued
        # tasks are finished.
        while not local_queue.is_empty:
            time.sleep(1)

    @property
    def is_running(self):
        """Is the crawler currently running?"""
        conn = connect_redis()
        if conn is None or self.disabled:
            return False
        active_ops = conn.get(self.name)
        return active_ops and int(active_ops) > 0

    @property
    def last_run(self):
        conn = connect_redis()
        if conn is None:
            return Tag.latest(self.name)

        last_run = conn.get(self.name+":last_run")
        return datetime.strptime(last_run, "%Y-%m-%d %H:%M:%S.%f")

    @property
    def op_count(self):
        """Total operations performed for this crawler"""
        conn = connect_redis()
        if conn is None:
            return None
        total_ops = conn.get(self.name+":total_ops")
        if total_ops:
            return int(total_ops)

    @property
    def runs(self):
        conn = connect_redis()
        if conn is None:
            return
        for run_id in conn.smembers(self.name + ":runs"):
            run_id = str(run_id)
            yield {
                'run_id': run_id,
                'total_ops': conn.get("run:" + run_id + ":total_ops"),
                'start': datetime.strptime(
                    conn.get("run:" + run_id + ":start"), "%Y-%m-%d %H:%M:%S.%f"
                ),
                'end': datetime.strptime(
                    conn.get("run:" + run_id + ":end"), "%Y-%m-%d %H:%M:%S.%f"
                )
            }

    def cleanup(self):
        """Run a cleanup method after the crawler finishes running"""
        if self.is_running:
            # Run cleanup if the last operation of the crawler was more than
            # half a day ago and it's just hanging in running state since.
            delta = timedelta(hours=12)
            timeout = datetime.utcnow() - delta
            last_run = self.last_run
            if last_run is None or last_run > timeout:
                return

        conn = connect_redis()
        if conn is not None:
            conn.delete(self.name)

    def get(self, name):
        return self.stages.get(name)

    def __iter__(self):
        return iter(self.stages.values())

    def __repr__(self):
        return '<Crawler(%s)>' % self.name
