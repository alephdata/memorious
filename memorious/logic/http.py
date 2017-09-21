import os
import cgi
import json
import pickle
import tempfile
from lxml import html
from hashlib import sha1
from banal import hash_data
from normality import guess_encoding
from fake_useragent import UserAgent
from requests import Session, Request
from requests.structures import CaseInsensitiveDict

from memorious import settings
from memorious.core import storage
from memorious.util import normalize_url
from memorious.exc import ParseError


class ContextHttp(object):
    STATE_SESSION = '_http_session'

    def __init__(self, context):
        self.context = context

        self.cache = settings.HTTP_CACHE
        if 'cache' in context.params:
            self.cache = context.params.get('cache')

        if self.STATE_SESSION in self.context.state:
            session = self.context.state.get(self.STATE_SESSION)
            self.session = pickle.loads(session)
        else:
            self.session = Session()

    @property
    def ua(self):
        return UserAgent().random

    def reset(self):
        self.session = Session()

    def request(self, url, method='GET', headers={}, auth=None, data=None,
                params=None, random_ua=False):
        url = normalize_url(url)
        if random_ua:
            headers.update({'User-Agent': self.ua})
        request = Request(method, url, data=data, headers=headers,
                          params=params, auth=auth)
        return ContextHttpResponse.from_request(self, request)

    def get(self, url, **kwargs):
        return self.request(url, method='GET', **kwargs)

    def post(self, url, **kwargs):
        return self.request(url, method='POST', **kwargs)

    def rehash(self, data):
        return ContextHttpResponse.deserialize(self, data)


class ContextHttpResponse(object):
    """Handle a cached and managed HTTP response.

    This is a wrapper for ``requests`` HTTP response which adds several
    aspects:

    * Uses HTTP caching against the database when configured to do so.
    * Will evaluate lazily in order to allow fast web crawling.
    * Allow responses to be serialized between crawler operations.
    """

    def __init__(self, http, request=None, request_id=None):
        self.http = http
        self.context = http.context
        self.request = request
        self.request_id = request_id
        self._response = None
        self._status_code = None
        self._url = None
        self._headers = None
        self._encoding = None
        self._content_hash = None
        self._file_path = None
        self._remove_file = False

    @property
    def response(self):
        if self._response is None and self.request is not None:
            request = self.request
            existing = None
            if self.http.cache:
                existing = self.context.get_tag(self.request_id)
            if existing is not None:
                headers = CaseInsensitiveDict(existing.get('headers'))
                last_modified = headers.get('last-modified')
                if last_modified:
                    request.headers['If-Modified-Since'] = last_modified

                etag = headers.get('etag')
                if etag:
                    request.headers['If-None-Match'] = etag

            prepared = self.http.session.prepare_request(request)
            response = self.http.session.send(prepared, stream=True)

            if existing is not None and response.status_code == 304:
                self.context.log.info("Using cached HTTP response: %s",
                                      response.url)
                self.apply_data(existing)
            else:
                self._response = response

            # update the serialised session with cookies etc.
            session = pickle.dumps(self.http.session)
            self.context.state[self.http.STATE_SESSION] = session
        return self._response

    def _stream_content(self):
        """Lazily trigger download of the data when requested."""
        if self.response is None:
            self._file_path = storage.load_file(self._content_hash)
        else:
            fd, self._file_path = tempfile.mkstemp()
            os.close(fd)
            content_hash = sha1()
            with open(self._file_path, 'wb') as fh:
                for chunk in self.response.iter_content(chunk_size=8192):
                    content_hash.update(chunk)
                    fh.write(chunk)
            self._remove_file = True
            chash = content_hash.hexdigest()
            self._content_hash = storage.archive_file(self._file_path,
                                                      content_hash=chash)

            if self.http.cache and self.ok:
                self.context.set_tag(self.request_id, self.serialize())
        return self._file_path

    @property
    def url(self):
        if self._response is not None:
            return self._response.url
        if self.request is not None:
            return self.request.url
        return self._url

    @property
    def status_code(self):
        if self._status_code is None and self.response:
            self._status_code = self.response.status_code
        return self._status_code

    @property
    def headers(self):
        if self._headers is None and self.response:
            self._headers = self.response.headers
        return self._headers or CaseInsensitiveDict()

    @property
    def encoding(self):
        if self._encoding is None and self.response:
            self._encoding = self.response.encoding
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        self._encoding = encoding

    @property
    def file_path(self):
        if self._file_path is None:
            self._stream_content()
        return self._file_path

    @property
    def content_hash(self):
        if self._content_hash is None:
            self._stream_content()
        return self._content_hash

    @property
    def content_type(self):
        content_type = self.headers.get('content-type')
        if content_type is not None:
            content_type, options = cgi.parse_header(content_type)
        return content_type or 'application/octet-stream'

    @property
    def ok(self):
        return self.status_code < 400

    @property
    def raw(self):
        if not hasattr(self, '_raw'):
            if self.file_path is None:
                raise ParseError("Cannot parse failed download.")
            with open(self.file_path, 'r') as fh:
                self._raw = fh.read()
        return self._raw

    @property
    def text(self):
        encoding = self.encoding
        if encoding is None:
            encoding = guess_encoding(self.raw)
        return self.raw.decode(encoding)

    @property
    def html(self):
        if not hasattr(self, '_html'):
            self._html = None
            try:
                self._html = html.fromstring(self.text)
            except ValueError as ve:
                if 'encoding declaration' in ve.message:
                    self._html = html.parse(self.file_path)
        return self._html

    @property
    def json(self):
        if not hasattr(self, '_json'):
            if self.file_path is None:
                raise ParseError("Cannot parse failed download.")
            with open(self.file_path, 'r') as fh:
                self._json = json.load(fh)
        return self._json

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        if self._response is not None:
            self._response.close()
        if self._remove_file and os.path.isfile(self._file_path):
            os.unlink(self._file_path)
        storage.cleanup_file(self._content_hash)

    def serialize(self):
        return {
            'request_id': self.request_id,
            'status_code': self.status_code,
            'url': self.url,
            'content_hash': self.content_hash,
            'encoding': self.encoding,
            'headers': dict(self.headers)
        }

    def apply_data(self, data):
        self._status_code = data.get('status_code')
        self._url = data.get('url')
        self._headers = CaseInsensitiveDict(data.get('headers'))
        self._encoding = data.get('encoding')
        self._content_hash = data.get('content_hash')

    @classmethod
    def deserialize(cls, http, data):
        obj = cls(http, request_id=data.get('request_id'))
        obj.apply_data(data)
        return obj

    @classmethod
    def from_request(cls, http, request):
        request_id = hash_data((request.url, request.method,
                                request.params, request.data))
        return cls(http, request=request, request_id=request_id)

    def __repr__(self):
        return '<ContextHttpResponse(%s,%s)>' % (self.url,
                                                 self._content_hash)
