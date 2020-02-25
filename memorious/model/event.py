import logging

from servicelayer.util import pack_now, unpack_datetime, unpack_int
from servicelayer.util import dump_json, load_json
from servicelayer.cache import make_key
from servicelayer.settings import REDIS_EXPIRE, REDIS_LONG

from memorious.core import conn
from memorious.model.crawl import Crawl

log = logging.getLogger(__name__)


class Event(object):
    """Document errors and warnings caused during tasks."""
    LEVEL_WARNING = 'warning'
    LEVEL_ERROR = 'error'
    LEVELS = [LEVEL_WARNING, LEVEL_ERROR]

    @classmethod
    def save(cls, crawler, stage, level, run_id, error=None, message=None):
        """Create an event, possibly based on an exception."""
        event = {
            'stage': stage.name,
            'level': level,
            'timestamp': pack_now(),
            'error': error,
            'message': message
        }
        data = dump_json(event)
        keys = [
            make_key(crawler, "events"),
            make_key(crawler, "events", level),
            make_key(crawler, "events", stage),
            make_key(crawler, "events", stage, level),
            make_key(crawler, "events", run_id),
            make_key(crawler, "events", run_id, level),
        ]
        for key in keys:
            conn.lpush(key, data)
            conn.expire(key, REDIS_EXPIRE)
        # Persist the counts for longer
        count_keys = [
            make_key(crawler, "events", "count", level),
            make_key(crawler, "events", "count", stage, level),
            make_key(crawler, "events", "count", run_id, level),
        ]
        for key in count_keys:
            conn.incr(key)
            conn.expire(key, REDIS_LONG)
        return event

    @classmethod
    def delete(cls, crawler):
        cls.delete_data(crawler)
        cls.delete_counts(crawler)

    @classmethod
    def delete_data(cls, crawler):
        conn.delete(make_key(crawler, "events"))
        for level in cls.LEVELS:
            conn.delete(make_key(crawler, "events", level))
        for run_id in Crawl.run_ids(crawler):
            conn.delete(make_key(crawler, "events", run_id))
            for level in cls.LEVELS:
                conn.delete(make_key(crawler, "events", run_id, level))
        for stage in crawler.stages.keys():
            conn.delete(make_key(crawler, "events", stage))
            for level in cls.LEVELS:
                conn.delete(make_key(crawler, "events", stage, level))

    @classmethod
    def delete_counts(cls, crawler):
        for level in cls.LEVELS:
            conn.delete(make_key(crawler, "events", "count", level))
        for run_id in Crawl.run_ids(crawler):
            for level in cls.LEVELS:
                conn.delete(make_key(crawler, "events", "count", run_id, level))  # noqa
        for stage in crawler.stages.keys():
            for level in cls.LEVELS:
                conn.delete(make_key(crawler, "events", "count", stage, level))

    @classmethod
    def get_counts(cls, crawler):
        counts = {}
        for level in cls.LEVELS:
            key = make_key(crawler, "events", "count", level)
            counts[level] = unpack_int(conn.get(key))
        return counts

    @classmethod
    def get_stage_counts(cls, crawler, stage):
        counts = {}
        for level in cls.LEVELS:
            key = make_key(crawler, "events", "count", stage, level)
            counts[level] = unpack_int(conn.get(key))
        return counts

    @classmethod
    def get_run_counts(cls, crawler, run_id):
        counts = {}
        for level in cls.LEVELS:
            key = make_key(crawler, "events", "count", run_id, level)
            counts[level] = unpack_int(conn.get(key))
        return counts

    @classmethod
    def event_list(cls, key, start, end):
        results = []
        events = conn.lrange(key, start, end)
        if events is None:
            return results
        for event in events:
            result = load_json(event)
            result["timestamp"] = unpack_datetime(result['timestamp'])
            results.append(result)
        return results

    @classmethod
    def get_crawler_events(cls, crawler, start, end, level=None):
        key = make_key(crawler, "events", level)
        return cls.event_list(key, start, end)

    @classmethod
    def get_stage_events(cls, crawler, stage_name, start, end, level=None):
        """events from a particular stage"""
        key = make_key(crawler, "events", stage_name, level)
        return cls.event_list(key, start, end)

    @classmethod
    def get_run_events(cls, crawler, run_id, start, end, level=None):
        """Events from a particular run"""
        key = make_key(crawler, "events", run_id, level)
        return cls.event_list(key, start, end)
