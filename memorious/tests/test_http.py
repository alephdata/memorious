import os
import pytest
from requests import Session, Response, Request
from lxml import html, etree

from memorious.logic.http import ContextHttpResponse


class TestContextHttp(object):
    def test_session(self, http):
        assert isinstance(http.session, Session)

    def test_response(self, http):
        response = http.get("https://httpbin.org/get")
        assert isinstance(response, ContextHttpResponse)
        assert isinstance(response._response, Response)

    def test_response_lazy(self, http):
        response = http.get("https://httpbin.org/get", lazy=True)
        assert isinstance(response, ContextHttpResponse)
        assert response._response is None


class TestContextHttpResponse(object):
    def test_fetch_response(self, http):
        request = Request("GET", "https://httpbin.org/get")
        context_http_response = ContextHttpResponse(http, request)
        file_path = context_http_response.fetch()
        assert os.path.exists(file_path)

    def test_contenttype(self, http):
        request = Request("GET", "https://httpbin.org/get")
        context_http_response = ContextHttpResponse(http, request)
        assert context_http_response.content_type == "application/json"

    def test_attachment(self, http):
        request = Request(
            "GET", "https://httpbin.org/response-headers?Content-Type="
            "text/plain;%20charset=UTF-8&Content-Disposition=attachment;"
            "%20filename%3d%22test.json%22"
        )
        context_http_response = ContextHttpResponse(http, request)
        assert context_http_response.file_name == "test.json"

    @pytest.mark.parametrize("url,encoding", [
        ("https://httpbin.org/response-headers?charset=", "utf-8"),
        ("https://httpbin.org/response-headers?content-type=text"
         "/plain;%20charset=utf-16", "utf-16"),
        ("https://httpbin.org/response-headers?Content-Type=text/"
         "plain;%20charset=utf-32", "utf-32")
    ])
    def test_encoding(self, url, encoding, http):
        request = Request("GET", url)
        context_http_response = ContextHttpResponse(http, request)
        assert context_http_response.encoding == encoding

    def test_request_id(self, http):
        request = Request(
            "GET", "https://httpbin.org/get", data={"hello": "world"}
        )
        context_http_response = ContextHttpResponse(http, request)
        assert context_http_response._request_id is None
        assert isinstance(context_http_response.request_id, str)

    def test_content(self, http):
        request = Request(
            "GET", "https://httpbin.org/user-agent",
            headers={"User-Agent": "Memorious Test"}
        )
        context_http_response = ContextHttpResponse(http, request)
        assert isinstance(context_http_response.raw, bytes)
        assert isinstance(context_http_response.text, str)
        assert context_http_response.json == {"user-agent": "Memorious Test"}

    def test_html(self, http):
        request = Request("GET", "https://httpbin.org/html")
        context_http_response = ContextHttpResponse(http, request)
        assert isinstance(context_http_response.html, html.HtmlElement)

    def test_xml(self, http):
        request = Request("GET", "https://httpbin.org/xml")
        context_http_response = ContextHttpResponse(http, request)
        assert isinstance(context_http_response.xml, etree._ElementTree)

    def test_apply_data(self, http):
        context_http_response = ContextHttpResponse(http)
        assert context_http_response.url is None
        assert context_http_response.status_code is None
        context_http_response.apply_data(data={
            "status_code": 200,
            "url": "https://httpbin.org/get"
        })
        assert context_http_response.url == "https://httpbin.org/get"
        assert context_http_response.status_code == 200

    def test_deserialize(self, http):
        data = {
            "status_code": 200,
            "url": "https://httpbin.org/get"
        }
        context_http_response = ContextHttpResponse.deserialize(http, data)
        assert isinstance(context_http_response, ContextHttpResponse)
        assert context_http_response.url == "https://httpbin.org/get"
        assert context_http_response.status_code == 200

    def test_close(self, http):
        request = Request("GET", "https://httpbin.org/get")
        context_http_response = ContextHttpResponse(http, request)
        file_path = context_http_response.fetch()
        assert os.path.exists(file_path)
        context_http_response.close()
        # assert not os.path.exists(file_path)

    @pytest.mark.parametrize("url,status_code", [
        ("https://httpbin.org/status/404", 404),
        ("https://httpbin.org/status/500", 500),
        ("https://httpbin.org/status/200", 200)
    ])
    def test_status_code(self, url, status_code, http):
        request = Request("GET", url)
        context_http_response = ContextHttpResponse(http, request)
        assert context_http_response.status_code == status_code
