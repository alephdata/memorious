import os
import uuid

import pytest

from memorious.logic.manager import CrawlerManager
from memorious.logic.context import Context
from memorious.logic.http import ContextHttp


@pytest.fixture(scope="module")
def crawler_dir():
    file_path = os.path.realpath(__file__)
    crawler_dir = os.path.normpath(os.path.join(
        file_path, "../testdata/config"
    ))
    return crawler_dir


@pytest.fixture(scope="module")
def manager():
    manager = CrawlerManager()
    manager.load_path(crawler_dir())
    return manager


@pytest.fixture(scope="module")
def crawler():
    return manager().get("occrp_web_site")


@pytest.fixture(scope="module")
def stage():
    cr = crawler()
    return cr.get(cr.init_stage)


@pytest.fixture(scope="module")
def context():
    ctx = Context(crawler(), stage(), {"foo": "bar"})
    ctx.run_id = str(uuid.uuid4())
    return ctx


@pytest.fixture(scope="module")
def http():
    return ContextHttp(context())
