"""add_postal_code_to_orders

Revision ID: ce708ce88c85
Revises: c3ed73806592
Create Date: 2025-12-02 17:36:45.250248

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce708ce88c85'
down_revision = 'c3ed73806592'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add postal_code column to orders table
    op.add_column('orders', sa.Column('postal_code', sa.String(length=10), nullable=True))


def downgrade() -> None:
    # Remove postal_code column from orders table
    op.drop_column('orders', 'postal_code')
