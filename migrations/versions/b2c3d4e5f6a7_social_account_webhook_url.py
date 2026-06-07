"""social account webhook url (Zapier connector)

Adds social_accounts.webhook_url. When set, posts for that account are sent to
the URL (a Zapier "Catch Hook") which posts to the client's real social account
— so we can post for real without building our own platform developer apps.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-07 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('social_accounts') as batch_op:
        batch_op.add_column(sa.Column('webhook_url', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('social_accounts') as batch_op:
        batch_op.drop_column('webhook_url')
