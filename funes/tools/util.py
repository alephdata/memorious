import re
import urlnorm
from urlparse import urldefrag


def normalize_url(url):
    # TODO: learn from https://github.com/hypothesis/h/blob/master/h/api/uri.py
    try:
        url = urlnorm.norm(url)
        url, _ = urldefrag(url)
        url = re.sub('[\n\r]', '', url)
        url = url.rstrip('/')
        return url
    except:
        return None
