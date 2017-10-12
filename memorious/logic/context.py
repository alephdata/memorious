import os
import six
import uuid
import logging
import traceback
from copy import deepcopy
from datetime import datetime
from contextlib import contextmanager

from memorious.core import manager, storage, celery, session
from memorious.core import datastore
from memorious.model import Result, Tag, Operation, Event
from memorious.exc import StorageFileMissing
from memorious.logic.http import ContextHttp


class Context(object):
    """Provides state tracking and methods for operation interactions."""

    def __init__(self, crawler, stage, state):
        self.crawler = crawler
        self.stage = stage
        self.state = state
        self.params = stage.params
        self.run_id = state.get('run_id') or uuid.uuid1().hex
        self.operation_id = None
        self.log = logging.getLogger('%s.%s' % (crawler.name, stage.name))
        self.http = ContextHttp(self)
        self.datastore = datastore

    def get(self, name, default=None):
        """Get a configuration value and expand environment variables."""
        value = self.params.get(name, default=None)
        if isinstance(value, six.string_types):
            value = os.path.expandvars(value)
        return value

    def emit(self, rule='pass', stage=None, data={}, delay=None):
        """Invoke the next stage, either based on a handling rule, or by calling
        the `pass` rule by default."""
        if stage is None:
            stage = self.stage.handlers.get(rule)
        if stage is None or stage not in self.crawler.stages:
            raise TypeError("Invalid stage: %s (%s)" % (stage, rule))
        state = self.dump_state()
        delay = delay or self.crawler.delay
        Result.save(self.crawler, self.operation_id,
                    self.stage.name, stage, data)
        handle.apply_async((state, stage, data), countdown=delay)

    def recurse(self, data={}, delay=None):
        """Have a stage invoke itself with a modified set of arguments."""
        return self.emit(stage=self.stage.name,
                         data=data,
                         delay=delay)

    def execute(self, data):
        """Execute the crawler and create a database record of having done
        so."""
        op = Operation()
        op.crawler = self.crawler.name
        op.name = self.stage.name
        op.run_id = self.run_id
        op.status = Operation.STATUS_PENDING
        session.add(op)
        session.commit()
        self.operation_id = op.id

        try:
            self.log.debug('Running: %s', op.name)
            res = self.stage.method(self, data)
            op.status = Operation.STATUS_SUCCESS
            return res
        except Exception as exc:
            # this should clear results and tags created by this op
            # TODO: should we also use transactions on the datastore?
            session.rollback()
            self.emit_exception(exc)
        finally:
            if op.status == Operation.STATUS_PENDING:
                op.status = Operation.STATUS_FAILED
            op.ended_at = datetime.utcnow()
            session.add(op)
            session.commit()

    def emit_warning(self, message, type=None, details=None):
        return Event.save(self.operation_id, Event.LEVEL_WARNING,
                          error_type=type,
                          error_message=message,
                          error_details=details)

    def emit_exception(self, exc):
        self.log.exception(exc)
        return Event.save(self.operation_id, Event.LEVEL_ERROR,
                          error_type=exc.__class__.__name__,
                          error_message=unicode(exc),
                          error_details=traceback.format_exc())

    def set_tag(self, key, value, run_id=None):
        return Tag.save(self.crawler, key, value, run_id=run_id)

    def set_run_tag(self, key, value):
        return self.set_tag(key, value, run_id=self.run_id)

    def get_tag(self, key, run_id=None):
        tag = Tag.find(self.crawler, key, run_id=run_id)
        if tag is not None:
            return tag.value

    def get_run_tag(self, key):
        return self.get_tag(key, run_id=self.run_id)

    def check_tag(self, key, run_id=None):
        return Tag.exists(self.crawler, key, run_id=run_id)

    def check_run_tag(self, key):
        return self.check_tag(key, run_id=self.run_id)

    def store_file(self, file_path, content_hash=None):
        """Put a file into permanent storage so it can be visible to other
        stages."""
        return storage.archive_file(file_path, content_hash=content_hash)

    @contextmanager
    def load_file(self, content_hash, file_name=None):
        file_path = storage.load_file(content_hash, file_name=file_name)
        if file_path is None:
            raise StorageFileMissing(content_hash, file_name=file_name)

        try:
            with open(file_path, 'r') as fh:
                yield fh
        finally:
            storage.cleanup_file(content_hash)

    def dump_state(self):
        state = deepcopy(self.state)
        state['crawler'] = self.crawler.name
        state['run_id'] = self.run_id
        return state

    @classmethod
    def from_state(cls, state, stage):
        state_crawler = state.pop('crawler')
        crawler = manager.get(state_crawler)
        if crawler is None:
            raise RuntimeError("Missing crawler: [%s]" % state_crawler)
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
