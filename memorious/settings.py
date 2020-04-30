import os
import pkg_resources
import multiprocessing
from servicelayer import env
from servicelayer import settings as sls

###############################################################################
# Core configuration
VERSION = pkg_resources.get_distribution('memorious').version
APP_NAME = env.get('MEMORIOUS_APP_NAME', 'memorious')

# Enable debug logging etc.
DEBUG = env.to_bool('MEMORIOUS_DEBUG', default=False)
TESTING = False

# Base operating path
BASE_PATH = os.path.join(os.getcwd(), 'data')
BASE_PATH = env.get('MEMORIOUS_BASE_PATH', BASE_PATH)

# Override servicelayer archive if undefined
sls.ARCHIVE_PATH = sls.ARCHIVE_PATH or os.path.join(BASE_PATH, 'archive')

# Directory which contains crawler pipeline YAML specs
CONFIG_PATH = env.get('MEMORIOUS_CONFIG_PATH')

# Try and run scrapers in a way that only acquires new data
INCREMENTAL = env.to_bool('MEMORIOUS_INCREMENTAL', default=True)

# How many days until an incremental crawl expires
EXPIRE = env.to_int('MEMORIOUS_EXPIRE', 1)

# How many db inserts per minute
DB_RATE_LIMIT = env.to_int('MEMORIOUS_DB_RATE_LIMIT', 6000)

# How many http requests to a host per minute
HTTP_RATE_LIMIT = env.to_int('MEMORIOUS_HTTP_RATE_LIMIT', 120)

# How many seconds to wait before trying to run scheduled crawlers
SCHEDULER_INTERVAL = env.to_int('MEMORIOUS_SCHEDULER_INTERVAL', 60)

# Max scheduled tasks at the same time
MAX_SCHEDULED = max(env.to_int('MEMORIOUS_MAX_SCHEDULED', multiprocessing.cpu_count()), 20)   # noqa

# How many seconds to wait before timing out a crawler
CRAWLER_TIMEOUT = env.to_int('MEMORIOUS_CRAWLER_TIMEOUT', 3600 * 6)

# Max number of tasks in a stage's task queue
MAX_QUEUE_LENGTH = env.to_int('MEMORIOUS_MAX_QUEUE_LENGTH', 50000)

# HTTP request configuration
HTTP_CACHE = env.to_bool('MEMORIOUS_HTTP_CACHE', default=True)

# HTTP user agent default
USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.1)'
USER_AGENT = '%s aleph.memorious/%s' % (USER_AGENT, VERSION)
USER_AGENT = env.get('MEMORIOUS_USER_AGENT', USER_AGENT)

# Datastore: operational data store (ODS) database connection
DATASTORE_FILE = os.path.join(BASE_PATH, 'datastore.sqlite3')
DATASTORE_URI = 'sqlite:///%s' % DATASTORE_FILE
DATASTORE_URI = env.get('MEMORIOUS_DATASTORE_URI', DATASTORE_URI)
