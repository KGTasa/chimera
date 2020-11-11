"""config_concurrency

Revision ID: 25626108a83e
Revises: 757644f94932
Create Date: 2019-10-07 19:54:25.816112

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '25626108a83e'
down_revision = '757644f94932'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('concurrency', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('workers', sa.Integer()))


def downgrade():
    pass
