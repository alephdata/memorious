import json
import requests
from pprint import pprint  # noqa
from banal import clean_dict
from six.moves.urllib.parse import urljoin

from memorious import settings


def aleph_emit(context, data):
    if not settings.ALEPH_HOST:
        context.log.warning("No $MEMORIOUS_ALEPH_HOST, skipping upload...")
        return
    if not settings.ALEPH_API_KEY:
        context.log.warning("No $MEMORIOUS_ALEPH_API_KEY, skipping upload...")
        return

    session = requests.Session()
    session.headers['Authorization'] = 'apikey %s' % settings.ALEPH_API_KEY
    collection_id = get_collection_id(context, session)
    if collection_id is None:
        context.log.warning("Cannot get aleph collection.")
        return

    content_hash = data.get('content_hash')
    source_url = data.get('source_url', data.get('url'))
    foreign_id = data.get('foreign_id', data.get('request_id', source_url))
    if context.skip_incremental(collection_id, foreign_id, content_hash):
        context.log.info("Skip aleph upload: %s", foreign_id)
        return

    meta = {
        'crawler': context.crawler.name,
        'foreign_id': foreign_id,
        'source_url': source_url,
        'title': data.get('title'),
        'author': data.get('author'),
        'file_name': data.get('file_name'),
        'retrieved_at': data.get('retrieved_at'),
        'modified_at': data.get('modified_at'),
        'published_at': data.get('published_at'),
        'headers': data.get('headers', {})
    }

    languages = context.params.get('languages')
    meta['languages'] = data.get('languages', languages)
    countries = context.params.get('countries')
    meta['countries'] = data.get('countries', countries)
    mime_type = context.params.get('mime_type')
    meta['mime_type'] = data.get('mime_type', mime_type)

    if data.get('parent_foreign_id'):
        meta['parent'] = {'foreign_id': data.get('parent_foreign_id')}

    meta = clean_dict(meta)
    # pprint(meta)

    url = make_url('collections/%s/ingest' % collection_id)
    label = meta.get('file_name', meta.get('source_url'))
    context.log.info("Upload: %s", label)
    with context.load_file(content_hash) as fh:
        if fh is None:
            return
        res = session.post(url,
                           data={'meta': json.dumps(meta)},
                           files={'file': fh})
        if not res.ok:
            context.emit_warning("Error: %r" % res.text)
        else:
            document = res.json().get('documents')[0]
            context.log.info("Document ID: %s", document['id'])


def get_collection_id(context, session):
    url = make_url('collections')
    if hasattr(context.stage, '_aleph_cid'):
        return context.stage._aleph_cid
    foreign_id = context.get('collection', context.crawler.name)
    res = session.get(url, params={
        'filter:foreign_id': foreign_id
    })
    data = res.json()
    for coll in data.get('results'):
        if coll.get('foreign_id') == foreign_id:
            context.stage._aleph_cid = coll.get('id')
            return context.stage._aleph_cid

    res = session.post(url, json={
        'label': context.crawler.description,
        'casefile': False,
        'foreign_id': foreign_id
    })

    if not res.ok:
        context.log.info("Could not create collection: %s", foreign_id)
        return

    context.stage._aleph_cid = res.json().get('id')
    return context.stage._aleph_cid


def make_url(path):
    prefix = urljoin(settings.ALEPH_HOST, '/api/2/')
    return urljoin(prefix, path)
