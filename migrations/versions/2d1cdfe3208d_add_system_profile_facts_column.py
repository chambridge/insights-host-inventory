"""empty message

Revision ID: 2d1cdfe3208d
Revises: 2d951983fa89
Create Date: 2019-03-22 10:52:29.024809

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2d1cdfe3208d"
down_revision = "2d951983fa89"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("hosts", sa.Column("system_profile_facts", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("hosts", "system_profile_facts")
    # ### end Alembic commands ###
