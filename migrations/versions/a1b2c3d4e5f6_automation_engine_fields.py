"""automation engine fields

Adds the columns the per-client automation engine needs:

  - brands.automation_enabled       : per-client autopilot on/off
  - brands.posting_frequency_days   : how often to refresh + post
  - brands.last_research_at         : freshness of the client's source data
  - brands.research_snapshot        : latest research result (JSON text)
  - social_accounts.is_simulated    : demo/simulated connection (no real OAuth)

Purely additive. NOT NULL boolean/int columns carry a server_default so the
migration is safe against existing rows; the server_default is then dropped so
the application layer owns the default (matches the pivot migration's pattern).

Revision ID: a1b2c3d4e5f6
Revises: f06038cdd1a2
Create Date: 2026-06-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = 'f06038cdd1a2'
branch_labels = None
depends_on = None


def upgrade():
    # --- brands: automation fields ---------------------------------------
    with op.batch_alter_table('brands') as batch_op:
        batch_op.add_column(sa.Column('automation_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('posting_frequency_days', sa.Integer(), nullable=False, server_default='3'))
        batch_op.add_column(sa.Column('last_research_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('research_snapshot', sa.Text(), nullable=True))

    # --- social_accounts: simulated flag ---------------------------------
    with op.batch_alter_table('social_accounts') as batch_op:
        batch_op.add_column(sa.Column('is_simulated', sa.Boolean(), nullable=False, server_default=sa.false()))

    # Drop server_defaults now that existing rows are backfilled — the app
    # layer owns these defaults going forward.
    with op.batch_alter_table('brands') as batch_op:
        batch_op.alter_column('automation_enabled', server_default=None)
        batch_op.alter_column('posting_frequency_days', server_default=None)
    with op.batch_alter_table('social_accounts') as batch_op:
        batch_op.alter_column('is_simulated', server_default=None)


def downgrade():
    with op.batch_alter_table('social_accounts') as batch_op:
        batch_op.drop_column('is_simulated')
    with op.batch_alter_table('brands') as batch_op:
        batch_op.drop_column('research_snapshot')
        batch_op.drop_column('last_research_at')
        batch_op.drop_column('posting_frequency_days')
        batch_op.drop_column('automation_enabled')
