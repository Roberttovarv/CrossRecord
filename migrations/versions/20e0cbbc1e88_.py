"""empty message

Revision ID: 20e0cbbc1e88
Revises: 
Create Date: 2025-05-05 21:37:31.401281

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20e0cbbc1e88'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('calisthenic_record', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_private', sa.Boolean(), nullable=False))

    with op.batch_alter_table('cardio_record', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_private', sa.Boolean(), nullable=False))

    with op.batch_alter_table('weight_record', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_private', sa.Boolean(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('weight_record', schema=None) as batch_op:
        batch_op.drop_column('is_private')

    with op.batch_alter_table('cardio_record', schema=None) as batch_op:
        batch_op.drop_column('is_private')

    with op.batch_alter_table('calisthenic_record', schema=None) as batch_op:
        batch_op.drop_column('is_private')

    # ### end Alembic commands ###
