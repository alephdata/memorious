import math
import logging

from memorious import settings
from memorious.core import manager
from memorious.model import Event

log = logging.getLogger(__name__)


def global_stats():
    """Stats visible on each page of the UI."""
    stats = {
        'version': settings.VERSION,
        'num_crawlers': len(manager)
    }
    return stats


def crawlers_index():
    """Generate a list of all crawlers, sorted alphabetically, with op
    counts."""
    crawlers = []
    for crawler in manager:
        data = Event.get_counts(crawler)
        data['last_active'] = crawler.last_run
        data['total_ops'] = crawler.op_count
        data['running'] = crawler.is_running
        data['crawler'] = crawler
        crawlers.append(data)
    return crawlers


def get_crawler(name):
    return manager.get(name)


def crawler_stages(crawler):
    """See the number of executions of each stage."""
    stages = []
    for stage in crawler:
        data = Event.get_stage_counts(crawler, stage)
        data['total_ops'] = stage.op_count
        data['stage'] = stage
        stages.append(data)
    return stages


def crawler_events(crawler, level=None, stage_name=None,
                   run_id=None, page=1, per_page=15):
    start = (max(1, page) - 1) * per_page
    end = start + per_page

    if stage_name:
        events = Event.get_stage_events(crawler, stage_name, start, end, level)
    elif run_id:
        events = Event.get_run_events(crawler, run_id, start, end, level)
    else:
        events = Event.get_crawler_events(crawler, start, end, level)
    total = len(events)

    return {
        'page': page,
        'per_page': per_page,
        'pages': int(math.ceil((float(total) / per_page))),
        'total': total,
        'results': events
    }


def crawler_runs(crawler):
    runs = list(crawler.runs)
    for run in runs:
        run.update(Event.get_run_counts(crawler, run['run_id']))
    return runs
