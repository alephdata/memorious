# Funes

``funes`` is a distributed web scraping toolkit. It is a light-weight tool that
schedules, monitors and supports scrapers that collect structured or
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

``funes`` handles this by managing a set of ``crawlers``, each of which can
be composed of multiple ``stages``. Each ``stage`` is implemented using a
Python function, which can be re-used across different ``crawlers``.

## Installation

see https://github.com/alephdata/funes/issues/1 for Docker. For now:

```sh
$ git clone git@github.com:alephdata/funes.git funes
$ cd funes
$ virtualenv env
$ source env/bin/activate
$ pip install -e .
# configure all needed environment variables, including database
# connection strings.
$ funes upgrade
```

## Configuraton

TODO

## Usage

``funes`` is controlled via a command-line tool, which can be used to monitor
or invoke a crawler interactively. Most of the actual work, however, is handled
by a daemon service running in the background. Communication between different
components is handled via a central message queue.

See the status of all crawlers managed by funes:

```sh
funes list
```

Force an immediate run of a specific crawler:

```sh
funes list
```

Check which crawlers are due for scheduled execution and execute the ones that
need to be updated:

```sh
funes scheduled
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
$ cd funes/migration
$ alembic revision --autogenerate -m 'message'
```

Then edit to make it actually work and remove surplus changes. We're generally
not aiming to support downgrades.

## Licensing

see ``LICENSE``
