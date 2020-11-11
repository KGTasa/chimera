"""Chimera Config Part 2

Revision ID: 87d168a8b2b5
Revises: 364b073603fa
Create Date: 2019-08-26 19:59:52.607418

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '87d168a8b2b5'
down_revision = '364b073603fa'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('tag_artist', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('tag_date', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('tag_year', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('tag_cover', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('tag_album', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('tag_tracknumber', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('tag_discnumber', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('tag_genre', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('tag_albumartist', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('tag_bpm', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('tag_length', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('tag_organization', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('tag_isrc', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('tag_gain', sa.Boolean()))


def downgrade():
    pass
