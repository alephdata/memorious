import uuid
import json
import time
import pickle
import logging
from lxml import html
from datetime import datetime
from urlparse import urlparse
from requests import Session, Request

from funes.core import store
from funes.core import celery as app, config, session
from funes.model.result import HTTPResult
from funes.tools.util import normalize_url
from funes.tools.results import find_http_results
from funes.tools.files import save_to_temp, guess_fh_encoding


class Context(object):
    """Provides state tracking and methods for operation interactions."""

    def __init__(self, name=None, description=None, run_id=None, sender=None,
                 session=None, params={}):
        self.name = name
        self.description = description
        self.sender = sender
        self.params = params
        self.run_id = run_id or uuid.uuid1().hex
        if session is not None:
            self._session = session

    @classmethod
    def from_state(cls, state):
        return cls(state.get('name'),
                   state.get('description'),
                   state.get('run_id'),
                   state.get('sender'),
                   pickle.loads(state.get('session')),
                   state.get('params'))

    @property
    def session(self):
        if not hasattr(self, '_session'):
            self.new_session()
        return self._session

    @session.setter
    def session(self, s):
        self._session = s

    def new_session(self):
        self.session = Session()

    @property
    def log(self):
        if not hasattr(self, '_log'):
            log_name = '[%s] %s' % (self.run_id, self.name)
            self._log = logging.getLogger(log_name)
        return self._log

    def dump_state(self):
        state = {}
        state['name'] = self.name
        state['description'] = self.description
        state['run_id'] = self.run_id
        state['sender'] = self.sender
        state['session'] = pickle.dumps(self.session)
        state['params'] = self.params
        return state

    def emit(self, rule='pass', data={}, sender=None):
        if rule is None:
            return
        state = self.dump_state()
        if sender is not None:
            state['sender'] = sender
        state = json.dumps(state)
        time.sleep(self.params.get('delay'))
        handle(state, rule, data)

    def request(self, url, cache=None, method='GET', headers=None,
                http_session=None, auth=None, cookies=None, foreign_id=None,
                data=None, params=None, *a, **kw):
        if url is None or urlparse(url).scheme != 'http':
            return None
        res = None
        if cache is None:
            cache = config.get('cache')
        if cache and (method == 'GET' or foreign_id is not None):
            q = session.query(HTTPResult)
            q = find_http_results(self.name, q, url, foreign_id)
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
        res.crawler = self.name
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
        if not config.get('incremental'):
            return
        q = session.query(HTTPResult.id)
        q = find_http_results(self.name, q, url, foreign_id)
        return q.count() > 0


@app.task
def handle(state, rule, data):
    context = Context.from_state(json.loads(state))
    crawler = context.name
    sender = context.sender
    rule_target = store.rule_target(crawler, sender, rule)
    if rule_target is None:
        context.log.info('No target for %s rule %s', sender, rule)
        return
    context.sender = None
    rule_target(context, data)
