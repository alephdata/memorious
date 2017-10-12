import json
import requests
from banal import clean_dict
from urlparse import urljoin

from memorious import settings


def aleph_emit(context, data):
    context.log.info("Store [aleph]: %s", data.get('url'))
    if not settings.ALEPH_HOST:
        context.log.warning("No $MEMORIOUS_ALEPH_HOST, skipping upload...")
        return
    if not settings.ALEPH_API_KEY:
        context.log.warning("No $MEMORIOUS_ALEPH_API_KEY, skipping upload...")
        return

    with context.http.rehash(data) as result:
        if not result.ok:
            return
        submit_result(context, result, data)


def submit_result(context, result, data):
    session = requests.Session()
    session.headers['Authorization'] = 'apikey %s' % settings.ALEPH_API_KEY
    collection_id = get_collection_id(context, session)
    meta = {
        'crawler': context.crawler.name,
        'source_url': data.get('source_url', result.url),
        'file_name': data.get('file_name'),
        'title': data.get('title'),
        'author': data.get('author'),
        'foreign_id': data.get('foreign_id', result.request_id),
        'mime_type': data.get('mime_type', result.content_type),
        'countries': data.get('countries'),
        'languages': data.get('languages'),
        'headers': result.headers
    }
    meta = clean_dict(meta)
    url = make_url('collections/%s/ingest' % collection_id)
    context.log.info("Sending %r to %s/collections/%s", result,
                     settings.ALEPH_HOST, collection_id)

    files = {
        'file': (meta.get('file_name'), result.file_path, result.content_type)
    }
    data = {'meta': json.dumps(meta)}
    res = session.post(url, data=data, files=files)
    if not res.ok:
        context.log.error("Could not ingest %r: %r", result, res.json())


def get_collection_id(context, session):
    url = make_url('collections')
    foreign_id = context.get('collection', context.name)
    while True:
        res = session.get(url, params={'limit': 100})
        data = res.json()
        for coll in data.get('results'):
            if coll.get('foreign_id') == foreign_id:
                return coll.get('id')
        if not data.get('next_url'):
            break
        url = urljoin(url, data.get('next_url'))

    url = make_url('collections')
    res = session.post(url, json={
        'label': context.description,
        'managed': True,
        'foreign_id': foreign_id
    })
    return res.json().get('id')


def make_url(path):
    return urljoin(settings.ALEPH_HOST, '/api/1/%s' % path)
