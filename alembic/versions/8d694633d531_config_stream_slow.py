"""config stream slow

Revision ID: 8d694633d531
Revises: 1d33c73c7027
Create Date: 2019-09-11 09:07:39.199158

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d694633d531'
down_revision = '1d33c73c7027'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('deezer_inline_decrypt', sa.Boolean()))


def downgrade():
    pass
