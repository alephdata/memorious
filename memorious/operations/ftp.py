import os
from datetime import datetime
from urllib.parse import urlparse

import requests
import requests_ftp

from memorious.core import get_rate_limit
from memorious.model import Queue
from memorious import settings


def ftp_fetch(context, data):
    url = data.get("url")
    context.log.info("FTP fetch: %s", url)
    requests_ftp.monkeypatch_session()
    session = requests.Session()
    username = context.get("username", "Anonymous")
    password = context.get("password", "anonymous@ftp")

    resource = urlparse(url).netloc or url
    # a bit weird to have a http rate limit while using ftp
    limit = context.get("http_rate_limit", settings.HTTP_RATE_LIMIT)
    limit = limit / 60  # per minute to per second for stricter enforcement
    rate_limit = get_rate_limit(resource, limit=limit, interval=1, unit=1)

    cached = context.get_tag(url)
    if cached is not None:
        context.emit(rule="pass", data=cached)
        return

    context.enforce_rate_limit(rate_limit)
    resp = session.retr(url, auth=(username, password))
    if resp.status_code < 399:
        data.update(
            {
                "status_code": resp.status_code,
                "retrieved_at": datetime.utcnow().isoformat(),
                "content_hash": context.store_data(data=resp.content),
            }
        )
        context.set_tag(url, data)
        context.emit(rule="pass", data=data)
    else:
        context.enforce_rate_limit(rate_limit)
        resp = session.nlst(url, auth=(username, password))
        for child in resp.iter_lines(decode_unicode=True):
            child_data = data.copy()
            child_data["url"] = os.path.join(url, child)
            context.log.info("FTP directory child: %(url)s", child_data)
            context.emit(rule="child", data=child_data)
