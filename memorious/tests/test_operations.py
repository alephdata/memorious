import os
import json
from unittest.mock import ANY

import pytest

from memorious.operations.fetch import fetch, session
from memorious.operations.parse import parse
from memorious.operations.initializers import seed, sequence, dates, enumerate
from memorious.operations.store import directory
from memorious.core import connect_redis


@pytest.mark.parametrize("url,call_count", [
    ("https://httpbin.org/html", 1),
    ("https://occrp.org/", 0),
    ("https://httpbin.org/status/418", 0)
])
def test_fetch(url, call_count, context, mocker):
    rules = {'pattern': 'https://httpbin.org/*'}
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
    assert (
        context.http.session.headers["User-Agent"] == "Godzilla Firehose 0.1"
    )
    assert context.http.session.headers["Referer"] == "https://httpbin.org/get"
    assert context.http.session.auth == ("user", "password")


def test_parse(context, mocker):
    url = "http://example.org/"
    result = context.http.get(url)
    data = result.serialize()

    mocker.patch.object(context, "emit")

    rules = {'pattern': 'https://httpbin.org/*'}
    context.params["store"] = rules
    context.params["meta"] = {
        "title": ".//h1",
        "description": ".//p"
    }
    parse(context, data)
    assert context.emit.call_count == 1
    context.emit.assert_called_once_with(rule="fetch", data=ANY)

    # cleanup tags
    conn = connect_redis()
    conn.flushall()

    context.http.result = None
    context.params["store"] = None
    parse(context, data)
    assert data['url'] == 'https://www.iana.org/domains/example'
    assert data['title'] == 'Example Domain'
    assert data['description'].startswith('This domain is for')
    assert context.emit.call_count == 3, data


def test_seed(context, mocker):
    context.params["url"] = None
    context.params["urls"] = [
        "http://httpbin.org/status/%(status)s"
    ]
    mocker.patch.object(context, "emit")
    seed(context, data={"status": 404})
    assert context.emit.call_count == 1
    context.emit.assert_called_once_with(
        data={"url": "http://httpbin.org/status/404"}
    )


def test_sequence(context, mocker):
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


def test_dates(context, mocker):
    mocker.patch.object(context, "emit")
    mocker.patch.object(context, "recurse")
    context.params["format"] = '%d-%m-%Y'
    context.params["days"] = 3
    context.params["begin"] = "10-12-2012"
    context.params["end"] = "20-12-2012"
    dates(context, data={})
    assert context.emit.call_count == 1
    context.emit.assert_called_once_with(data={
        "date": "20-12-2012",
        "date_iso": "2012-12-20T00:00:00"
    })
    assert context.recurse.call_count == 1
    context.recurse.assert_called_once_with(
        data={"current": "17-12-2012"}
    )


def test_enumerate(context, mocker):
    mocker.patch.object(context, "emit")
    context.params["items"] = [1, 2, 3]
    enumerate(context, data={})
    assert context.emit.call_count == 3
    # expected_calls = [
    #     mocker.call(data={"item": 1}),
    #     mocker.call(data={"item": 2}),
    #     mocker.call(data={"item": 3}),
    # ]
    # assert context.emit.mock_calls == expected_calls
    # Ideally this should work, but currently it doesn't; because we pass
    # the reference to data dict around and then mutate it.


def test_directory(context):
    # echo user-agent
    url = "https://httpbin.org/user-agent"
    result = context.http.get(url, headers={"User-Agent": "Memorious Test"})
    data = result.serialize()
    directory(context, data)

    content_hash = data.get('content_hash')
    file_path = os.path.realpath(__file__)
    store_dir = os.path.normpath(os.path.join(
        file_path, "../testdata/data/store/occrp_web_site"
    ))

    raw_file_path = os.path.join(store_dir, content_hash + ".data.json")
    meta_file_path = os.path.join(store_dir, content_hash + ".json")
    assert os.path.exists(meta_file_path)
    assert os.path.exists(raw_file_path)

    with open(meta_file_path, "rb") as fh:
        assert json.load(fh)['content_hash'] == data['content_hash']
    with open(raw_file_path, "rb") as fh:
        assert b'"user-agent": "Memorious Test"' in fh.read()
