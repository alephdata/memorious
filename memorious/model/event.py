import json
import logging

from memorious.model.common import Base, pack_now, unpack_datetime

log = logging.getLogger(__name__)


class Event(Base):
    """Document errors and warnings caused during tasks."""
    LEVEL_WARNING = 'warning'
    LEVEL_ERROR = 'error'
    LEVELS = [LEVEL_WARNING, LEVEL_ERROR]

    @classmethod
    def save(cls, crawler, stage, level, run_id, error=None, message=None):
        """Create an event, possibly based on an exception."""
        assert level in cls.LEVELS
        event = {
            'stage': stage.name,
            'level': level,
            'run_id': run_id,
            'timestamp': pack_now(),
            'error': error,
            'message': message
        }
        event_data = json.dumps(event)
        cls.conn.lpush(crawler.name + ":events", event_data)
        cls.conn.lpush(crawler.name + ":events:" + level, event_data)
        cls.conn.lpush(
            crawler.name + ":" + stage.name + ":events", event_data
        )
        cls.conn.lpush(
            crawler.name + ":" + stage.name + ":events:" + level, event_data
        )
        cls.conn.lpush(
            crawler.name + ":" + run_id + ":events", event_data
        )
        cls.conn.lpush(
            crawler.name + ":" + run_id + ":events:" + level, event_data
        )
        return event

    @classmethod
    def delete(cls, crawler):
        cls.conn.delete(crawler.name + ":events")
        for level in cls.LEVELS:
            cls.conn.delete(crawler.name + ":events:" + level)
            for stage in crawler.stages:
                key = crawler.name + ":" + stage + ":events:" + level
                cls.conn.delete(key)

    @classmethod
    def get_counts(cls, crawler):
        counts = {}
        for level in cls.LEVELS:
            key = crawler.name + ":events:" + level
            counts[level] = cls.conn.llen(key) or 0
        return counts

    @classmethod
    def get_stage_counts(cls, crawler, stage):
        counts = {}
        for level in cls.LEVELS:
            key = crawler.name + ":" + stage.name + ":events:" + level
            counts[level] = cls.conn.llen(key) or 0
        return counts

    @classmethod
    def get_run_counts(cls, crawler, run_id):
        counts = {}
        for level in cls.LEVELS:
            key = crawler.name + ":" + run_id + ":events:" + level
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
        if level:
            key = crawler.name + ":events:" + level
        else:
            key = crawler.name + ":events"
        return cls.event_list(key, start, end)

    @classmethod
    def get_stage_events(cls, crawler, stage_name, start, end, level=None):
        """events from a particular stage"""
        if level:
            key = crawler.name + ":" + stage_name + ":events:" + level
        else:
            key = crawler.name + ":" + stage_name + ":events"
        return cls.event_list(key, start, end)

    @classmethod
    def get_run_events(cls, crawler, run_id, start, end, level=None):
        """Events from a particular run"""
        if level:
            key = crawler.name + ":" + run_id + ":events:" + level
        else:
            key = crawler.name + ":" + run_id + ":events"
        return cls.event_list(key, start, end)
