## Installation

Lots of commands you need are in the [Makefile](https://github.com/alephdata/memorious/blob/master/Makefile).

### Production (with Docker)

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

If you leave ``MEMORIOUS_DATABASE_URI`` unset, it will use SQLite.

Otherwise set the `MEMORIOUS_DATABASE_URI` environment
variable in `env.sh` to match your local Postgres database.

```sh
$ git clone git@github.com:alephdata/memorious.git memorious
$ cd memorious
$ virtualenv env
$ source env/bin/activate
$ make install
$ source env.sh
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

See 'Writing a crawler' for what these files should contain.

You can arrange the files using any directory structure you like, ``memorious`` will
find them. You might, for example, like to put your yaml config and python source
files in different directories. If you have a lot of crawlers, you can organise
these into different subdirectories or python modules.

If you're running ``memorious`` with Docker, your package will be installed at
build time. If not, you'll need to run `pip install` in the `crawlers` directory.