"""tidal quality

Revision ID: 5970850f7737
Revises: 004f6a8922b1
Create Date: 2019-08-30 13:48:09.603337

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5970850f7737'
down_revision = '004f6a8922b1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('tidal_quality', sa.String()))


def downgrade():
    pass
