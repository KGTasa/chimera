"""napster

Revision ID: ff8310c75418
Revises: 5d08eab89a47
Create Date: 2019-09-01 07:58:28.844422

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ff8310c75418'
down_revision = '5d08eab89a47'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('chimeraconfigs', sa.Column('napster_email', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('napster_password', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('napster_quality', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('napster_cover_size', sa.String()))

def downgrade():
    pass
