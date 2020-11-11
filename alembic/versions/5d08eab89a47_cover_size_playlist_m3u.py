"""cover size, playlist m3u

Revision ID: 5d08eab89a47
Revises: 5970850f7737
Create Date: 2019-08-31 21:00:15.287716

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5d08eab89a47'
down_revision = '5970850f7737'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('m3u', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('deezer_cover_size', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('tidal_cover_size', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('qobuz_cover_size', sa.String()))


def downgrade():
    pass
