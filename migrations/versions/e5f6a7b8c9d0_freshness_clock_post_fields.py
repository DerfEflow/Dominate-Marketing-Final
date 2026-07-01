"""freshness clock: just-in-time post fields

Adds:
  social_posts.brief       - the strategist brief (JSON) a 'planned' post is
                             written from just-in-time, near its publish slot.
  social_posts.grounded_at - timestamp of the research data the final content
                             was built from (the "built from data dated X" stamp).

Enforces BLUEPRINT layer 5 (the Freshness Clock): posts scheduled days ahead are
no longer written days ahead — they are written from FRESH signals shortly
before they publish.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('social_posts') as batch_op:
        batch_op.add_column(sa.Column('brief', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('grounded_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('social_posts') as batch_op:
        batch_op.drop_column('grounded_at')
        batch_op.drop_column('brief')
