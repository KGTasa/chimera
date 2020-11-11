"""spotify scope


Revision ID: d475ea347726
Revises: c2c6e5d79075
Create Date: 2019-08-28 19:41:39.722596

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd475ea347726'
down_revision = 'c2c6e5d79075'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('spotify_scope', sa.Text()))

def downgrade():
    pass
