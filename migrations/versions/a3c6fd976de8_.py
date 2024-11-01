"""empty message

Revision ID: a3c6fd976de8
Revises: b35929c536b1
Create Date: 2024-10-29 16:07:15.666768

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3c6fd976de8'
down_revision = 'b35929c536b1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('artists', schema=None) as batch_op:
        batch_op.add_column(sa.Column('availability', sa.JSON(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('artists', schema=None) as batch_op:
        batch_op.drop_column('availability')

    # ### end Alembic commands ###
