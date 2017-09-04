import click
import logging
from tabulate import tabulate
from sqlalchemy import create_engine

from funes.core import config, store
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
    config.set('cache', cache)
    config.set('incremental', incremental)
    config.set('debug', debug)
    if config.get_bool('debug'):
        logging.basicConfig(level=logging.DEBUG)
    if config.get('crawlers_path') is None:
        raise NoPathException('You need to set a path to your crawlers directory.') # noqa


@cli.command()
def init():
    """Connect to the database and create the tables."""
    if config.get('database_uri') is None:
        raise RuntimeError("No $FUNES_DATABASE_URI is set, aborting.")
    from funes.model.common import Base
    from funes.model.event import Event
    from funes.model.result import Result
    from funes.model.result import HTTPResult
    from funes.model.op import Operation
    engine = create_engine(config['database_uri'])
    Base.metadata.create_all(engine)
    log.info('Database models created for %r', config.get('database_uri'))


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
    print(tabulate(crawler_list, headers=['Name', 'Description', 'Schedule', 'Due']))


@cli.command()
def scheduled():
    """Run crawlers that are due."""
    run_scheduled()

def main():
    cli(obj={})


if __name__ == '__main__':
    main()
