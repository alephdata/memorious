import os
from datetime import datetime
from urllib.parse import urljoin

DEFAULT_HOST = 'https://documentcloud.org/'
DEFAULT_INSTANCE = 'documentcloud'

LANGUAGES = {
    "ara": "ar",
    "zho": "zh",
    "tra": "zh",
    "hrv": "hr",
    "dan": "da",
    "nld": "nl",
    "eng": "en",
    "fra": "fr",
    "deu": "de",
    "heb": "he",
    "hun": "hu",
    "ind": "id",
    "ita": "it",
    "jpn": "ja",
    "kor": "ko",
    "nor": "no",
    "por": "pt",
    "ron": "ro",
    "rus": "ru",
    "spa": "es",
    "swe": "sv",
    "ukr": "uk"
}


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
            'file_name': os.path.basename(document.get('pdf_url')),
            'mime_type': 'application/pdf'
        }

        lang = LANGUAGES.get(document.get('language'))
        if lang is not None:
            data['languages'] = [lang]

        published = document.get('created_at')
        if published is not None:
            dt = datetime.strptime(published, '%b %d, %Y')
            doc['published_at'] = dt.isoformat()

        context.emit(data=doc)

    if len(documents):
        context.recurse(data={'page': page + 1})
