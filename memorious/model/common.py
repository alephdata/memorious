import json

from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class TextJSON(TypeDecorator):
    """Stores and retrieves JSON as TEXT."""
    impl = TEXT

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        return json.loads(value)


JSON = TextJSON().with_variant(JSONB, 'postgresql')
