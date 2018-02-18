import logging
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging.basicConfig(level=logging.INFO)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('alembic').setLevel(logging.WARNING)
logging.getLogger('zeep').setLevel(logging.WARNING)
logging.getLogger('httpstream').setLevel(logging.WARNING)
logging.getLogger('celery').setLevel(logging.WARNING)


# Register signal handlers
from . import signals  # noqa
