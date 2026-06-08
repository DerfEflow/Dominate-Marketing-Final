"""client profile fields (Foundational Client Profile / DNA)

Adds brands.client_profile (JSON text) and brands.profile_built_at — the
structured profile of the business that all grounded content is built from.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-08 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('brands') as batch_op:
        batch_op.add_column(sa.Column('client_profile', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('profile_built_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('brands') as batch_op:
        batch_op.drop_column('profile_built_at')
        batch_op.drop_column('client_profile')
