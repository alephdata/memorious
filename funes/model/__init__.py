from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


def create_session(config):
    """Connect to the database and create the tables."""
    if config.get('database_uri') is None:
        raise RuntimeError("No $FUNES_DATABASE_URI is set, aborting.")
    engine = create_engine(config['database_uri'])
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)
