import six
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
