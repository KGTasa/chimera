"""qobuz-seed

Revision ID: 757644f94932
Revises: 0b23d7a8ea16
Create Date: 2019-10-06 17:37:32.657991

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '757644f94932'
down_revision = '0b23d7a8ea16'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('qobuz_seed_type', sa.String()))

def downgrade():
    pass
