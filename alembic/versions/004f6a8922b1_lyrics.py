"""lyrics

Revision ID: 004f6a8922b1
Revises: d475ea347726
Create Date: 2019-08-30 11:02:31.735856

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004f6a8922b1'
down_revision = 'd475ea347726'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('tag_lyrics', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('save_lyrics', sa.Boolean()))


def downgrade():
    pass
