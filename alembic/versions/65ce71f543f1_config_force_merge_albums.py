"""config force merge albums

Revision ID: 65ce71f543f1
Revises: 6c61bbf069c8
Create Date: 2019-12-01 18:09:55.562742

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '65ce71f543f1'
down_revision = '6c61bbf069c8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('force_merge_albums', sa.Boolean()))
    pass


def downgrade():
    pass
