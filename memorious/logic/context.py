import os
import uuid
import shutil
import logging
import time
import random
from copy import deepcopy
from tempfile import mkdtemp
from contextlib import contextmanager
from servicelayer.cache import make_key
from servicelayer.util import load_json, dump_json

from memorious.core import manager, storage, tags, datastore
from memorious.model import Queue, Crawl
from memorious.logic.http import ContextHttp
from memorious.logic.check import ContextCheck
from memorious.util import random_filename
from memorious.exc import QueueTooBigError
from memorious import settings


class Context(object):
    """Provides state tracking and methods for operation interactions."""

    def __init__(self, crawler, stage, state):
        self.crawler = crawler
        self.stage = stage
        self.state = state
        self.params = stage.params
        self.incremental = state.get("incremental")
        self.continue_on_error = state.get("continue_on_error")
        self.run_id = state.get("run_id") or uuid.uuid1().hex
        self.work_path = mkdtemp()
        self.log = logging.getLogger("%s.%s" % (crawler.name, stage.name))
        self.http = ContextHttp(self)
        self.datastore = datastore
        self.check = ContextCheck(self)

    def get(self, name, default=None):
        """Get a configuration value and expand environment variables."""
        value = self.params.get(name, default)
        if isinstance(value, str):
            value = os.path.expandvars(value)
        return value

    def emit(self, rule="pass", stage=None, data={}, delay=None, optional=False):
        """Invoke the next stage, either based on a handling rule, or by
        calling the `pass` rule by default."""
        if stage is None:
            stage = self.stage.handlers.get(rule)
        if optional and stage is None:
            return
        if stage is None or stage not in self.crawler.stages:
            self.log.info("No next stage: %s (%s)", stage, rule)
            return
        if settings.DEBUG:
            # sampling rate is a float between 0.0 to 1.0. If it's 0.2, we
            # aim to execute only 20% of the crawler's tasks.
            sampling_rate = self.get("sampling_rate")
            if sampling_rate and random.random() > float(sampling_rate):
                self.log.info("Skipping emit due to sampling rate")
                return
        # In sync mode we use a in-memory backend for the task queue.
        # Make a copy of the data to avoid mutation in that case.
        data = deepcopy(data)
        state = self.dump_state()
        stage = self.crawler.get(stage)
        delay = delay or self.params.get("delay", 0) or self.crawler.delay
        self.sleep(delay)
        Queue.queue(stage, state, data)

    def recurse(self, data=None, delay=None):
        """Have a stage invoke itself with a modified set of arguments."""
        if data is None:
            data = {}
        return self.emit(stage=self.stage.name, data=data, delay=delay)

    def execute(self, data):
        """Execute the crawler and create a database record of having done
        so."""
        if Crawl.is_aborted(self.crawler, self.run_id):
            return

        try:
            Crawl.operation_start(self.crawler, self.stage, self.run_id)
            self.log.info(
                "[%s->%s(%s)]: %s",
                self.crawler.name,
                self.stage.name,
                self.stage.method_name,
                self.run_id,
            )
            return self.stage.method(self, data)
        except QueueTooBigError as qtbe:
            self.emit_warning(str(qtbe))
        except Exception as exc:
            self.emit_exception(exc)
            if not self.continue_on_error:
                raise exc
        finally:
            Crawl.operation_end(self.crawler, self.run_id)
            shutil.rmtree(self.work_path)

    def sleep(self, seconds):
        for sec in range(seconds):
            time.sleep(1)

    def emit_warning(self, message, *args):
        self.log.warning(message, *args)

    def emit_exception(self, exc):
        self.log.exception(exc)

    def set_tag(self, key, value):
        data = dump_json(value)
        key = make_key(self.crawler, "tag", key)
        return tags.set(key, data)

    def get_tag(self, key):
        value = tags.get(make_key(self.crawler, "tag", key))
        if value is not None:
            return load_json(value)

    def check_tag(self, key):
        return tags.exists(make_key(self.crawler, "tag", key))

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
        key = make_key("inc", *criteria)
        if key is None:
            return False

        if self.check_tag(key):
            return True

        self.set_tag(key, "inc")
        return False

    def store_file(self, file_path, content_hash=None):
        """Put a file into permanent storage so it can be visible to other
        stages."""
        return storage.archive_file(file_path, content_hash=content_hash)

    def store_data(self, data, encoding="utf-8"):
        """Put the given content into a file, possibly encoding it as UTF-8
        in the process."""
        path = random_filename(self.work_path)
        try:
            with open(path, "wb") as fh:
                if isinstance(data, str):
                    data = data.encode(encoding)
                if data is not None:
                    fh.write(data)
            return self.store_file(path)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    @contextmanager
    def load_file(self, content_hash, file_name=None, read_mode="rb"):
        file_path = storage.load_file(
            content_hash, file_name=file_name, temp_path=self.work_path
        )
        if file_path is None:
            yield None
        else:
            try:
                with open(file_path, mode=read_mode) as fh:
                    yield fh
            finally:
                storage.cleanup_file(content_hash, temp_path=self.work_path)

    def dump_state(self):
        state = deepcopy(self.state)
        state["crawler"] = self.crawler.name
        state["run_id"] = self.run_id
        return state

    @classmethod
    def from_state(cls, state, stage):
        state_crawler = state.get("crawler")
        crawler = manager.get(state_crawler)
        if crawler is None:
            raise RuntimeError("Missing crawler: [%s]" % state_crawler)
        stage = crawler.get(stage)
        if stage is None:
            raise RuntimeError("[%r] has no stage: %s" % (crawler, stage))
        return cls(crawler, stage, state)

    def enforce_rate_limit(self, rate_limit):
        """
        Enforce rate limit for a resource. If rate limit is exceeded, put the
        offending stage on a timeout (don't execute tasks for that stage for
        some time)
        """
        rate_limit.update()
        if not rate_limit.check():
            Queue.timeout(self.stage, rate_limit=rate_limit)

    def __repr__(self):
        return "<Context(%r, %r)>" % (self.crawler, self.stage)
