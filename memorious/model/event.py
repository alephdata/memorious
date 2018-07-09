import json
import logging

from memorious.model.common import Base, pack_now, unpack_datetime
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
        data = json.dumps(event)
        cls.conn.lpush(make_key(crawler, "events"), data)
        cls.conn.lpush(make_key(crawler, "events", level), data)
        cls.conn.lpush(make_key(crawler, stage, "events"), data)
        cls.conn.lpush(make_key(crawler, stage.name, "events", level), data)
        cls.conn.lpush(make_key(crawler, run_id, "events"), data)
        cls.conn.lpush(make_key(crawler, run_id, "events", level), data)
        return event

    @classmethod
    def delete(cls, crawler):
        cls.conn.delete(make_key(crawler, "events"))
        for level in cls.LEVELS:
            cls.conn.delete(make_key(crawler, "events", level))
            for stage in crawler.stages:
                cls.conn.delete(make_key(crawler, stage, "events", level))

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
            key = make_key(crawler, stage, "events", level)
            counts[level] = cls.conn.llen(key) or 0
        return counts

    @classmethod
    def get_run_counts(cls, crawler, run_id):
        counts = {}
        for level in cls.LEVELS:
            key = make_key(crawler, run_id, "events", level)
            counts[level] = cls.conn.llen(key) or 0
        return counts

    @classmethod
    def event_list(cls, key, start, end):
        results = []
        events = cls.conn.lrange(key, start, end)
        if events is None:
            return results
        for event in events:
            result = json.loads(event)
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
        key = make_key(crawler, stage_name, "events", level)
        return cls.event_list(key, start, end)

    @classmethod
    def get_run_events(cls, crawler, run_id, start, end, level=None):
        """Events from a particular run"""
        key = make_key(crawler, run_id, "events", level)
        return cls.event_list(key, start, end)
