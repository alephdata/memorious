import pickle
import codecs
import logging
from hashlib import sha1

from memorious.model.common import Base, delete_prefix, QUEUE_EXPIRE
from memorious.util import make_key

log = logging.getLogger(__name__)


class SessionState(Base):
    """An HTTP session state."""

    @classmethod
    def save(cls, crawler, session):
        session = pickle.dumps(session)
        session = codecs.encode(session, 'base64')
        key = sha1(session).hexdigest()[:15]
        key = make_key(crawler, "session", key)
        cls.conn.set(key, session, ex=QUEUE_EXPIRE)
        return key

    @classmethod
    def get(cls, crawler, key):
        value = cls.conn.get(make_key(crawler, "session", key))
        if value is not None:
            session = codecs.decode(bytes(value, 'utf-8'), 'base64')
            return pickle.loads(session)

    @classmethod
    def delete(cls, crawler):
        delete_prefix(cls.conn, make_key(crawler, "session", "*"))
