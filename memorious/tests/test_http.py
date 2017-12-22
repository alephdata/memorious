import os
from requests import Session, Response, Request
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
        request = Request(
            "GET", "http://httpbin.org/response-headers?Content-Type=text/plain;"
            "%20charset=UTF-8&Content-Disposition=attachment;%20filename%3d%22"
            "test.json%22"
        )
        context_http_response = ContextHttpResponse(http, request)
        file_path = context_http_response.fetch()
        assert os.path.exists(file_path)

    def test_contenttype(self, http):
        request = Request(
            "GET", "http://httpbin.org/response-headers?Content-Type=text/plain;"
            "%20charset=UTF-8&Content-Disposition=attachment;%20filename%3d%22"
            "test.json%22"
        )
        context_http_response = ContextHttpResponse(http, request)
        assert context_http_response.content_type == "application/json, text/plain"

    def test_attachment(self, http):
        request = Request(
            "GET", "http://httpbin.org/response-headers?Content-Type=text/plain;"
            "%20charset=UTF-8&Content-Disposition=attachment;%20filename%3d%22"
            "test.json%22"
        )
        context_http_response = ContextHttpResponse(http, request)
        assert context_http_response.file_name == "test.json"

    def test_encoding(self, http):
        request = Request(
            "GET", "http://httpbin.org/response-headers?Content-Type=text/plain;"
            "%20charset=UTF-8&Content-Disposition=attachment;%20filename%3d%22"
            "test.json%22"
        )
        context_http_response = ContextHttpResponse(http, request)
        assert context_http_response.encoding == "utf-8"
