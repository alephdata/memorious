"""Add table for CrawlerReport

Revision ID: e68033826101
Revises: c4b853c9b21a
Create Date: 2018-01-15 11:47:46.787642

"""

# revision identifiers, used by Alembic.
revision = 'e68033826101'
down_revision = 'c4b853c9b21a'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


def upgrade():
    crawler_report_table = op.create_table('crawler_report',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('crawler', sa.String(), nullable=False),
        sa.Column('op_count', sa.Integer(), nullable=True),
        sa.Column('last_run', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_crawler_report_crawler'),
        'crawler_report', ['crawler'], unique=True
    )

    connection = op.get_bind()
    results = connection.execute("""
        SELECT op.crawler AS op_crawler, count(op.id) AS op_count,
                max(op.started_at) AS last_run
        FROM operation AS op
        GROUP BY op.crawler
    """)
    records = []
    for idx, (crawler, op_count, last_run) in enumerate(results):
        records.append({
            "id": idx,
            "crawler": crawler,
            "op_count": op_count,
            "last_run": last_run
        })
    op.bulk_insert(crawler_report_table, records)


def downgrade():
    op.drop_index(
        op.f('ix_crawler_report_crawler'), table_name='crawler_report'
    )
    op.drop_table('crawler_report')
