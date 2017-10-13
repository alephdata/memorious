"""Add 'crawler' field to events.

Revision ID: c4b853c9b21a
Revises: fa4b74d9c734
Create Date: 2017-10-13 10:56:50.365325

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c4b853c9b21a'
down_revision = 'fa4b74d9c734'


def upgrade():
    op.add_column('event', sa.Column('crawler', sa.String(), nullable=True))
    op.create_index(op.f('ix_event_crawler'), 'event', ['crawler'],
                    unique=False)


def downgrade():
    pass
