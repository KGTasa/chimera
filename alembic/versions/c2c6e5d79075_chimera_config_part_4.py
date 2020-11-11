"""chimera_config_part_4

Revision ID: c2c6e5d79075
Revises: 7a9e937e36aa
Create Date: 2019-08-28 13:00:59.924579

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2c6e5d79075'
down_revision = '7a9e937e36aa'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('first_run', sa.Boolean()))


def downgrade():
    pass
