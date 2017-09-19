import os
from urlparse import urljoin
from itertools import count
from pycountry import languages

from memorious.operation import operation

DEFAULT_HOST = 'https://documentcloud.org/'
DEFAULT_INSTANCE = 'documentcloud'


@operation()
def documentcloud_query(context, data):
    host = context.params.get('host', DEFAULT_HOST)
    instance = context.params.get('instance', DEFAULT_INSTANCE)
    query = context.params.get('query')

    search_url = urljoin(host, 'search/documents.json')
    for page in count(1):
        res = context.http.get(search_url, params={
            'q': query,
            'per_page': 100,
            'page': page
        })
        documents = res.json.get('documents', [])
        if not len(documents):
            break

        for document in documents:
            data['foreign_id'] = '%s:%s' % (instance, document.get('id'))
            data['url'] = document.get('pdf_url')
            data['source_url'] = document.get('canonical_url')
            data['title'] = document.get('title')
            data['author'] = document.get('author')
            data['file_name'] = os.path.basename(document.get('pdf_url'))
            data['mime_type'] = 'application/pdf'

            try:
                lang = languages.get(alpha_3=document.get('language'))
                data['countries'] = [lang.alpha_2]
            except Exception as exc:
                context.log.exception(exc)

            context.emit(rule='pass', data=data)
