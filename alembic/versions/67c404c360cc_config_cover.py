"""config_cover

Revision ID: 67c404c360cc
Revises: 25626108a83e
Create Date: 2019-10-10 20:25:52.847697

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '67c404c360cc'
down_revision = '25626108a83e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('save_cover', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('cover_file_name', sa.String()))


def downgrade():
    pass
