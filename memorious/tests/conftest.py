import os
import uuid

import pytest

from memorious import settings
from memorious.logic.manager import CrawlerManager
from memorious.logic.context import Context
from memorious.logic.http import ContextHttp


settings.TESTING = True


def get_crawler_dir():
    file_path = os.path.realpath(__file__)
    crawler_dir = os.path.normpath(os.path.join(
        file_path, "../testdata/config"
    ))
    return crawler_dir


@pytest.fixture(scope="module")
def crawler_dir():
    return get_crawler_dir()


def get_manager():
    manager = CrawlerManager()
    manager.load_path(get_crawler_dir())
    settings._manager = manager
    return manager


@pytest.fixture(scope="module")
def manager():
    return get_manager()


def get_crawler():
    return get_manager().get("occrp_web_site")


@pytest.fixture(scope="module")
def crawler():
    return get_crawler()


def get_stage():
    cr = get_crawler()
    return cr.get(cr.init_stage)


@pytest.fixture(scope="module")
def stage():
    return get_stage()


def get_context():
    ctx = Context(get_crawler(), get_stage(), {"foo": "bar"})
    ctx.run_id = str(uuid.uuid4())
    return ctx


@pytest.fixture(scope="module")
def context():
    return get_context()


@pytest.fixture(scope="module")
def http():
    return ContextHttp(get_context())
