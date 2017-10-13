import pkg_resources
from sqlalchemy import func, distinct
from sqlalchemy.orm import aliased
from datetime import datetime, timedelta

from memorious.core import session, manager
from memorious.model import Event, Operation


def crawlers_index():
    """Generate a list of all crawlers, sorted alphabetically, with op
    counts."""
    # query for overall run and operations count:
    op = aliased(Operation)
    q = session.query(
        op.crawler,
        func.count(distinct(op.run_id)).label('runs'),
        func.count(op.id).label('operations'),
    )
    q = q.group_by(op.crawler)
    counts = {}
    for (name, runs, operations) in q:
        counts[name] = {
            'runs': runs,
            'operations': operations
        }

    # query for error and warning events:
    event = aliased(Event)
    q = session.query(
        event.crawler,
        event.level,
        func.count(event.id).label('operations'),
    )
    q = q.group_by(event.crawler, event.level)
    for (name, level, count) in q:
        if name not in counts:
            counts[name] = {}
        counts[name][level] = count

    # make sure we're including crawlers that have never been run:
    crawlers = []
    for crawler in manager:
        data = counts.get(crawler.name, {})
        data['crawler'] = crawler
        crawlers.append(data)
    return crawlers


def global_stats():
    stats = {
        'version': pkg_resources.get_distribution('memorious').version,
        'num_crawlers': len(manager)
    }

    steps = (('ops_last_hour', timedelta(hours=1)),
             ('ops_last_day', timedelta(days=1)))
    for (field, delta) in steps:
        q = session.query(func.count(Operation.id))
        q = q.filter(Operation.started_at >= datetime.utcnow() - delta)
        stats[field] = q.scalar()
    return stats
