# memorious

``memorious`` is a distributed web scraping toolkit. It is a light-weight tool
that schedules, monitors and supports scrapers that collect structured or
un-structured data. This includes the following use cases:

* Maintain an overview of a fleet of crawlers
* Schedule crawler execution in regular intervals
* Store execution information and error messages
* Distribute scraping tasks across multiple machines
* Make crawlers modular and simple tasks re-usable
* Get out of your way as much as possible

## Design

When writing a scraper, you often need to paginate through through an index
page, then download an HTML page for each result and finally parse that page
and insert or update a record in a database.

``memorious`` handles this by managing a set of ``crawlers``, each of which 
can be composed of multiple ``stages``. Each ``stage`` is implemented using a
Python function, which can be re-used across different ``crawlers``.

## Installation

Lots of commands you need are in the [Makefile](https://github.com/alephdata/memorious/blob/master/Makefile).

### With Docker (production)

1. Configure the environment variables in `docker-compose.yml` and 
`memorious.env`. 
2. Copy your crawlers (yaml and optional python files, see next section) into 
the `crawlers` directory.
3. Run:

```sh
$ make build
$ docker-compose up -d 
```

This launches a celery worker and scheduler, as well as containers for 
PostgreSQL and RabbitMQ.

To access the shell, use:

```sh
$ make shell
```

If you add new crawlers, you'll need to rebuild.

(TODO: find a way to avoid rebuilding?)

### Development mode

To set the ``MEMORIOUS_*`` environment variables, modify `env.sh` (*before* 
running `make install`). See the next section for configuration options.

Set up Postgres. Either create a database is called `funes`, with username and
password also `funes`, or updated the `MEMORIOUS_DATABASE_URI` environment
variable in `env.sh` to match your local database. [TODO: make this run with 
SQLite](https://github.com/alphedata/memorious/issues/8).

```sh
$ git clone git@github.com:alephdata/memorious.git memorious
$ cd memorious
$ virtualenv env
$ source env/bin/activate
$ make install
```

As well as installing ``memorious``, this looks for a setup.py in your 
`MEMORIOUS_CONFIG_PATH` and runs pip install if it finds one. (This isn't 
needed if you only have yaml configurations - see the next two sections).

## Configuration

There are two principal components to the configuration of ``memorious``. A
set of environment variables that control database connectivity and general
principles of how the sytem operates. 

A recursive folder of YAML configuration files are used to specify the 
operation of each individual crawler.

### Environment variables

* ``MEMORIOUS_DATABASE_URI``
* ``MEMORIOUS_CONFIG_PATH``
* ``MEMORIOUS_DEBUG``
* ``MEMORIOUS_INCREMENTAL``
* ``MEMORIOUS_HTTP_CACHE``
* ``MEMORIOUS_DATASTORE_URI``
* ``MEMORIOUS_BROKER_URI``
* ``MEMORIOUS_EAGER``

* ``MEMORIOUS_ARCHIVE_TYPE``, either ``file`` or ``s3``
* ``MEMORIOUS_ARCHIVE_PATH``
* ``MEMORIOUS_ARCHIVE_AWS_KEY_ID``
* ``MEMORIOUS_ARCHIVE_AWS_SECRET``
* ``MEMORIOUS_ARCHIVE_AWS_REGION``
* ``MEMORIOUS_ARCHIVE_BUCKET``

* ``ALEPH_HOST``, default is ``https://data.occrp.org/``, but any instance
  of Aleph 2.0 or greater should work.
* ``ALEPH_API_KEY``, a valid API key for use by the upload operation.

### Crawler configuration files

For simple crawlers which don't need to extend ``memorious``, you just need
a yaml configuration file per crawler.

You can configure more complex crawlers to execute custom python functions. You 
should package your python modules with a `setup.py` and include along them with 
your yaml files.

See 'Writing a crawler' below for what these files should contain.

You can arrange the files using any directory structure you like, ``memorious`` will
find them. You might, for example, like to put your yaml config and python source
files in different directories. If you have a lot of crawlers, you can organise
these into different subdirectories or python modules.

If you're running ``memorious`` with Docker, your package will be installed at
build time. If not, you'll need to run `pip install` in the `crawlers` directory.

..TODO..

## Usage

``memorious`` is controlled via a command-line tool, which can be used to monitor
or invoke a crawler interactively. Most of the actual work, however, is handled
by a daemon service running in the background. Communication between different
components is handled via a central message queue.

See the status of all crawlers managed by memorious:

```sh
memorious list
```

Force an immediate run of a specific crawler:

```sh
memorious run my_crawler
```

Check which crawlers are due for scheduled execution and execute the ones that
need to be updated:

```sh
memorious scheduled
```

Clear all the run status and cached information associated with a crawler:

```sh
memorious flush my_crawler
```

## Writing a crawler

TODO

1. Make YAML crawler configuration file
2. Add different stages
3. Write code for stage operations
4. Test, rinse, repeat

## Development

### Making a migration

To autogenerate a migration:

```sh
$ cd memorious/migration
$ alembic revision --autogenerate -m 'message'
```

Then edit to make it actually work and remove surplus changes. We're generally
not aiming to support downgrades.

## Licensing

see ``LICENSE``
