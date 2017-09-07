import uuid
import json
import time
import pickle
import logging
from lxml import html
from copy import deepcopy
from datetime import datetime
from urlparse import urlparse
from requests import Session, Request

from funes import settings
from funes.core import manager
from funes.core import celery, session
from funes.model.result import HTTPResult
from funes.tools.util import normalize_url
from funes.tools.results import find_http_results
from funes.tools.files import save_to_temp, guess_fh_encoding


class Context(object):
    """Provides state tracking and methods for operation interactions."""

    def __init__(self, crawler, stage, state):
        self.crawler = crawler
        self.stage = stage
        self.state = state
        self.params = stage.params
        self.run_id = state.get('run_id') or uuid.uuid1().hex
        self.operation_id = None

        self._session = state.pop('session', None)
        if self._session is not None:
            self._session = pickle.loads(self._session)

    @classmethod
    def from_state(cls, state, stage):
        crawler = manager.get(state.pop('crawler'))
        stage = crawler.get(stage)
        if stage is None:
            raise RuntimeError('[%r] has no stage: %s' % (crawler, stage))
        return cls(crawler, stage, state)

    @property
    def session(self):
        if self._session is None:
            self.new_session()
        return self._session

    @session.setter
    def session(self, s):
        self._session = s

    def new_session(self):
        self._session = Session()

    @property
    def log(self):
        if not hasattr(self, '_log'):
            log_name = '[%s] %s' % (self.run_id, self.crawler.name)
            self._log = logging.getLogger(log_name)
        return self._log

    def dump_state(self):
        state = deepcopy(self.state)
        state['crawler'] = self.crawler.name
        state['run_id'] = self.run_id
        if self._session is not None:
            state['session'] = pickle.dumps(self._session)
        return state

    def emit(self, rule='pass', data={}):
        stage = self.stage.handlers.get(rule)
        if stage is None or stage not in self.crawler.stages:
            raise TypeError("Invalid stage: %s" % stage)
        state = self.dump_state()
        time.sleep(self.crawler.delay)
        handle.delay(state, stage, data)

    def execute(self, data):
        self.stage.method(self, data)

    def request(self, url, cache=None, method='GET', headers=None,
                http_session=None, auth=None, cookies=None, foreign_id=None,
                data=None, params=None, *a, **kw):
        if url is None or urlparse(url).scheme != 'http':
            return None
        res = None
        if cache is None:
            cache = settings.HTTP_CACHE
        if cache and (method == 'GET' or foreign_id is not None):
            q = session.query(HTTPResult)
            q = find_http_results(self.crawler.name, q, url, foreign_id)
            res = q.first()

        if res is None:
            http_session = http_session or self.session
            headers = headers or self.session.headers
            auth = auth or self.session.auth
            cookies = cookies or self.session.cookies
            req = Request(method, url, data=data, headers=headers,
                          params=params, auth=auth, cookies=cookies)
            r = req.prepare()
            http_res = http_session.send(r)
            res = self.res_from_http(http_res, foreign_id)
            session.add(res)
            session.commit()
        return res

    def request_html(self, url, *a, **kw):
        res = self.request(url, *a, **kw)
        return html.fromstring(res.get().read())

    def request_json(self, url, *a, **kw):
        res = self.request(url, *a, **kw)
        return json.loads(res.get().read())

    def res_from_http(self, http_res, foreign_id=None,
                      created_at=datetime.now(), meta={}):
        res = HTTPResult()
        content = ''
        size = 0
        for chunk in http_res.iter_content(chunk_size=4096):
            if not chunk:
                continue
            content += chunk
            size += len(chunk)
        path = save_to_temp(content)
        res.put(path)
        res.foreign_id = foreign_id
        res.crawler = self.crawler.name
        res.run_id = self.run_id
        res.size = size
        res.encoding = guess_fh_encoding(path)
        res.url = normalize_url(http_res.url)
        res.status_code = int(http_res.status_code)
        res.headers = dict(http_res.headers)
        res.created_at = created_at
        res.meta = meta
        return res

    def skip_incremental(self, url=None, foreign_id=None):
        if not settings.INCREMENTAL:
            return False
        q = session.query(HTTPResult.id)
        q = find_http_results(self.crawler.name, q, url, foreign_id)
        return q.count() > 0

    def __repr__(self):
        return '<Context(%r, %r)>' % (self.crawler, self.stage)


@celery.task
def handle(state, stage, data):
    context = Context.from_state(state, stage)
    context.execute(data)
