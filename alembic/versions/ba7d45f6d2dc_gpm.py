"""gpm

Revision ID: ba7d45f6d2dc
Revises: 997da59d27ef
Create Date: 2019-09-04 15:10:56.477559

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba7d45f6d2dc'
down_revision = '997da59d27ef'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('gpm_enabled', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('gpm_email', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('gpm_password', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('gpm_quality', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('gpm_device_id', sa.String()))


def downgrade():
    pass
