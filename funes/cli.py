import click
import logging
from tabulate import tabulate

from funes import settings
from funes.core import store, session
from funes.model.common import Base
from funes.run import run_crawler, run_scheduled
from funes.tools.schedule import Schedule

log = logging.getLogger(__name__)


@click.group()
@click.option('--debug/--no-debug', default=False,
              envvar='FUNES_DEBUG')
@click.option('--cache/--no-cache', default=True,
              envvar='FUNES_REQUESTS_CACHE')
@click.option('--incremental/--non-incremental', default=True,
              envvar='FUNES_INCREMENTAL')
def cli(debug, cache, incremental):
    """Crawler framework for documents and structured scrapers."""
    settings.HTTP_CACHE = cache
    settings.INCREMENTAL = incremental
    settings.DEBUG = debug
    if settings.DEBUG:
        logging.basicConfig(level=logging.DEBUG)


@cli.command()
def init():
    """Connect to the database and create the tables."""
    Base.metadata.create_all(session.engine)
    log.info('Database models created: %s', session.engine)


@cli.command()
@click.argument('crawler')
def run(crawler):
    """Run a specified crawler."""
    if crawler is None:
        log.info('You must specify a crawler.')
        return
    if store.crawlers.get(crawler) is None:
        log.info('Crawler [%s] not found.', crawler)
        return
    run_crawler(crawler)


@cli.command()
def list():
    """List the available crawlers."""
    crawler_list = []
    for name, crawler in store.crawlers.items():
        schedule = crawler.get('schedule')
        is_due = 'no'
        if Schedule.check_due(name, schedule):
            is_due = 'yes'
        crawler_list.append([name, crawler.get('description'),
                            schedule, is_due])
    headers = ['Name', 'Description', 'Schedule', 'Due']
    print(tabulate(crawler_list, headers=headers))


@cli.command()
def scheduled():
    """Run crawlers that are due."""
    run_scheduled()


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
