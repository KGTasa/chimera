"""chimera config part1

Revision ID: 364b073603fa
Revises: 4a688bb25f07
Create Date: 2019-08-26 17:38:30.455228

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '364b073603fa'
down_revision = '4a688bb25f07'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'chimeraconfigs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('naming_scheme', sa.String(128), nullable=True),
        sa.Column('tag_title', sa.Boolean, nullable=True)
    )


def downgrade():
    pass
