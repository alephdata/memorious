import os
import cgi
import logging
from datetime import datetime
from normality import stringify
from urlparse import urlparse, unquote
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, String, Integer, DateTime

from funes.core import config
from funes.exc import StorageNotFound
from funes.model.common import Base
from funes.core import session
from funes.tools.files import save_to_temp

log = logging.getLogger(__name__)


class Result(Base):
    """A resource that has been retrieved, or that failed to retrieve."""
    __tablename__ = 'result'

    id = Column(Integer, primary_key=True)
    crawler = Column(String, nullable=False, index=True)
    run_id = Column(String, nullable=False, index=True)
    operation_id = Column(Integer, nullable=True, index=True)
    content_hash = Column(String, nullable=True, index=True)
    foreign_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta = Column(JSONB, nullable=False, default={})

    def __init__(self, operation_id=None):
        self._local_path = None
        if operation_id is not None:
            self.operation_id = operation_id

    def get(self):
        """Return a minimal fileobj for the given artifact path."""
        if self.content_hash is None:
            raise StorageNotFound("No hash for artifact: %r" % self)
        return config.storage.load_file(self.content_hash)

    def put(self, file_path=None):
        """Store a stream at the given path if it does not already exist."""
        if file_path is None:
            raise StorageNotFound("No path for artifact: %r" % self)
        self.content_hash = config.storage.archive_file(file_path)
        return self.content_hash

    @classmethod
    def from_res(cls, res, content=None, foreign_id=None):
        if type(res).__name__ != cls.__name__:
            log.debug('Class %s cannot be copied to class %s', res.__name__,
                      cls.__name__)
            return
        new_res = cls()
        new_res.__dict__.update(res.__dict__)
        new_res.foreign_id = foreign_id
        if content is not None:
            path = save_to_temp(content)
            new_res.put(path)
        session.add(new_res)
        session.commit()
        return new_res

    def __repr__(self):
        return '<Result(%s,%s,%s)>' % \
            (self.crawler, self.foreign_id)


class HTTPResult(Result):
    url = Column(String, nullable=True, index=True)
    size = Column(Integer, nullable=True, index=True)
    encoding = Column(String, nullable=True)
    status_code = Column(Integer, nullable=True)
    headers = Column(JSONB, nullable=True, default={})

    def __init__(self):
        super(HTTPResult, self).__init__()

    @property
    def file_name(self):
        file_name = None
        disposition = self.headers.get('Content-Disposition')

        if disposition is not None:
            _, attrs = cgi.parse_header(disposition)
            file_name = attrs.get('filename') or ''
            file_name = stringify(unquote(file_name))

        if file_name is None and self.url:
            parsed = urlparse(self.url)
            file_name = os.path.basename(parsed.path) or ''
            file_name = stringify(unquote(file_name))

        return file_name or 'data'

    @property
    def content_type(self):
        content_type = self.headers.get('Content-Type')
        content_type = content_type or 'application/octet-stream'
        content_type, attrs = cgi.parse_header(content_type)
        return content_type

    def __repr__(self):
        return '<HTTPResult(%s,%s,%s)>' % \
            (self.crawler, self.url, self.foreign_id)
