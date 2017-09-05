from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from funes import settings

Base = declarative_base()


def create_session():
    """Connect to the database and create the tables."""
    engine = create_engine(settings.DATABASE_URI)
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)
