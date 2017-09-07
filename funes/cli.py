import click
import logging
from tabulate import tabulate

from funes import settings
from funes.core import manager, session
from funes.model.common import Base

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
    Base.metadata.create_all(session.bind)
    log.info('Database models created: %s', session.bind)


@cli.command()
@click.argument('crawler')
def run(crawler):
    """Run a specified crawler."""
    crawler_obj = manager.get(crawler)
    if crawler_obj is None:
        log.info('Crawler [%s] not found.', crawler)
        return
    crawler_obj.run()


@cli.command()
def list():
    """List the available crawlers."""
    crawler_list = []
    for crawler in manager:
        is_due = 'yes' if crawler.check_due() else 'no'
        crawler_list.append([crawler.name,
                             crawler.description,
                             crawler.schedule,
                             is_due])
    headers = ['Name', 'Description', 'Schedule', 'Due']
    print(tabulate(crawler_list, headers=headers))


@cli.command()
def scheduled():
    """Run crawlers that are due."""
    manager.run_scheduled()


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
