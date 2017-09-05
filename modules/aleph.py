import json
import requests
from urlparse import urljoin

from funes import settings
from funes.operation import operation


@operation()
def aleph_emit(context, data):
    if not settings.ALEPH_HOST:
        context.log.warning("No $FUNES_ALEPH_HOST is set, skipping upload...")
        return

    res = data.get('res')
    meta = data.get('meta')
    if res is None or meta is None:
        return
    files = data.get('files')

    collection_id = aleph_collection_id(context)
    url = aleph_resource('collections/%s/ingest' % collection_id)
    context.log.info("Sending %r to %s/collections/%s", res,
                     settings.ALEPH_HOST, collection_id)

    if files is None:
        files = {'file': (meta.get('file_name'),
                          res.get(),
                          meta.get('content_type'))}
    data = {'meta': json.dumps(meta)}
    res = aleph_session(context).post(url, data=data, files=files)
    if res.status_code != 200:
        context.log.error("Could not ingest %s: %r", res, res.json())
        return
    context.params['count'] -= 1


def aleph_collection_id(context):
    if hasattr(context, '_aleph_collection_id'):
        return context._aleph_collection_id
    foreign_id = context.name

    url = aleph_resource('collections')
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
