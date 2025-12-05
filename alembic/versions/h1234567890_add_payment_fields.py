"""add_payment_fields

Revision ID: h1234567890
Revises: g1234567890
Create Date: 2025-12-05 11:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h1234567890'
down_revision = 'g1234567890'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add back payment-related columns
    op.add_column('orders', sa.Column('payment_status', sa.Enum('PENDING', 'SUCCEEDED', 'CANCELLED', 'FAILED', name='paymentstatus'), nullable=True))
    op.add_column('orders', sa.Column('payment_id', sa.String(length=255), nullable=True))
    op.add_column('orders', sa.Column('payment_url', sa.String(length=500), nullable=True))
    op.add_column('orders', sa.Column('receipt_url', sa.String(length=500), nullable=True))
    op.add_column('orders', sa.Column('paid_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Drop payment-related columns from orders table
    op.drop_column('orders', 'payment_status')
    op.drop_column('orders', 'payment_id')
    op.drop_column('orders', 'payment_url')
    op.drop_column('orders', 'receipt_url')
    op.drop_column('orders', 'paid_at')