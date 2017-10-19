import math
from sqlalchemy import func, distinct
from sqlalchemy.orm import aliased
from datetime import datetime, timedelta

from memorious import settings
from memorious.core import session, manager
from memorious.model import Event, Operation


def global_stats():
    """Stats visible on each page of the UI."""
    stats = {
        'version': settings.VERSION,
        'num_crawlers': len(manager)
    }

    steps = (('ops_last_hour', timedelta(hours=1)),
             ('ops_last_day', timedelta(days=1)))
    for (field, delta) in steps:
        q = session.query(func.count(Operation.id))
        q = q.filter(Operation.started_at >= datetime.utcnow() - delta)
        stats[field] = q.scalar()
    return stats


def crawlers_index():
    """Generate a list of all crawlers, sorted alphabetically, with op
    counts."""
    # query for overall run and operations count:
    op = aliased(Operation)
    q = session.query(
        op.crawler,
        func.count(distinct(op.run_id)),
        func.count(op.id),
        func.max(op.started_at),
    )
    q = q.group_by(op.crawler)
    counts = {}
    for (name, runs, operations, last_active) in q:
        counts[name] = {
            'runs': runs,
            'operations': operations,
            'last_active': last_active,
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


def get_crawler(name):
    return manager.get(name)


def crawler_stages(crawler):
    """See the number of executions of each stage."""
    counts = {}

    # operation runs per stage name, status
    op = aliased(Operation)
    q = session.query(
        op.name,
        op.status,
        func.count(op.id),
    )
    q = q.filter(op.crawler == crawler.name)
    q = q.group_by(op.name, op.status)
    counts = {}
    for (name, status, count) in q:
        if name not in counts:
            counts[name] = {}
        counts[name][status] = count

    # events by level
    op = aliased(Operation)
    evt = aliased(Event)
    q = session.query(
        op.name,
        evt.level,
        func.count(evt.id),
    )
    q = q.filter(evt.operation_id == op.id)
    q = q.filter(op.crawler == crawler.name)
    q = q.group_by(op.name, evt.level)
    for (name, level, count) in q:
        if name not in counts:
            counts[name] = {}
        counts[name][level] = count

    stages = []
    for stage in crawler:
        data = counts.get(stage.name, {})
        data['stage'] = stage
        stages.append(data)
    return stages


# def crawler_runs(crawler):
#     pass


def crawler_events(crawler, run_id=None, level=None, stage=None,
                   page=1, per_page=15):
    evt = aliased(Event)
    op = aliased(Operation)
    q = session.query(evt, op)
    q = q.join(op, op.id == evt.operation_id)
    q = q.filter(evt.crawler == crawler.name)
    if level is not None:
        q = q.filter(evt.level == level)
    if run_id is not None:
        q = q.filter(op.run_id == run_id)
    if stage is not None:
        q = q.filter(op.name == stage)

    total = q.count()
    q = q.order_by(evt.timestamp.desc())
    q = q.limit(per_page)
    q = q.offset((max(1, page) - 1) * per_page)

    results = []
    for (event, operation) in q:
        results.append({
            'event': event,
            'operation': operation
        })

    return {
        'page': page,
        'per_page': per_page,
        'pages': int(math.ceil((float(total) / per_page))),
        'total': total,
        'results': results
    }
