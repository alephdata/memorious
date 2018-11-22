import logging

from memorious.model.common import Base
from memorious.model.common import dump_json, load_json
from memorious.util import make_key

log = logging.getLogger(__name__)


class Cache(Base):
    """Cache crawled objects till cleanup."""

    @classmethod
    def cache_entity(cls, crawler, entity):
        cls.conn.lpush(
            make_key(crawler, "cache", "entities"), dump_json(entity)
        )

    @classmethod
    def export_entities(cls, crawler):
        entities = cls.conn.lrange(
            make_key(crawler, "cache", "entities"), 0, -1
        )
        entities = map(load_json, entities)
        return list(entities)

    @classmethod
    def flush(cls, crawler):
        cls.conn.delete(make_key(crawler, "cache", "entities"))
