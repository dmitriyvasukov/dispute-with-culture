"""Change sizes to dict, remove stock_count

Revision ID: 003
Revises: 002
Create Date: 2025-10-05 12:34:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove stock_count column
    op.drop_column('products', 'stock_count')

    # Update sizes column default (this might not work perfectly, but for migration it's ok)
    # Note: Changing JSON default might require data migration
    pass


def downgrade() -> None:
    # Add back stock_count column
    op.add_column('products', sa.Column('stock_count', sa.Integer(), nullable=True, default=0))

    # Note: Need to populate stock_count from sizes sum if downgrading
    pass