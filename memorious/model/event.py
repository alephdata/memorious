import json
import logging
from datetime import datetime

from memorious.model.common import Base

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
        event_data = json.dumps({
            'stage': stage.name,
            'level': level,
            'run_id': run_id,
            'timestamp': str(datetime.utcnow()),
            'error': error,
            'message': message
        })
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

    @classmethod
    def delete(cls, crawler):
        cls.conn.delete(crawler.name + ":events")
        for level in cls.LEVELS:
            cls.conn.delete(crawler.name + ":events:" + level)
            for stage in crawler.stages:
                cls.conn.delete(
                    crawler.name + ":" + stage + ":events:" + level
                )

    @classmethod
    def get_counts(cls, crawler):
        counts = {}
        for level in cls.LEVELS:
            counts[level] = cls.conn.llen(
                crawler.name + ":events:" + level
            ) or 0
        return counts

    @classmethod
    def get_stage_counts(cls, crawler, stage):
        counts = {}
        for level in cls.LEVELS:
            counts[level] = cls.conn.llen(
                crawler.name + ":" + stage.name + ":events:" + level
            ) or 0
        return counts

    @classmethod
    def get_run_counts(cls, crawler, run_id):
        counts = {}
        for level in cls.LEVELS:
            counts[level] = cls.conn.llen(
                crawler.name + ":" + run_id + ":events:" + level
            ) or 0
        return counts

    @classmethod
    def event_list(cls, events):
        results = []
        if events is None:
            return results
        for event in events:
            result = json.loads(event)
            result["timestamp"] = cls.unpack_datetime(result['timestamp'])
            results.append(result)
        return results

    @classmethod
    def get_crawler_events(cls, crawler, start, end, level=None):
        if level:
            events = cls.conn.lrange(
                crawler.name + ":events:" + level, start, end
            )
        else:
            events = cls.conn.lrange(
                crawler.name + ":events", start, end
            )
        return cls.event_list(events)

    @classmethod
    def get_stage_events(cls, crawler, stage_name, start, end, level=None):
        """events from a particular stage"""
        if level:
            events = cls.conn.lrange(
                crawler.name + ":" + stage_name + ":events:" + level,
                start, end
            )
        else:
            events = cls.conn.lrange(
                crawler.name + ":" + stage_name + ":events", start, end
            )
        return cls.event_list(events)

    @classmethod
    def get_run_events(cls, crawler, run_id, start, end, level=None):
        """Events from a particular run"""
        if level:
            events = cls.conn.lrange(
                crawler.name + ":" + run_id + ":events:" + level, start, end
            )
        else:
            events = cls.conn.lrange(
                crawler.name + ":" + run_id + ":events", start, end
            )
        return cls.event_list(events)
