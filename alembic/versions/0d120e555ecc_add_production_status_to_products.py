"""add_production_status_to_products

Revision ID: 0d120e555ecc
Revises: g1234567890
Create Date: 2025-12-02 16:42:46.070277

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0d120e555ecc'
down_revision = 'g1234567890'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for production status
    op.execute("""
        CREATE TYPE productionstatus AS ENUM (
            'COLLECTING_PREORDERS',
            'PRODUCTION',
            'TRACKING_FORMATION',
            'SHIPPING'
        )
    """)

    # Add production_status column to products table
    op.add_column('products', sa.Column('production_status', sa.Enum('COLLECTING_PREORDERS', 'PRODUCTION', 'TRACKING_FORMATION', 'SHIPPING', name='productionstatus'), nullable=True))


def downgrade() -> None:
    # Drop production_status column
    op.drop_column('products', 'production_status')

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS productionstatus")
