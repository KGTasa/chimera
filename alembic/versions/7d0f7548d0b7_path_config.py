"""path config

Revision ID: 7d0f7548d0b7
Revises: ba7d45f6d2dc
Create Date: 2019-09-06 12:33:53.594428

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d0f7548d0b7'
down_revision = 'ba7d45f6d2dc'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('path_with_service', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('deezer_quality_fallback', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('tidal_quality_fallback', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('qobuz_quality_fallback', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('napster_quality_fallback', sa.Boolean()))


def downgrade():
    pass
