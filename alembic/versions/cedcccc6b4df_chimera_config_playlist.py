"""chimera_config_playlist


Revision ID: cedcccc6b4df
Revises: 83462bad0105
Create Date: 2019-09-22 13:02:47.544030

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cedcccc6b4df'
down_revision = '83462bad0105'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('save_as_compilation', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('discography_filter', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('playlist_naming_scheme', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('playlist_folder_naming_scheme', sa.String()))

def downgrade():
    pass
