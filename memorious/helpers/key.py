from hashlib import sha1

from memorious.util import make_key


def make_id(*parts):
    key = make_key(*parts)
    if key is not None:
        key = key.encode('utf-8')
        return sha1(key).hexdigest()
