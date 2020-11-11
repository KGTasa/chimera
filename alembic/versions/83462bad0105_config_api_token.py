"""config api token

Revision ID: 83462bad0105
Revises: 8d694633d531
Create Date: 2019-09-14 08:10:58.285402

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83462bad0105'
down_revision = '8d694633d531'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('api_token', sa.String()))


def downgrade():
    pass
