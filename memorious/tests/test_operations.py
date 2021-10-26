import os
import json
import shutil
import pytest

from banal import clean_dict
from unittest.mock import ANY
from memorious.core import tags, storage
from memorious.operations.fetch import fetch, session
from memorious.operations.parse import parse
from memorious.operations.initializers import seed, sequence, dates, enumerate
from memorious.operations.store import directory, cleanup_archive
from memorious.logic.context import Context
from memorious.operations.aleph import (
    _create_meta_object,
    aleph_emit_document,
    get_collection_id,
)
from alephclient.api import AlephAPI


@pytest.mark.parametrize(
    "url,call_count",
    [
        ("https://httpbin.org/html", 1),
        ("https://occrp.org/", 0),
        ("https://httpbin.org/status/418", 0),
    ],
)
def test_fetch(url, call_count, context, mocker):
    rules = {"pattern": "https://httpbin.org/*"}
    context.params["rules"] = rules
    mocker.patch.object(context, "emit")
    fetch(context, {"url": url})
    assert context.emit.call_count == call_count


def test_session(context, mocker):
    context.params["user"] = "user"
    context.params["password"] = "password"
    context.params["user_agent"] = "Godzilla Firehose 0.1"
    context.params["url"] = "https://httpbin.org/get"
    data = {"hello": "world"}

    mocker.patch.object(context.http, "save")
    mocker.patch.object(context, "emit")

    session(context, data)

    assert context.http.save.called_one_with()
    assert context.emit.called_one_with(data=data)
    assert context.http.session.headers["User-Agent"] == "Godzilla Firehose 0.1"
    assert context.http.session.headers["Referer"] == "https://httpbin.org/get"
    assert context.http.session.auth == ("user", "password")


def test_parse(context: Context, mocker):
    url = "http://example.org/"
    result = context.http.get(url)
    data = result.serialize()

    mocker.patch.object(context, "emit")

    rules = {"pattern": "https://httpbin.org/*"}
    context.params["store"] = rules
    parse(context, data)

    assert context.emit.call_count == 1
    context.emit.assert_called_once_with(rule="fetch", data=ANY)

    # cleanup tags
    tags.delete()

    context.http.result = None
    context.params["store"] = None
    context.params["meta"] = {"title": ".//h1", "description": ".//p"}
    parse(context, data)

    assert data["url"] == "https://www.iana.org/domains/example"
    assert data["title"] == "Example Domain"
    assert data["description"].startswith("This domain is for")
    assert context.emit.call_count == 3, data


def test_parse_ftm(context: Context, mocker):
    url = "https://www.occrp.org/en/daily/14082-riviera-maya-gang-members-sentenced-in-romania"
    result = context.http.get(url)
    data = result.serialize()

    context.params["meta"] = {}
    context.params["schema"] = "Article"
    context.params["properties"] = {
        "title": './/meta[@property="og:title"]/@content',
        "author": './/meta[@name="author"]/@content',
        "publishedAt": './/*[@class="date"]/text()',
        "description": './/meta[@property="og:description"]/@content',
    }

    parse(context, data)
    props = data["properties"]

    assert "Riviera Maya Gang Members Sentenced in Romania" in props["title"]
    assert "Attila Biro" in props["author"]
    assert props["description"][0].startswith("A Bucharest court")


def test_seed(context: Context, mocker):
    context.params["url"] = None
    context.params["urls"] = ["http://httpbin.org/status/%(status)s"]
    mocker.patch.object(context, "emit")
    seed(context, data={"status": 404})
    assert context.emit.call_count == 1
    context.emit.assert_called_once_with(data={"url": "http://httpbin.org/status/404"})


def test_sequence(context: Context, mocker):
    mocker.patch.object(context, "emit")

    context.params["start"] = 2
    context.params["stop"] = 11
    context.params["step"] = 3
    sequence(context, data={})
    assert context.emit.call_count == 3

    context.params["start"] = 7
    context.params["stop"] = 1
    context.params["step"] = -3
    sequence(context, data={})
    assert context.emit.call_count == 5


def test_dates(context: Context, mocker):
    mocker.patch.object(context, "emit")
    mocker.patch.object(context, "recurse")
    context.params["format"] = "%d-%m-%Y"
    context.params["days"] = 3
    context.params["begin"] = "10-12-2012"
    context.params["end"] = "20-12-2012"
    dates(context, data={})
    assert context.emit.call_count == 1
    context.emit.assert_called_once_with(
        data={"date": "20-12-2012", "date_iso": "2012-12-20T00:00:00"}
    )
    assert context.recurse.call_count == 1
    context.recurse.assert_called_once_with(data={"current": "17-12-2012"})


def test_enumerate(context: Context, mocker):
    mocker.patch.object(context, "emit")
    context.params["items"] = [1, 2, 3]
    enumerate(context, data={})
    assert context.emit.call_count == 3


def test_directory(context: Context):
    file_path = os.path.realpath(__file__)
    store_dir = os.path.normpath(
        os.path.join(file_path, "../testdata/data/store/occrp_web_site")
    )
    shutil.rmtree(store_dir, ignore_errors=True)

    # echo user-agent
    url = "https://httpbin.org/user-agent"
    result = context.http.get(url, headers={"User-Agent": "Memorious Test"})
    data = result.serialize()
    directory(context, data)

    content_hash = data.get("content_hash")

    raw_file_path = os.path.join(store_dir, content_hash + ".data.json")
    meta_file_path = os.path.join(store_dir, content_hash + ".json")
    assert os.path.exists(meta_file_path)
    assert os.path.exists(raw_file_path)

    with open(meta_file_path, "rb") as fh:
        assert json.load(fh)["content_hash"] == data["content_hash"]
    with open(raw_file_path, "rb") as fh:
        assert b'"user-agent": "Memorious Test"' in fh.read()


def test_cleanup_archive(context: Context):
    url = "https://httpbin.org/user-agent"
    result = context.http.get(url, headers={"User-Agent": "Memorious Test"})
    data = result.serialize()
    assert storage.load_file(data["content_hash"]) is not None
    cleanup_archive(context, data)
    assert storage.load_file(data["content_hash"]) is None


def test_create_meta_object(context: Context, mocker):
    data = {
        "title": "test-title",
        "author": "test-author",
        "publisher": "test-publisher",
        "file-name": "test-filename",
        "retrieved_at": "test-retrieved-at",
    }
    meta = clean_dict(_create_meta_object(context, data))
    assert meta.get("title") is "test-title"
    assert isinstance(meta.get("languages"), list) is True
    assert len(meta.get("languages")) is 0

    context.params["languages"] = ["en", "es", "ru"]
    meta = clean_dict(_create_meta_object(context, data))
    assert meta.get("languages") == ["en", "es", "ru"]

    data.update({"aleph_folder_id": "test_folder_id"})
    meta = clean_dict(_create_meta_object(context, data))
    assert meta.get("parent")["id"] is "test_folder_id"


def test_emit_document_existing(context: Context, mocker):
    mocker.patch.object(AlephAPI, "load_collection_by_foreign_id", mock_AlephApi)
    mocker.patch.object(context, "get_tag", mock_get_tag)
    mocker.patch.object(context, "emit")
    tag_spy = mocker.spy(context, "get_tag")
    emit_spy = mocker.spy(context, "emit")

    context.stage.aleph_cid = "aleph_cid"
    aleph_emit_document(context, {})

    assert tag_spy.call_count == 1
    assert emit_spy.call_count == 1


def test_emit_document_new(context: Context, mocker):
    file_path = os.path.realpath(__file__)
    store_dir = os.path.normpath(
        os.path.join(file_path, "../testdata/data/store/occrp_web_site")
    )
    shutil.rmtree(store_dir, ignore_errors=True)

    # echo user-agent
    url = "https://httpbin.org/user-agent"
    result = context.http.get(url, headers={"User-Agent": "Memorious Test"})
    data = result.serialize()
    directory(context, data)

    mocker.patch.object(AlephAPI, "load_collection_by_foreign_id", mock_AlephApi)
    mocker.patch.object(AlephAPI, "ingest_upload", mock_ingest_upload)
    mocker.patch.object(context, "emit")

    ingest_spy = mocker.spy(AlephAPI, "ingest_upload")
    load_spy = mocker.spy(context, "load_file")
    emit_spy = mocker.spy(context, "emit")

    context.stage.aleph_cid = "aleph_cid"
    aleph_emit_document(context, data)

    assert load_spy.call_count == 1
    assert ingest_spy.call_count == 1
    assert emit_spy.call_count == 1


def test_get_collection_id(context: Context, mocker):
    mocker.patch.object(AlephAPI, "load_collection_by_foreign_id", mock_AlephApi)

    collection_id = get_collection_id(context, AlephAPI)
    assert collection_id is "aleph_cid"

    context.stage.aleph_cid = "alternate_aleph_cid"
    collection_id = get_collection_id(context, AlephAPI)
    assert collection_id is "alternate_aleph_cid"


def mock_get_tag(key):
    return {
        "id": "12345",
    }


def mock_AlephApi(foreign_id=None, config=None):
    return {"id": "aleph_cid"}


def mock_ingest_upload(collection_id, file_path, meta, sync=False, index=True):
    return {"id": "document_id"}
