import os
from datetime import datetime
from urllib.parse import urljoin

from servicelayer.cache import make_key

API_HOST = "https://api.www.documentcloud.org"
ASSET_HOST = "https://assets.documentcloud.org"
DOCUMENT_HOST = "https://www.documentcloud.org"
DEFAULT_INSTANCE = "documentcloud"

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
    "ukr": "uk",
}


def documentcloud_query(context, data):
    host = context.get("host", API_HOST)
    instance = context.get("instance", DEFAULT_INSTANCE)
    query = data.get("query", context.get("query"))
    if isinstance(query, list):
        for q in query:
            data["query"] = q
            context.recurse(data)
        return
    page = data.get("page", 1)

    search_url = urljoin(host, "/api/documents/search")

    context.log.info(f"Searching DocumentCloud for query: {query}, page: {page}")
    res = context.http.get(
        search_url,
        params={"q": query, "per_page": 100, "page": page, "expand": "organization"},
    )

    documents = res.json.get("results", [])

    for document in documents:
        doc = {
            "foreign_id": "%s:%s" % (instance, document.get("id")),
            "url": "{}/documents/{}/{}.pdf".format(
                ASSET_HOST, document.get("id"), document.get("slug")
            ),
            "source_url": "{}/documents/{}-{}".format(
                DOCUMENT_HOST, document.get("id"), document.get("slug")
            ),
            "title": document.get("title"),
            "publisher": document.get("organization", {}).get("name"),
            "file_name": "{}.pdf".format(document.get("slug")),
            "mime_type": "application/pdf",
        }

        # In incremental crawling mode, skip processing this document if it has been already fully processed before.
        # The key we check for is set in `mark_processed` after a document is fully processed.
        # So the supplied arguments to `make_key` must match.
        if context.incremental:
            key = make_key(
                context.crawler.name,
                doc["foreign_id"],
                document.get("file_hash"),
            )
            if context.check_tag(key):
                context.log.info(
                    f"Skipping processing of document: {doc['foreign_id']}"
                )
                continue

        lang = LANGUAGES.get(document.get("language"))
        if lang is not None:
            doc["languages"] = [lang]

        published = document.get("created_at")
        if published is not None:
            try:
                dt = datetime.strptime(published, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                dt = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
            doc["published_at"] = dt.isoformat()

        context.emit(data=doc)

    if len(documents):
        context.recurse(data={"page": page + 1, "query": query})


def documentcloud_mark_processed(context, data):
    """Create a persistent tag to indicate that a document has been fully processed

    On subsequent runs, we can check and skip processing this document earlier in the
    pipeline.
    """
    key = make_key(
        context.crawler.name,
        data["foreign_id"],
        data["content_hash"],
    )
    context.log.info(
        f"Document with foreign id {data['foreign_id']} has been processed"
    )
    context.set_tag(key, "processed")
