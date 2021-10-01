from pathlib import Path
from pprint import pprint
from typing import Optional  # noqa
from banal import clean_dict  # type: ignore

from servicelayer.cache import make_key  # type: ignore
from alephclient import settings
from alephclient.api import AlephAPI
from alephclient.util import backoff
from alephclient.errors import AlephException
from memorious.core import get_rate_limit  # type: ignore
from memorious.logic.context import Context
from memorious.logic.meta import Meta


def _create_meta_object(context: Context, data: dict) -> Meta:
    languages_default: list[str] = list(context.params.get("languages", []))
    countries_default: list[str] = list(context.params.get("countries", []))
    mime_type_default: str = context.params.get("mime_type", "")

    languages = data.get("languages", languages_default)
    countries = data.get("countries", countries_default)
    mime_type = data.get("mime_type", mime_type_default)

    source_url = data.get("source_url", data.get("url"))
    foreign_id = data.get("foreign_id", data.get("request_id", source_url))

    parent = {}

    if data.get("aleph_folder_id"):
        parent = {"id": data.get("aleph_folder_id")}

    meta = Meta(
        crawler=context.crawler.name,
        foreign_id=foreign_id,
        source_url=source_url,
        title=data.get("title"),
        author=data.get("author"),
        publisher=data.get("publisher"),
        file_name=data.get("file_name"),
        retrieved_at=data.get("retrieved_at"),
        modified_at=data.get("modified_at"),
        published_at=data.get("published_at"),
        headers=data.get("headers", {}),
        keywords=data.get("keywords", []),
        parent=parent,
        languages=languages,
        countries=countries,
        mime_type=mime_type,
    )

    return meta


def aleph_emit(context: Context, data: dict):
    aleph_emit_document(context, data)


def aleph_emit_document(context: Context, data: dict):
    api = get_api(context)
    if api is None:
        return
    collection_id: str = get_collection_id(context, api)
    content_hash: Optional[str] = data.get("content_hash")
    source_url: str = data.get("source_url", data.get("url"))
    foreign_id: str = data.get("foreign_id", data.get("request_id", source_url))
    document_id: Optional[str] = context.get_tag(
        make_key(collection_id, foreign_id, content_hash)
    )

    if document_id:
        context.log.info("Skip aleph upload: %s", foreign_id)
        data["aleph_id"] = document_id
        context.emit(data=data, optional=True)
        return

    meta = clean_dict(_create_meta_object(context, data))
    label = meta.get("file_name", meta.get("source_url"))
    context.log.info("Upload: %s", label)

    with context.load_file(content_hash) as fh:
        if fh is None:
            return
        file_path = Path(fh.name).resolve()

        for try_number in range(api.retries):
            rate = settings.MEMORIOUS_RATE_LIMIT
            rate_limit = get_rate_limit("aleph", limit=rate)
            rate_limit.comply()
            try:
                res = api.ingest_upload(collection_id, file_path, meta)
                document_id = res.get("id")
                context.log.info("Aleph document ID: %s", document_id)
                # Save the document id in cache for future use
                context.set_tag(
                    make_key(collection_id, foreign_id, content_hash), document_id
                )
                data["aleph_id"] = document_id
                data["aleph_document"] = meta
                data["aleph_collection_id"] = collection_id
                context.emit(data=data, optional=True)
                return
            except AlephException as exc:
                if try_number > api.retries or not exc.transient:
                    context.emit_warning("Error: %s" % exc)
                    return
                backoff(exc, try_number)


def aleph_folder(context: Context, data: dict):
    api = get_api(context)
    if api is None:
        return
    collection_id = get_collection_id(context, api)
    foreign_id = data.get("foreign_id")
    if foreign_id is None:
        context.log.warning("No folder foreign ID!")
        return

    meta = clean_dict(_create_meta_object(context, data))
    label = meta.get("file_name", meta.get("source_url"))
    context.log.info("Make folder: %s", label)
    for try_number in range(api.retries):
        rate = settings.MEMORIOUS_RATE_LIMIT
        rate_limit = get_rate_limit("aleph", limit=rate)
        rate_limit.comply()
        try:
            res = api.ingest_upload(collection_id, metadata=meta, sync=True)
            document_id = res.get("id")
            context.log.info("Aleph folder entity ID: %s", document_id)
            # Save the document id in cache for future use
            context.set_tag(make_key(collection_id, foreign_id), document_id)
            data["aleph_folder_id"] = document_id
            data["aleph_collection_id"] = collection_id
            context.emit(data=data, optional=True)
            return
        except AlephException as ae:
            if try_number > api.retries or not ae.transient:
                context.emit_warning("Error: %s" % ae)
                return
            backoff(ae, try_number)


def aleph_emit_entity(context: Context, data: dict) -> None:
    context.log.info("Emit to entity: {}".format(data.get("entity_id")))

    api = get_api(context)
    if api is None:
        return
    collection_id: str = get_collection_id(context, api)
    entity_id: Optional[str] = data.get("entity_id")
    source_url: Optional[str] = data.get("source_url", data.get("url"))
    foreign_id: Optional[str] = data.get(
        "foreign_id", data.get("request_id", source_url)
    )

    # Fetch id from cache
    if entity_id is None:
        context.log.warn("No entity_id found. Skipping store")
        context.emit(data=data, optional=True)
        return

    cached_key = context.get_tag(make_key(collection_id, foreign_id, entity_id))

    if cached_key:
        context.log.info("Entity exists. Skip creation: {}".format(cached_key))
        data["aleph_id"] = cached_key
        context.emit(data=data, optional=True)
        return

    for try_number in range(api.retries):
        rate = settings.MEMORIOUS_RATE_LIMIT
        rate_limit = get_rate_limit("aleph", limit=rate)
        rate_limit.comply()
        try:
            res: dict[str, str] = api.write_entity(
                collection_id,
                {
                    "schema": data.get("schema"),
                    "properties": data.get("properties"),
                },
                entity_id,
            )

            aleph_id = res.get("id")
            context.log.info("Entity created. entity_id is: %s", aleph_id)

            # Save the entity id in cache for future use
            context.set_tag(make_key(collection_id, foreign_id, entity_id), aleph_id)

            data["aleph_id"] = aleph_id
            data["aleph_collection_id"] = collection_id
            context.emit(data=data, optional=True)
            return
        except AlephException as exc:
            if try_number > api.retries or not exc.transient:
                context.emit_warning("Error: %s" % exc)
                return
            backoff(exc, try_number)


def get_api(context: Context) -> Optional[AlephAPI]:
    if not settings.HOST:
        context.log.warning("No $ALEPHCLIENT_HOST, skipping upload...")
        return None
    if not settings.API_KEY:
        context.log.warning("No $ALEPHCLIENT_API_KEY, skipping upload...")
        return None

    session_id: str = "memorious:%s" % context.crawler.name
    return AlephAPI(settings.HOST, settings.API_KEY, session_id=session_id)


def get_collection_id(context: Context, api: AlephAPI) -> str:
    if not hasattr(context.stage, "aleph_cid"):
        foreign_id = context.get("collection", context.crawler.name)
        config = {"label": context.crawler.description}
        collection = api.load_collection_by_foreign_id(foreign_id, config=config)
        context.stage.aleph_cid = collection.get("id")
    return context.stage.aleph_cid
