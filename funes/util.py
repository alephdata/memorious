import six
from hashlib import sha1
from itertools import chain
from collections import Sequence, Mapping
from urlparse import urlsplit, urlunsplit


def normalize_url(url):
    # TODO: learn from https://github.com/hypothesis/h/blob/master/h/api/uri.py
    try:
        if isinstance(url, six.text_type):
            url = url.encode('utf-8')
        parsed = urlsplit(url)
        scheme = parsed.scheme.lower()

        port = parsed.port
        if scheme == 'http' and port == 80:
            port = None
        elif scheme == 'https' and port == 443:
            port = None

        netloc = parsed.hostname.lower()
        if port is not None:
            netloc += ':' + str(port)

        userinfo = parsed.username
        if parsed.password is not None:
            userinfo += ':' + parsed.password
        if userinfo is not None:
            netloc = '@'.join([userinfo, netloc])

        path = parsed.path
        if not len(path):
            path = '/'

        query = parsed.query
        return urlunsplit((scheme, netloc, path, query, None))
    except:
        return url


def text_data(obj):
    if obj is None:
        yield ''
    elif isinstance(obj, six.binary_type):
        yield obj
    elif isinstance(obj, six.text_type):
        yield obj.encode('utf-8')
    elif isinstance(obj, Mapping):
        for key, value in obj.items():
            for out in chain(text_data(key), text_data(value)):
                yield out
    elif isinstance(obj, Sequence):
        for item in obj:
            for out in text_data(item):
                yield out
    else:
        yield unicode(obj).encode('utf-8')


def hash_data(obj):
    collect = sha1()
    for text in text_data(obj):
        collect.update(text + '$')
    return collect.hexdigest()
