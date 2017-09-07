import uuid
import time
import logging
from copy import deepcopy
from contextlib import contextmanager

from funes.core import manager, storage, celery
from funes.tools.http import ContextHttp
from funes.model import Result, Tag


class Context(object):
    """Provides state tracking and methods for operation interactions."""

    def __init__(self, crawler, stage, state):
        self.crawler = crawler
        self.stage = stage
        self.state = state
        self.params = stage.params
        self.run_id = state.get('run_id') or uuid.uuid1().hex
        self.operation_id = None
        self.log = logging.getLogger(crawler.name)
        self.http = ContextHttp(self)

    def dump_state(self):
        state = deepcopy(self.state)
        state['crawler'] = self.crawler.name
        state['run_id'] = self.run_id
        return state

    def emit(self, rule='pass', data={}):
        stage = self.stage.handlers.get(rule)
        if stage is None or stage not in self.crawler.stages:
            raise TypeError("Invalid stage: %s" % stage)
        state = self.dump_state()
        Result.save(self.crawler, self.operation_id,
                    self.stage.name, stage, data)
        time.sleep(self.crawler.delay)
        handle.delay(state, stage, data)

    def execute(self, data):
        self.stage.method(self, data)

    def set_tag(self, key, value):
        return Tag.save(self.crawler, key, value)

    def set_run_tag(self, key, value):
        return Tag.save(self.crawler, key, value, run_id=self.run_id)

    def get_tag(self, key):
        tag = Tag.find(self.crawler, key)
        if tag is not None:
            return tag.value

    def get_run_tag(self, key):
        tag = Tag.find(self.crawler, key, run_id=self.run_id)
        if tag is not None:
            return tag.value

    def check_tag(self, key):
        return Tag.exists(self.crawler, key)

    def check_run_tag(self, key):
        return Tag.exists(self.crawler, key, run_id=self.run_id)

    def store_file(self, file_path, content_hash=None):
        return storage.archive_file(file_path, content_hash=content_hash)

    @contextmanager
    def load_file(self, content_hash, file_name=None):
        file_path = storage.load_file(content_hash, file_name=file_name)
        try:
            with open(file_path, 'r') as fh:
                yield fh
        finally:
            storage.cleanup_file(content_hash)

    @classmethod
    def from_state(cls, state, stage):
        crawler = manager.get(state.pop('crawler'))
        stage = crawler.get(stage)
        if stage is None:
            raise RuntimeError('[%r] has no stage: %s' % (crawler, stage))
        return cls(crawler, stage, state)

    def __repr__(self):
        return '<Context(%r, %r)>' % (self.crawler, self.stage)


@celery.task
def handle(state, stage, data):
    context = Context.from_state(state, stage)
    context.execute(data)
