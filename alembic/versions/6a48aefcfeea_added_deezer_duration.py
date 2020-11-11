"""added deezer_duration

Revision ID: 6a48aefcfeea
Revises: 05982afdef6d
Create Date: 2019-07-09 08:40:27.654798

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a48aefcfeea'
down_revision = '05982afdef6d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('dbtracks', sa.Column('deezer_duration', sa.Integer()))


def downgrade():
    pass
