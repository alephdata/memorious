"""Store stage name and run_id on event


Revision ID: 5903b3db4c04
Revises: be90d88eaabf
Create Date: 2018-02-08 13:45:15.270791

"""

# revision identifiers, used by Alembic.
revision = '5903b3db4c04'
down_revision = 'be90d88eaabf'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('event', sa.Column('run_id', sa.String(), nullable=True))
    op.add_column('event', sa.Column('stage', sa.String(), nullable=True))
    op.create_index(op.f('ix_event_run_id'), 'event', ['run_id'], unique=False)
    op.create_index(op.f('ix_event_stage'), 'event', ['stage'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_event_stage'), table_name='event')
    op.drop_index(op.f('ix_event_run_id'), table_name='event')
    op.drop_column('event', 'stage')
    op.drop_column('event', 'run_id')
