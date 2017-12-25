import os

import pytest

from memorious.logic.manager import CrawlerManager
from memorious.logic.context import Context
from memorious.logic.http import ContextHttp
from memorious.core import ensure_db


ensure_db()


@pytest.fixture(scope="module")
def crawler_dir():
    file_path = os.path.realpath(__file__)
    crawler_dir = os.path.normpath(os.path.join(
        file_path, "../testdata/config"
    ))
    return crawler_dir


@pytest.fixture(scope="module")
def manager():
    return CrawlerManager(crawler_dir())


@pytest.fixture(scope="module")
def crawler():
    return manager().get("occrp_web_site")


@pytest.fixture(scope="module")
def stage():
    cr = crawler()
    return cr.get(cr.init_stage)


@pytest.fixture(scope="module")
def context():
    return Context(crawler(), stage(), {"foo": "bar"})


@pytest.fixture(scope="module")
def http():
    return ContextHttp(context())
