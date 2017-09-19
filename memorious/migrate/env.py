from __future__ import with_statement
from alembic import context

from memorious.core import session
from memorious.model import Base

config = context.config
config.set_main_option('script_location', '.')
target_metadata = Base.metadata
target_metadata.bind = session.bind


def ignore_autogen(obj, name, type_, reflexted, compare_to):
    if type_ == 'table' and name.startswith('tabular_'):
        return False
    return True


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url,
                      include_object=ignore_autogen)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connection = session.bind.connect()
    context.configure(connection=connection,
                      target_metadata=target_metadata,
                      include_object=ignore_autogen)

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
