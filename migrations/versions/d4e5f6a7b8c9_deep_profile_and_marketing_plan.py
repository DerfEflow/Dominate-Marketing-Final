"""deep profile overrides + persistent living marketing plan

Adds:
  brands.profile_overrides         - JSON of salesperson edits, merged over the
                                     AI-built profile so re-scrapes never clobber
                                     human corrections (e.g. the true service area).
  brands.marketing_plan            - the persistent living marketing plan (JSON).
  brands.marketing_plan_updated_at - when the plan was last built/edited.

So the engine holds a comprehensive profile and a stored marketing plan per
client, instead of a shallow profile and throwaway per-cycle ideas.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('brands') as batch_op:
        batch_op.add_column(sa.Column('profile_overrides', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('marketing_plan', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('marketing_plan_updated_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('brands') as batch_op:
        batch_op.drop_column('marketing_plan_updated_at')
        batch_op.drop_column('marketing_plan')
        batch_op.drop_column('profile_overrides')
