"""columns

Revision ID: 05982afdef6d
Revises: 0c8388cf7c87
Create Date: 2019-05-29 21:34:26.295254

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '05982afdef6d'
down_revision = '0c8388cf7c87'
branch_labels = None
depends_on = None


def upgrade():
    ##track_name;artist;album;release_date;duration_ms;isrc
    op.add_column('dbtracks', sa.Column('artist', sa.String()))
    op.add_column('dbtracks', sa.Column('album', sa.String()))
    op.add_column('dbtracks', sa.Column('release_date', sa.String()))
    op.add_column('dbtracks', sa.Column('isrc', sa.String()))
    op.add_column('dbtracks', sa.Column('spotify_id', sa.String()))
    op.add_column('dbtracks', sa.Column('deezer_id', sa.String()))
    op.add_column('dbtracks', sa.Column('path', sa.String()))
    pass


def downgrade():
    pass
