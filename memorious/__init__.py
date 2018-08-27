import logging
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('zeep').setLevel(logging.WARNING)
logging.getLogger('httpstream').setLevel(logging.WARNING)
