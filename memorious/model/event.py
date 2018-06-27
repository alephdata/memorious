import logging
from datetime import datetime
import json

import attr

from memorious.model.common import Base

log = logging.getLogger(__name__)


@attr.s
class Event(Base):
    """Document errors and warnings caused during tasks."""
    LEVEL_WARNING = 'warning'
    LEVEL_ERROR = 'error'
    LEVELS = [LEVEL_WARNING, LEVEL_ERROR]

    level = attr.ib(default=None)
    crawler = attr.ib(default=None)
    stage = attr.ib(default=None)
    run_id = attr.ib(default=None)
    error_type = attr.ib(default=None)
    error_message = attr.ib(default=None)
    error_details = attr.ib(default=None)
    timestamp = attr.ib(default=attr.Factory(datetime.now))

    @classmethod
    def deserialize(cls, event_json):
        event_data = json.loads(event_json)
        event_data["timestamp"] = datetime.strptime(
            event_data["timestamp"], "%Y-%m-%d %H:%M:%S.%f"
        )
        return event_data

    @classmethod
    def save(cls, crawler, stage, level, run_id, error_type=None,
             error_message=None, error_details=None):
        """Create an event, possibly based on an exception."""
        event = cls()
        event.crawler = crawler.name
        event.stage = stage.name
        assert level in cls.LEVELS
        event.level = level
        event.run_id = run_id
        event.error_type = error_type
        event.error_message = error_message
        event.error_details = error_details
        event_data = attr.asdict(event)
        event_data['timestamp'] = str(event_data['timestamp'])
        event_data = json.dumps(event_data)
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
                cls.conn.delete(
                    crawler.name + ":" + stage.name + ":events:" + level
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
    def get_crawler_events(cls, crawler, start, end, level=None):
        if level:
            events = cls.conn.lrange(
                crawler.name + ":events:" + level, start, end
            )
        else:
            events = cls.conn.lrange(
                crawler.name + ":events", start, end
            )
        if not events:
            events = []
        return [cls.deserialize(event) for event in events]

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
        if not events:
            events = []
        return [cls.deserialize(event) for event in events]

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
        if not events:
            events = []
        return [cls.deserialize(event) for event in events]

    def __repr__(self):
        return '<Event(%s,%s,%s,%s)>' % \
            (self.crawler, self.stage, self.error_type, self.level)
