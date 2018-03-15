import os
from datetime import datetime
import requests
import requests_ftp


def ftp_fetch(context, data):
    url = data.get('url')
    context.log.info("FTP fetch: %s", url)
    requests_ftp.monkeypatch_session()
    session = requests.Session()
    username = context.get('username', 'Anonymous')
    password = context.get('password', 'anonymous@ftp')

    cached = context.get_tag(url)
    if cached is not None:
        context.emit(rule='pass', data=cached)
        return

    resp = session.retr(url, auth=(username, password))
    if resp.status_code < 399:
        data.update({
            'status_code': resp.status_code,
            'retrieved_at': datetime.utcnow().isoformat(),
            'content_hash': context.store_data(data=resp.content)
        })
        context.set_tag(url, data)
        context.emit(rule='pass', data=data)
    else:
        resp = session.nlst(url, auth=(username, password))
        for child in resp.iter_lines():
            child_data = data.copy()
            child_data['url'] = os.path.join(url, child)
            # context.log.info("FTP directory child: %(url)s", child_data)
            context.emit(rule='child', data=child_data)
