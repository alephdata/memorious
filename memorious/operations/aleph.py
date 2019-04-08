from pathlib import Path
from pprint import pprint  # noqa
from banal import clean_dict
from alephclient.api import AlephAPI

from servicelayer import settings


def aleph_emit(context, data):
    if not settings.ALEPH_HOST:
        context.log.warning("No $MEMORIOUS_ALEPH_HOST, skipping upload...")
        return
    if not settings.ALEPH_API_KEY:
        context.log.warning("No $MEMORIOUS_ALEPH_API_KEY, skipping upload...")
        return

    session_id = 'memorious:%s' % context.crawler.name
    api = AlephAPI(settings.ALEPH_HOST, settings.ALEPH_API_KEY,
                   session_id=session_id)
    collection_id = get_collection_id(context, api)
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

    label = meta.get('file_name', meta.get('source_url'))
    context.log.info("Upload: %s", label)
    with context.load_file(content_hash) as fh:
        if fh is None:
            return
        file_path = Path(fh.name).resolve()
        res = api.ingest_upload(collection_id, file_path, meta)
        if res.get('status') == 'ok':
            document = res.get('documents')[0]
            context.log.info("Document ID: %s", document['id'])
        else:
            context.emit_warning("Error: %r" % res)


def get_collection_id(context, api):
    if hasattr(context.stage, '_aleph_cid'):
        return context.stage._aleph_cid
    foreign_id = context.get('collection', context.crawler.name)
    config = {'label': context.crawler.description}
    collection = api.load_collection_by_foreign_id(foreign_id, config=config)
    context.stage._aleph_cid = collection.get('id')
    return context.stage._aleph_cid
