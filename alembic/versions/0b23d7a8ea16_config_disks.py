"""config_disks

Revision ID: 0b23d7a8ea16
Revises: cedcccc6b4df
Create Date: 2019-09-29 19:21:55.482295

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b23d7a8ea16'
down_revision = 'cedcccc6b4df'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('merge_disks', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('pad_track', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('pad_track_width', sa.String()))


def downgrade():
    pass
