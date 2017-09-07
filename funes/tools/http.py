import os
import cgi
import json
import pickle
import tempfile
from lxml import html
from hashlib import sha1
from normality import guess_encoding
from requests import Session, Request
from requests.structures import CaseInsensitiveDict

from funes import settings
from funes.core import storage
from funes.util import normalize_url, hash_data


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

    def request(self, url, method='GET', headers=None, auth=None, data=None,
                params=None):
        url = normalize_url(url)
        headers = headers or {}
        request_id = hash_data((url, method, params, data, auth))

        existing = self.context.get_tag(request_id) if self.cache else None
        if existing is not None:
            existing = ContextHttpResponse.deserialize(self.context, existing)
            if existing.last_modified and 'If-Modified-Since' not in headers:
                headers['If-Modified-Since'] = existing.last_modified
            if existing.etag and 'If-None-Match' not in headers:
                headers['If-None-Match'] = existing.etag

        request = Request(method, url, data=data, headers=headers,
                          params=params, auth=auth)
        prepared = self.session.prepare_request(request)
        response = self.session.send(prepared, stream=True)

        if existing and response.status_code == 304:
            return existing

        # update the serialised session with cookies etc.
        self.context.state[self.STATE_SESSION] = pickle.dumps(self.session)
        response = ContextHttpResponse.from_response(self.context,
                                                     request_id,
                                                     response)
        if self.cache:
            # TODO: this actually does a full fetch.
            self.context.set_tag(request_id, response.serialize())
        return response

    def get(self, url, **kwargs):
        return self.request(url, method='GET', **kwargs)

    def post(self, url, **kwargs):
        return self.request(url, method='POST', **kwargs)

    def rehash(self, data):
        return ContextHttpResponse.deserialize(self, data)


class ContextHttpResponse(object):

    def __init__(self, context, request_id, response=None, status_code=None,
                 url=None, headers=None, encoding=None, content_hash=None):
        self.context = context
        self.request_id = request_id
        self.response = response
        self.status_code = status_code
        self.url = url
        self.headers = CaseInsensitiveDict(headers)
        self.encoding = encoding
        self._content_hash = content_hash
        self._file_path = None
        self._remove_file = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _stream_content(self):
        """Lazily trigger download of the data when requested."""
        if self.response is None:
            self._file_path = storage.load_file(self._content_hash)
        else:
            fd, self._file_path = tempfile.mkstemp()
            os.close(fd)
            content_hash = sha1()
            with open(self._file_path, 'wb') as fh:
                for chunk in self.response.iter_content(chunk_size=None):
                    content_hash.update(chunk)
                    fh.write(chunk)
            self._remove_file = True
            chash = content_hash.hexdigest()
            self._content_hash = storage.archive_file(self._file_path,
                                                      content_hash=chash)
        return self._file_path

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
    def last_modified(self):
        return self.headers.get('last-modified')

    @property
    def etag(self):
        return self.headers.get('etag')

    @property
    def ok(self):
        return self.status_code < 400

    @property
    def raw(self):
        if not hasattr(self, '_raw'):
            with open(self.file_path, 'r') as fh:
                self._raw = fh.read()
        return self._raw

    @property
    def text(self):
        if self.encoding is None:
            self.encoding = guess_encoding(self.raw)
        return self.raw.decode(self.encoding)

    @property
    def html(self):
        if not hasattr(self, '_html'):
            with open(self.file_path, 'r') as fh:
                self._html = html.parse(fh)
        return self._html

    @property
    def json(self):
        if not hasattr(self, '_json'):
            with open(self.file_path, 'r') as fh:
                self._json = json.load(fh)
        return self._json

    def serialize(self):
        return {
            'request_id': self.request_id,
            'status_code': self.status_code,
            'url': self.url,
            'content_hash': self.content_hash,
            'encoding': self.encoding,
            'headers': dict(self.headers)
        }

    def close(self):
        if self.response:
            self.response.close()
        if self._remove_file and os.path.isfile(self._file_path):
            os.unlink(self._file_path)
        if self._content_hash is not None:
            storage.cleanup_file(self._content_hash)

    @classmethod
    def deserialize(cls, context, data):
        return cls(context, data.get('request_id'),
                   status_code=data.get('status_code'),
                   url=data.get('url'),
                   headers=data.get('headers'),
                   encoding=data.get('encoding'),
                   content_hash=data.get('content_hash'))

    @classmethod
    def from_response(cls, context, request_id, response):
        return cls(context, request_id,
                   response=response,
                   status_code=response.status_code,
                   url=response.url,
                   headers=response.headers,
                   encoding=response.encoding)

    def __repr__(self):
        return '<ContextHttpResponse(%s,%s)>' % (self.status_code,
                                                 self._content_hash)
