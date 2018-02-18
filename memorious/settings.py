import os
import pkg_resources
import six
from banal import as_bool


def env(name, default=None, required=False):
    name = 'MEMORIOUS_%s' % name.upper().strip()
    if required and name not in os.environ:
        raise RuntimeError("Missing configuration: $%s" % name)
    return os.environ.get(name, default)


def env_bool(name, default=False):
    """Extract a boolean value from the environment consistently."""
    return as_bool(env(name), default=default)


###############################################################################
# Core configuration

VERSION = pkg_resources.get_distribution('memorious').version
APP_NAME = env('APP_NAME', 'memorious')

# Enable debug logging etc.
DEBUG = env_bool('DEBUG', default=False)

# Base operating path
BASE_PATH = env('BASE_PATH', os.path.join(six.moves.getcwd(), 'data'))

# Database connection string
DATABASE_FILE = os.path.join(BASE_PATH, 'memorious.sqlite3')
DATABASE_URI = env('DATABASE_URI', 'sqlite:///%s' % DATABASE_FILE)

# Directory which contains crawler pipeline YAML specs
CONFIG_PATH = env('CONFIG_PATH')

# Try and run scrapers in a way that only acquires new data
INCREMENTAL = env_bool('INCREMENTAL', default=True)

# How many days until an incremental crawl expires
EXPIRE = int(env('EXPIRE', 100))

# HTTP request configuration
HTTP_CACHE = env_bool('HTTP_CACHE', default=True)

# HTTP user agent default
USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.1)'
USER_AGENT = '%s aleph.memorious/%s' % (USER_AGENT, VERSION)
USER_AGENT = env('USER_AGENT', USER_AGENT)

# Datastore: operational data store (ODS) database connection
DATASTORE_FILE = os.path.join(BASE_PATH, 'datastore.sqlite3')
DATASTORE_URI = env('DATASTORE_URI', 'sqlite:///%s' % DATASTORE_FILE)


###############################################################################
# Queue processing

BROKER_URI = 'amqp://guest:guest@localhost:5672//'
BROKER_URI = env('BROKER_URI', BROKER_URI)

# Enable delayed processing via queue
EAGER = env_bool('EAGER', True)


###############################################################################
# Data storage

# Archive type (either 's3' or 'file', i.e. local file system):
ARCHIVE_TYPE = env('ARCHIVE_TYPE', 'file')
ARCHIVE_PATH = env('ARCHIVE_PATH', os.path.join(BASE_PATH, 'archive'))
ARCHIVE_AWS_KEY_ID = env('AWS_ACCESS_KEY_ID',
                         os.environ.get('AWS_ACCESS_KEY_ID'))
ARCHIVE_AWS_SECRET = env('AWS_SECRET_ACCESS_KEY',
                         os.environ.get('AWS_SECRET_ACCESS_KEY'))
ARCHIVE_AWS_REGION = env('ARCHIVE_REGION', 'eu-west-1')
ARCHIVE_BUCKET = env('ARCHIVE_BUCKET')


###############################################################################
# Aleph module

ALEPH_HOST = env('ALEPH_HOST')
ALEPH_API_KEY = env('ALEPH_API_KEY')


###############################################################################
# Error reporting

# Using sentry raven
SENTRY_DSN = env('SENTRY_DSN')


###############################################################################
# Redis

REDIS_HOST = env('REDIS_HOST', '')
REDIS_PORT = int(env('REDIS_PORT', 6379))
