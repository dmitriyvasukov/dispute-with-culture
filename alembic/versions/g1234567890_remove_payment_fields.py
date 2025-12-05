"""remove_payment_fields

Revision ID: g1234567890
Revises: f1234567890
Create Date: 2025-12-02 12:59:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g1234567890'
down_revision = 'f1234567890'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop payment-related columns from orders table
    op.drop_column('orders', 'payment_status')
    op.drop_column('orders', 'payment_id')
    op.drop_column('orders', 'payment_url')
    op.drop_column('orders', 'receipt_url')
    op.drop_column('orders', 'paid_at')


def downgrade() -> None:
    # Add back payment-related columns
    op.add_column('orders', sa.Column('payment_status', sa.Enum('PENDING', 'SUCCEEDED', 'CANCELLED', 'FAILED', name='paymentstatus'), nullable=True))
    op.add_column('orders', sa.Column('payment_id', sa.String(length=255), nullable=True))
    op.add_column('orders', sa.Column('payment_url', sa.String(length=500), nullable=True))
    op.add_column('orders', sa.Column('receipt_url', sa.String(length=500), nullable=True))
    op.add_column('orders', sa.Column('paid_at', sa.DateTime(), nullable=True))