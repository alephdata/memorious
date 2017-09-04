from funes.model.result import HTTPResult
from funes.tools.util import normalize_url


def find_http_results(name, q, url, foreign_id):
    url = normalize_url(url)
    foreign_id = normalize_url(foreign_id)
    if url is None and foreign_id is None:
        return q.limit(0)
    q = q.filter(HTTPResult.crawler == name)
    if url is not None:
        q = q.filter(HTTPResult.url == url)
    if foreign_id is not None:
        q = q.filter(HTTPResult.foreign_id == foreign_id)
    return q
