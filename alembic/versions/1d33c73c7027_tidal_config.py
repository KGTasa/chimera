"""tidal_config

Revision ID: 1d33c73c7027
Revises: 7d0f7548d0b7
Create Date: 2019-09-10 18:59:50.896013

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1d33c73c7027'
down_revision = '7d0f7548d0b7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('tidal_video_path', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('tidal_video_pp', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('auto_login', sa.String()))

def downgrade():
    pass
