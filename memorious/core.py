import logging
import dataset
from servicelayer import settings as sls
from servicelayer.archive import init_archive
from servicelayer.cache import get_redis, get_fakeredis
from servicelayer.extensions import get_extensions
from sqlalchemy.pool import NullPool
from werkzeug.local import LocalProxy

from memorious.services.ocr import (
    LocalOCRService, ServiceOCRService, GoogleOCRService
)
from memorious import settings

log = logging.getLogger(__name__)


def load_manager():
    if not hasattr(settings, '_manager'):
        from memorious.logic.manager import CrawlerManager
        settings._manager = CrawlerManager()
        if settings.CONFIG_PATH:
            settings._manager.load_path(settings.CONFIG_PATH)
    return settings._manager


def load_datastore():
    if not hasattr(settings, '_datastore'):
        if not settings.DATASTORE_URI:
            raise RuntimeError("No $MEMORIOUS_DATASTORE_URI.")
        # do not pool connections for the datastore
        engine_kwargs = {'poolclass': NullPool}
        settings._datastore = dataset.connect(settings.DATASTORE_URI,
                                              engine_kwargs=engine_kwargs)
        # Use bigint to store integers by default
        settings._datastore.types.integer = settings._datastore.types.bigint
    return settings._datastore


def is_sync_mode():
    if settings.TESTING or settings.DEBUG:
        return True
    return sls.REDIS_URL is None


def connect_redis():
    if settings.TESTING:
        return get_fakeredis()
    return get_redis()


def get_ocr():
    """Find the best available method to perform OCR."""
    if not hasattr(settings, '_ocr_service'):
        if GoogleOCRService.is_available():
            settings._ocr_service = GoogleOCRService()
        elif ServiceOCRService.is_available():
            settings._ocr_service = ServiceOCRService()
        elif LocalOCRService.is_available():
            settings._ocr_service = LocalOCRService()
        else:
            raise RuntimeError("OCR is not available")
    return settings._ocr_service


manager = LocalProxy(load_manager)
datastore = LocalProxy(load_datastore)
conn = LocalProxy(connect_redis)
ocr_service = LocalProxy(get_ocr)

# File storage layer for blobs on local file system or S3
storage = init_archive()


def init_memorious():
    for func in get_extensions('memorious.plugins'):
        func()
