from os import environ


def env(name, default=None, required=False):
    name = 'MEMORIOUS_%s' % name.upper().strip()
    if required and name not in environ:
        raise RuntimeError("Missing configuration: $%s" % name)
    return environ.get(name, default)


def env_bool(name, default=False):
    """Extract a boolean value from the environment consistently."""
    value = env(name)
    if value is None:
        return default
    value = value.lower().strip()
    return value in ['t', '1', 'y', 'true', 'yes', 'enabled']


###############################################################################
# Core configuration

DEBUG = env_bool('DEBUG', default=False)

# Database connection string
DATABASE_URI = env('DATABASE_URI', required=True)

# Directory which contains crawler pipeline YAML specs
CONFIG_PATH = env('CONFIG_PATH', required=True)

# Try and run scrapers in a way that only acquires new data
INCREMENTAL = env_bool('INCREMENTAL', default=True)

# HTTP request configuration
HTTP_CACHE = env_bool('HTTP_CACHE', default=True)


###############################################################################
# Datastore: operational data store (ODS) database connection

DATASTORE_URI = env('DATASTORE_URI')


###############################################################################
# Queue processing

BROKER_URI = 'amqp://guest:guest@localhost:5672//'
BROKER_URI = env('BROKER_URI', BROKER_URI)

# Enable delayed processing via queue
EAGER = env_bool('EAGER', False)


###############################################################################
# Data storage

# Archive type (either 's3' or 'file', i.e. local file system):
ARCHIVE_TYPE = env('ARCHIVE_TYPE', 'file')
ARCHIVE_AWS_KEY_ID = env('AWS_ACCESS_KEY_ID')
ARCHIVE_AWS_SECRET = env('AWS_SECRET_ACCESS_KEY')
ARCHIVE_AWS_REGION = env('ARCHIVE_REGION', 'eu-west-1')
ARCHIVE_BUCKET = env('ARCHIVE_BUCKET')
ARCHIVE_PATH = env('ARCHIVE_PATH')


###############################################################################
# Aleph module

ALEPH_HOST = env('ALEPH_HOST')
ALEPH_API_KEY = env('ALEPH_API_KEY')
