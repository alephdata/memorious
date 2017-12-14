import os
from urlparse import urljoin

DEFAULT_HOST = 'https://documentcloud.org/'
DEFAULT_INSTANCE = 'documentcloud'


def documentcloud_query(context, data):
    host = context.get('host', DEFAULT_HOST)
    instance = context.get('instance', DEFAULT_INSTANCE)
    query = context.get('query')
    page = data.get('page', 1)

    search_url = urljoin(host, 'search/documents.json')
    res = context.http.get(search_url, params={
        'q': query,
        'per_page': 100,
        'page': page
    })
    documents = res.json.get('documents', [])
    for document in documents:
        doc = {
            'foreign_id': '%s:%s' % (instance, document.get('id')),
            'url': document.get('pdf_url'),
            'source_url': document.get('canonical_url'),
            'title': document.get('title'),
            'author': document.get('author'),
            'published_at': document.get('created_at'),
            'file_name': os.path.basename(document.get('pdf_url')),
            'mime_type': 'application/pdf'
        }
        # if document.get('language'):
        #     data['languages'] = [document.get('language')]
        context.emit(data=doc)

    if len(documents):
        context.recurse(data={'page': page + 1})
