import os
import six
import uuid
import random
import logging
import traceback
from copy import deepcopy
from tempfile import mkstemp
from datetime import datetime, timedelta
from contextlib import contextmanager

from memorious.core import manager, storage, celery, session
from memorious.core import datastore
from memorious.model import Result, Tag, Operation, Event
from memorious.exc import StorageFileMissing
from memorious.logic.http import ContextHttp
from memorious.util import make_key
from memorious import settings


class Context(object):
    """Provides state tracking and methods for operation interactions."""

    def __init__(self, crawler, stage, state):
        self.crawler = crawler
        self.stage = stage
        self.state = state
        self.params = stage.params
        self.incremental = state.get('incremental')
        self.run_id = state.get('run_id') or uuid.uuid1().hex
        self.operation_id = None
        self.log = logging.getLogger('%s.%s' % (crawler.name, stage.name))
        self.http = ContextHttp(self)
        self.datastore = datastore

    def get(self, name, default=None):
        """Get a configuration value and expand environment variables."""
        value = self.params.get(name, default)
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

    def emit_warning(self, message, type=None, details=None, *args):
        if len(args):
            message = message % args
        self.log.warning(message)
        return Event.save(self.crawler.name,
                          self.operation_id,
                          Event.LEVEL_WARNING,
                          error_type=type,
                          error_message=message,
                          error_details=details)

    def emit_exception(self, exc):
        self.log.exception(exc)
        return Event.save(self.crawler.name,
                          self.operation_id,
                          Event.LEVEL_ERROR,
                          error_type=exc.__class__.__name__,
                          error_message=unicode(exc),
                          error_details=traceback.format_exc())

    def set_tag(self, key, value):
        return Tag.save(self.crawler, key, value)

    def get_tag(self, key):
        tag = Tag.find(self.crawler, key)
        if tag is not None:
            return tag.value

    def check_tag(self, key):
        return Tag.exists(self.crawler, key)

    def skip_incremental(self, *criteria):
        """Perform an incremental check on a set of criteria.

        This can be used to execute a part of a crawler only once per an
        interval (which is specified by the ``expire`` setting). If the
        operation has already been performed (and should thus be skipped),
        this will return ``True``. If the operation needs to be executed,
        the returned value will be ``False``.
        """
        if not self.incremental:
            return False

        # this is pure convenience, and will probably backfire at some point.
        key = make_key(*criteria)
        if key is None:
            return False

        # this is used to re-run parts of a scrape after a certain interval,
        # e.g. half a year, or a year
        since = None
        if self.crawler.expire > 0:
            delta = timedelta(days=self.crawler.expire)
            since = datetime.utcnow() - delta

        if Tag.exists(self.crawler, key, since=since):
            return True
        self.set_tag(key, None)
        return False

    def store_file(self, file_path, content_hash=None):
        """Put a file into permanent storage so it can be visible to other
        stages."""
        return storage.archive_file(file_path, content_hash=content_hash)

    def store_data(self, data, encoding='utf-8'):
        """Put the given content into a file, possibly encoding it as UTF-8
        in the process."""
        fd, path = mkstemp()
        try:
            with os.fdopen(fd, 'wb') as fh:
                if isinstance(data, six.text_type):
                    data = data.encode(encoding)
                if data is not None:
                    fh.write(data)
            return self.store_file(path)
        finally:
            os.unlink(path)

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
        state_crawler = state.get('crawler')
        crawler = manager.get(state_crawler)
        if crawler is None:
            raise RuntimeError("Missing crawler: [%s]" % state_crawler)
        stage = crawler.get(stage)
        if stage is None:
            raise RuntimeError('[%r] has no stage: %s' % (crawler, stage))
        return cls(crawler, stage, state)

    def __repr__(self):
        return '<Context(%r, %r)>' % (self.crawler, self.stage)


@celery.task(bind=True, max_retries=None)
def handle(task, state, stage, data):
    """Execute the operation, rate limiting allowing."""
    context = Context.from_state(state, stage)

    if context.stage.rate_limit is not None:
        rate = Operation.check_rate(context.crawler.name,
                                    context.stage.name)
        if rate > context.stage.rate_limit:
            delay = max(10, rate * 120.0)
            delay = random.randint(10, int(delay))
            context.log.info("Rate exceeded [%.2f], delaying %d sec.",
                             rate, delay)
            task.retry(countdown=delay)

    if settings.EAGER:
        # If celery is running in eager mode, put the crawler in a Queue.
        # Then we get to execute them sequentially and avoid recursion errors.
        from memorious.core import task_queue
        task_queue.queue_operation(context, data)
    else:
        context.execute(data)
