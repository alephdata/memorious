import cgi
import json
import pickle
import codecs
from hashlib import sha1
from pathlib import Path
from lxml import html, etree
from datetime import datetime, timedelta
from urllib.parse import unquote, urlparse
from banal import hash_data, is_mapping
from pantomime import parse_mimetype, normalize_mimetype
from normality import guess_file_encoding, stringify
from requests import Session, Request
from requests.structures import CaseInsensitiveDict
from servicelayer.cache import make_key
from servicelayer.settings import REDIS_SHORT

from memorious import settings
from memorious.core import conn, storage, get_rate_limit
from memorious.logic.mime import NON_HTML
from memorious.exc import ParseError
from memorious.helpers.ua import UserAgent
from memorious.helpers.dates import parse_date
from memorious.util import random_filename


class ContextHttp(object):
    STATE_SESSION = '_http'

    def __init__(self, context):
        self.context = context

        self.cache = settings.HTTP_CACHE
        if 'cache' in context.params:
            self.cache = context.params.get('cache')

        self.session = self.load_session()
        if self.session is None:
            self.reset()

    def reset(self):
        self.session = Session()
        self.session.headers['User-Agent'] = settings.USER_AGENT
        if self.context.crawler.stealthy:
            self.session.headers['User-Agent'] = UserAgent().random()
        return self.session

    def request(self, method, url, headers={}, auth=None, data=None,
                params=None, json=None, allow_redirects=True, lazy=False):
        if is_mapping(params):
            params = list(params.items())

        method = method.upper().strip()
        request = Request(method, url, data=data, headers=headers,
                          json=json, auth=auth, params=params)
        response = ContextHttpResponse(self,
                                       request=request,
                                       allow_redirects=allow_redirects)
        if not lazy:
            response.fetch()
        return response

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def post(self, url, **kwargs):
        return self.request('POST', url, **kwargs)

    def rehash(self, data):
        return ContextHttpResponse.deserialize(self, data)

    def load_session(self):
        if self.STATE_SESSION not in self.context.state:
            return
        key = self.context.state.get(self.STATE_SESSION)
        value = conn.get(key)
        if value is not None:
            session = codecs.decode(bytes(value, 'utf-8'), 'base64')
            return pickle.loads(session)

    def save(self):
        session = pickle.dumps(self.session)
        session = codecs.encode(session, 'base64')
        key = sha1(session).hexdigest()[:15]
        key = make_key(self.context.crawler, "session", self.context.run_id, key)  # noqa
        conn.set(key, session, ex=REDIS_SHORT)
        self.context.state[self.STATE_SESSION] = key


class ContextHttpResponse(object):
    """Handle a cached and managed HTTP response.

    This is a wrapper for ``requests`` HTTP response which adds several
    aspects:

    * Uses HTTP caching against the database when configured to do so.
    * Will evaluate lazily in order to allow fast web crawling.
    * Allow responses to be serialized between crawler operations.
    """
    CACHE_METHODS = ['GET', 'HEAD']

    def __init__(self, http, request=None, allow_redirects=True):
        self.http = http
        self.context = http.context
        self.request = request
        self.allow_redirects = allow_redirects
        self._response = None
        self._status_code = None
        self._url = None
        self._request_id = None
        self._headers = None
        self._encoding = None
        self._content_hash = None
        self._file_path = None
        self.retrieved_at = None
        self._remove_file = False

    @property
    def use_cache(self):
        # It's complicated.
        if not self.http.cache:
            return False
        if self.request is not None:
            return self.request.method in self.CACHE_METHODS
        return True

    @property
    def response(self):
        if self._response is None and self.request is not None:
            request = self.request
            existing = None
            if self.use_cache:
                existing = self.context.get_tag(self.request_id)
            if existing is not None:
                headers = CaseInsensitiveDict(existing.get('headers'))
                last_modified = headers.get('last-modified')
                if last_modified:
                    request.headers['If-Modified-Since'] = last_modified

                etag = headers.get('etag')
                if etag:
                    request.headers['If-None-Match'] = etag

            self._rate_limit(request.url)

            session = self.http.session
            prepared = session.prepare_request(request)
            response = session.send(prepared,
                                    stream=True,
                                    verify=False,
                                    allow_redirects=self.allow_redirects)

            if existing is not None and response.status_code == 304:
                self.context.log.info("Using cached HTTP response: %s",
                                      response.url)
                self.apply_data(existing)
            else:
                self._response = response

            # update the serialised session with cookies etc.
            self.http.save()
        return self._response

    def fetch(self):
        """Lazily trigger download of the data when requested."""
        if self._file_path is not None:
            return self._file_path
        temp_path = self.context.work_path
        if self._content_hash is not None:
            self._file_path = storage.load_file(self._content_hash,
                                                temp_path=temp_path)
            return self._file_path
        if self.response is not None:
            self._file_path = random_filename(temp_path)
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
            self.retrieved_at = datetime.utcnow().isoformat()
        return self._file_path

    def _complete(self):
        if self._content_hash is None:
            self.fetch()

    def _rate_limit(self, url):
        resource = urlparse(url).netloc or url
        limit = self.context.get('http_rate_limit', settings.HTTP_RATE_LIMIT)
        rate_limit = get_rate_limit(resource, limit=limit)
        rate_limit.comply()

    @property
    def url(self):
        if self._response is not None:
            return self._response.url
        if self.request is not None:
            session = self.http.session
            return session.prepare_request(self.request).url
        return self._url

    @property
    def request_id(self):
        if self._request_id is not None:
            return self._request_id
        if self.request is not None:
            parts = [self.request.method, self.url]
            if self.request.data:
                parts.append(hash_data(self.request.data))
            if self.request.json:
                parts.append(hash_data(self.request.json))
            return make_key(*parts)

    @property
    def status_code(self):
        if self._status_code is None and self.response is not None:
            self._status_code = self.response.status_code
        return self._status_code

    @property
    def headers(self):
        if self._headers is None and self.response:
            self._headers = self.response.headers
        return self._headers or CaseInsensitiveDict()

    @property
    def last_modified(self):
        now = datetime.utcnow()
        last_modified_header = self.headers.get("Last-Modified")
        if last_modified_header is not None:
            # Tue, 15 Nov 1994 12:45:26 GMT
            last_modified = parse_date(last_modified_header)
            if last_modified < now + timedelta(seconds=30):
                return last_modified.strftime("%Y-%m-%dT%H:%M:%S%z")
        return None

    @property
    def encoding(self):
        if self._encoding is None:
            mime = parse_mimetype(self.headers.get('content-type'))
            self._encoding = mime.charset
        if self._encoding is None:
            with open(self.file_path, 'rb') as fh:
                self._encoding = guess_file_encoding(fh)
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        self._encoding = encoding

    @property
    def file_path(self):
        self.fetch()
        if self._file_path is not None:
            return Path(self._file_path)

    @property
    def content_hash(self):
        self.fetch()
        return self._content_hash

    @property
    def content_type(self):
        content_type = self.headers.get('content-type')
        return normalize_mimetype(content_type)

    @property
    def file_name(self):
        disposition = self.headers.get('content-disposition')
        file_name = None
        if disposition is not None:
            _, options = cgi.parse_header(disposition)
            filename = options.get('filename') or ''
            file_name = stringify(unquote(filename))
        return file_name

    @property
    def ok(self):
        if self.status_code is None:
            return False
        return self.status_code < 400

    @property
    def raw(self):
        if not hasattr(self, '_raw'):
            self._raw = None
            if self.file_path is not None:
                with open(self.file_path, 'rb') as fh:
                    self._raw = fh.read()
        return self._raw

    @property
    def text(self):
        if self.raw is None:
            return None
        return self.raw.decode(self.encoding, 'replace')

    @property
    def html(self):
        if not hasattr(self, '_html'):
            self._html = None
            if self.content_type in NON_HTML:
                return
            if self.raw is None or not len(self.raw):
                return
            try:
                self._html = html.fromstring(self.text)
            except ValueError as ve:
                if 'encoding declaration' in str(ve):
                    self._html = html.parse(self.file_path.as_posix())
            except (etree.ParserError, etree.ParseError):
                pass
        return self._html

    @property
    def xml(self):
        if not hasattr(self, '_xml'):
            parser = etree.XMLParser(
                ns_clean=True,
                recover=True,
                resolve_entities=False,
                no_network=True
            )
            self._xml = etree.parse(self.file_path.as_posix(), parser=parser)
        return self._xml

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
        # Will be deleted by the context:
        # storage.cleanup_file(self._content_hash)

    def serialize(self):
        self.fetch()
        data = {
            'request_id': self.request_id,
            'status_code': self.status_code,
            'url': self.url,
            'content_hash': self.content_hash,
            'encoding': self._encoding,
            'headers': dict(self.headers),
            'retrieved_at': self.retrieved_at
        }
        if self.last_modified is not None:
            data['modified_at'] = self.last_modified
        return data

    def apply_data(self, data):
        self._status_code = data.get('status_code')
        self._url = data.get('url')
        self._request_id = data.get('request_id')
        self._headers = CaseInsensitiveDict(data.get('headers'))
        self._encoding = data.get('encoding')
        self._content_hash = data.get('content_hash')
        self.retrieved_at = data.get('retrieved_at')

    @classmethod
    def deserialize(cls, http, data):
        obj = cls(http)
        obj.apply_data(data)
        return obj

    def __repr__(self):
        return '<ContextHttpResponse(%s,%s)>' % (self.url,
                                                 self._content_hash)
