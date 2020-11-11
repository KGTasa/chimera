"""napster api token

Revision ID: 997da59d27ef
Revises: ff8310c75418
Create Date: 2019-09-01 11:06:38.380729

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '997da59d27ef'
down_revision = 'ff8310c75418'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('napster_api_token', sa.String()))


def downgrade():
    pass
