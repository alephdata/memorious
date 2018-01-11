import json
import requests
from pprint import pprint  # noqa
from banal import clean_dict
from six.moves.urllib.parse import urljoin

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
    if result.file_path is None:
        context.log.info("Cannot ingest response: %s", result)
        return

    session = requests.Session()
    session.headers['Authorization'] = 'apikey %s' % settings.ALEPH_API_KEY
    collection_id = get_collection_id(context, session)
    if collection_id is None:
        return

    meta = {
        'crawler': context.crawler.name,
        'source_url': data.get('source_url', result.url),
        'title': data.get('title'),
        'author': data.get('author'),
        'foreign_id': data.get('foreign_id', result.request_id),
        'mime_type': data.get('mime_type', result.content_type),
        'countries': data.get('countries'),
        'languages': data.get('languages'),
        'retrieved_at': data.get('retrieved_at', result.retrieved_at),
        'modified_at': data.get('modified_at', result.last_modified),
        'published_at': data.get('published_at'),
        'headers': dict(result.headers or {})
    }
    if data.get('parent_foreign_id'):
        meta['parent'] = {'foreign_id': data.get('parent_foreign_id')}
    if result.file_name:
        meta['file_name'] = result.file_name

    meta = clean_dict(meta)
    # pprint(meta)

    url = make_url('collections/%s/ingest' % collection_id)
    title = meta.get('title', meta.get('file_name', meta.get('source_url')))
    context.log.info("Sending '%s' to %s", title, url)
    file = open(result.file_path, 'rb')
    res = session.post(url,
                       data={'meta': json.dumps(meta)},
                       files={'file': file})
    if not res.ok:
        context.emit_warning("Could not ingest '%s': %r" % (title, res.text))
    else:
        document = res.json().get('documents')[0]
        context.log.info("Ingesting, document ID: %s", document['id'])


def get_collection_id(context, session):
    url = make_url('collections')
    foreign_id = context.get('collection', context.crawler.name)
    while True:
        res = session.get(url, params={
            'limit': 100,
            'filter:foreign_id': foreign_id
        })
        data = res.json()
        for coll in data.get('results'):
            if coll.get('foreign_id') == foreign_id:
                return coll.get('id')
        if not data.get('next_url'):
            break
        url = urljoin(url, data.get('next_url'))

    url = make_url('collections')
    res = session.post(url, json={
        'label': context.crawler.description,
        'category': context.crawler.category,
        'managed': True,
        'foreign_id': foreign_id
    })
    coll_id = res.json().get('id')
    if coll_id is None:
        message = res.json().get('message')
        context.log.error("Could not get collection: %s", message)
    return coll_id


def make_url(path):
    prefix = urljoin(settings.ALEPH_HOST, '/api/')
    return urljoin(prefix, '%s/%s' % (settings.ALEPH_API_VERSION, path))
