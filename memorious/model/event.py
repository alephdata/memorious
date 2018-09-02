import logging

from memorious.model.crawl import Crawl
from memorious.model.common import Base, pack_now, unpack_datetime
from memorious.model.common import dump_json, load_json
from memorious.util import make_key

log = logging.getLogger(__name__)


class Event(Base):
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
        cls.conn.lpush(make_key(crawler, "events"), data)
        cls.conn.lpush(make_key(crawler, "events", level), data)
        cls.conn.lpush(make_key(crawler, "events", stage), data)
        cls.conn.lpush(make_key(crawler, "events", stage, level), data)
        cls.conn.lpush(make_key(crawler, "events", run_id), data)
        cls.conn.lpush(make_key(crawler, "events", run_id, level), data)
        return event

    @classmethod
    def delete(cls, crawler):
        cls.conn.delete(make_key(crawler, "events"))
        for level in cls.LEVELS:
            cls.conn.delete(make_key(crawler, "events", level))
        for run_id in Crawl.run_ids(crawler):
            cls.conn.delete(make_key(crawler, "events", run_id))
            for level in cls.LEVELS:
                cls.conn.delete(make_key(crawler, "events", run_id, level))
        for stage in crawler.stages.keys():
            cls.conn.delete(make_key(crawler, "events", stage))
            for level in cls.LEVELS:
                cls.conn.delete(make_key(crawler, "events", stage, level))

    @classmethod
    def get_counts(cls, crawler):
        counts = {}
        for level in cls.LEVELS:
            key = make_key(crawler, "events", level)
            counts[level] = cls.conn.llen(key) or 0
        return counts

    @classmethod
    def get_stage_counts(cls, crawler, stage):
        counts = {}
        for level in cls.LEVELS:
            key = make_key(crawler, "events", stage, level)
            counts[level] = cls.conn.llen(key) or 0
        return counts

    @classmethod
    def get_run_counts(cls, crawler, run_id):
        counts = {}
        for level in cls.LEVELS:
            key = make_key(crawler, "events", run_id, level)
            counts[level] = cls.conn.llen(key) or 0
        return counts

    @classmethod
    def event_list(cls, key, start, end):
        results = []
        events = cls.conn.lrange(key, start, end)
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
