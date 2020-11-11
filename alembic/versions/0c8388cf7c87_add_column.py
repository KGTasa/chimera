"""add column

Revision ID: 0c8388cf7c87
Revises: 
Create Date: 2019-05-29 17:22:38.891411

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c8388cf7c87'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('dbtracks', sa.Column('name', sa.String()))
    pass


def downgrade():
    pass
