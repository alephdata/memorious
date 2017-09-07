import os
import json
import pickle
import tempfile
from lxml import html
from hashlib import sha1
from normality import guess_encoding
from requests import Session, Request


class ContextHttp(object):
    STATE_SESSION = '_http_session'

    def __init__(self, context):
        self.context = context
        if self.STATE_SESSION in self.context.state:
            session = self.context.state.get(self.STATE_SESSION)
            self.session = pickle.loads(session)
        else:
            self.session = Session()

    def request(self, url, method='GET', headers=None, auth=None, data=None,
                params=None):
        request = Request(method, url, data=data, headers=headers,
                          params=params, auth=auth)
        prepared = self.session.prepare_request(request)
        response = self.session.send(prepared, stream=True)

        # update the serialised session with cookies etc.
        self.context.state[self.STATE_SESSION] = pickle.dumps(self.session)
        return ContextHttpResponse(self.context, response)


class ContextHttpResponse(object):

    def __init__(self, context, response):
        self.context = context
        self.response = response
        self.status_code = response.status_code
        self.url = response.url
        self.headers = response.headers
        self.encoding = response.encoding
        self._file_path = None
        self._content_hash = None

    def _stream_content(self):
        """Lazily trigger download of the data when requested."""
        fd, self._file_path = tempfile.mkstemp()
        os.close(fd)
        content_hash = sha1()
        with open(self._file_path, 'wb') as fh:
            for chunk in self.response.iter_content(chunk_size=8192):
                content_hash.update(chunk)
                fh.write(chunk)
        self._content_hash = content_hash.hexdigest()
        self.context.store_file(self._file_path,
                                content_hash=self._content_hash)
        return self._file_path

    @property
    def file_path(self):
        if self._file_path is not None:
            self._stream_content()
        return self._file_path

    @property
    def content_hash(self):
        if self._content_hash is None:
            self._stream_content()
        return self._content_hash

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

    def close(self):
        self.response.close()
