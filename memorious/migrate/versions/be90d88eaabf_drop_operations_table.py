"""Drop operations table

Revision ID: be90d88eaabf
Revises: c4b853c9b21a
Create Date: 2018-02-08 11:33:54.218434

"""

# revision identifiers, used by Alembic.
revision = 'be90d88eaabf'
down_revision = 'c4b853c9b21a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('event') as batch_op:
        batch_op.drop_column('operation_id')
    with op.batch_alter_table('result') as batch_op:
        batch_op.drop_column('operation_id')
    op.drop_table('operation')


def downgrade():
    pass
