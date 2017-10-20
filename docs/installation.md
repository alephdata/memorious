# Installation (running your own crawlers)

We recommend using [Docker Compose](https://docs.docker.com/compose/) to run your crawlers in production, and we have an [example project](https://github.com/alephdata/memorious/tree/master/example) to help you get started.

* Make a copy of the `memorious/example` directory.
* Add your own crawler YAML configurations into the `config` directory.
* Add your Python extensions into the `src` directory (if applicable).
* Update `setup.py` with the name of your project and any additional dependencies.
* If you need to (eg. if your database connection or directory structure is different), update any environment variables in the `Dockerfile` or `docker-compose.yml`, although the defaults should work fine.
* Run `docker-compose up -d`. This might take a while when it's building for the first time.

You can access the Memorious CLI through the `worker` container:

```
docker-compose run --rm worker /bin/bash
```

To see the crawlers available to you:

```
memorious list
```

And to run a crawler:

```
memorious run my_crawler
```

See [Usage](https://memorious.readthedocs.io/en/latest/usage.html) (or run `memorious --help`) for the complete list of Memorious commands.

*Note: you can use any directory structure you like, `src` and `config` are not required, and nor is separation of YAML and Python files. So long as the `MEMORIOUS_CONFIG_PATH` environment variable points to a directory containing, within any level of directory nesting, your YAML files, Memorious will find them.*

## Environment variables

Your Memorious instance is configured by a set of environment variables that control database connectivity and general principles of how the sytem operates. You can set all of these in the `Dockerfile`.

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

## Shut it down

To gracefully exit, run `docker-compose down`.

Files which were downloaded by crawlers you ran, Memorious progress data from the Postgres database, and the RabbitMQ queue, are all persisted in the `build` directory, and will be reused next time you start it up. (If you need a completely fresh start, you can delete this directory).

## Building a crawler

To understand what goes into your `config` and `src` directories, check out the [examples](https://github.com/alephdata/memorious/tree/master/example) and [reference documentation](https://memorious.readthedocs.io/en/latest/buildingcrawler.html).

### Development mode

When you're working on your crawlers, it's not convenient to rebuild your Docker containers all the time. To run without Docker:

* Copy the environment variables from the `Dockerfile` to `env.sh`.
* Run `source env.sh`.

If you leave ``MEMORIOUS_DATABASE_URI`` unset, it will use SQLite. Otherwise you need to set it to match a local Postgres database.

Make sure ``MEMORIOUS_CONFIG_PATH`` points to your crawler YAML files, wherever they may be.

Then either:

* Run `pip install memorious`. If your crawlers use Python extensions, you'll need to run `pip install` in your crawlers directory as well;
* **or** clone the [Memorious repository](https://github.com/alephdata/memorious) and run `make install` (this will also install your crawlers for you).

