import logging
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from memorious.operation import operation

__all__ = [operation]

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging.basicConfig(level=logging.INFO)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('alembic').setLevel(logging.WARNING)
logging.getLogger('zeep').setLevel(logging.WARNING)
logging.getLogger('httpstream').setLevel(logging.WARNING)
