import json
import requests
from banal import clean_dict
from urlparse import urljoin

from memorious import settings
from memorious.operation import operation


@operation()
def aleph_emit(context, data):
    if not settings.ALEPH_HOST:
        context.log.warning("No $FUNES_ALEPH_HOST is set, skipping upload...")
        return

    with context.http.rehash(data) as result:
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
        collection_id = aleph_collection_id(context)
        url = aleph_resource('collections/%s/ingest' % collection_id)
        context.log.info("Sending %r to %s/collections/%s", result,
                         settings.ALEPH_HOST, collection_id)

        files = {
            'file': (meta.get('file_name'),
                     result.file_path,
                     result.content_type)
        }
        data = {'meta': json.dumps(meta)}
        res = aleph_session(context).post(url, data=data, files=files)
        if not res.ok:
            context.log.error("Could not ingest %s: %r", res, res.json())
            return


def aleph_collection_id(context):
    if hasattr(context, '_aleph_collection_id'):
        return context._aleph_collection_id

    url = aleph_resource('collections')
    foreign_id = context.params.get('collection', context.name)
    collection_id = None
    while collection_id is None:
        res = aleph_session(context).get(url, params={'limit': 100})
        data = res.json()
        for coll in data.get('results'):
            if coll.get('foreign_id') == foreign_id:
                collection_id = coll.get('id')
        if not data.get('next_url'):
            break
        url = urljoin(url, data.get('next_url'))

    if collection_id is None:
        url = aleph_resource('collections')
        res = aleph_session(context).post(url, json={
            'label': context.description,
            'managed': True,
            'foreign_id': foreign_id
        })
        collection_id = res.json().get('id')

    context._aleph_collection_id = collection_id
    return context._aleph_collection_id


def aleph_resource(path):
    return urljoin(settings.ALEPH_HOST, '/api/1/%s' % path)


def aleph_session(context):
    if not hasattr(context, '_aleph_session'):
        api_key = settings.ALEPH_API_KEY
        if api_key is None:
            raise Exception("No $FUNES_ALEPH_API_KEY is set.")
        context._aleph_session = requests.Session()
        context._aleph_session.headers = {
            'Authorization': 'apikey %s' % api_key
        }
    return context._aleph_session
