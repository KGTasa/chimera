"""config_folder_scheme

Revision ID: 6c61bbf069c8
Revises: 67c404c360cc
Create Date: 2019-10-21 21:54:59.066527

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c61bbf069c8'
down_revision = '67c404c360cc'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('folder_naming_scheme', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('tag_comment', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('tag_comment_value', sa.String()))


def downgrade():
    pass
