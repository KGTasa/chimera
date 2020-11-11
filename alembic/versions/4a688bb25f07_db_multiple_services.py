"""db multiple services

Revision ID: 4a688bb25f07
Revises: 6a48aefcfeea
Create Date: 2019-08-22 10:42:44.437183

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a688bb25f07'
down_revision = '6a48aefcfeea'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('dbtracks', sa.Column('service', sa.String()))
    pass


def downgrade():
    pass
