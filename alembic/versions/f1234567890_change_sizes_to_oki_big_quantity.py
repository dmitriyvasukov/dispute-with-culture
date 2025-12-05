"""change_sizes_to_oki_big_quantity

Revision ID: f1234567890
Revises: e74e2884d915
Create Date: 2025-12-02 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1234567890'
down_revision = '77e9b96c7948'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns
    op.add_column('products', sa.Column('oki_quantity', sa.Integer(), nullable=False, default=0))
    op.add_column('products', sa.Column('big_quantity', sa.Integer(), nullable=False, default=0))

    # Migrate data from sizes JSON to new columns
    op.execute("""
        UPDATE products
        SET oki_quantity = COALESCE((sizes->>'OKI')::int, 0),
            big_quantity = COALESCE((sizes->>'BIG')::int, 0)
    """)

    # Drop old sizes column
    op.drop_column('products', 'sizes')


def downgrade() -> None:
    # Add back sizes column
    op.add_column('products', sa.Column('sizes', sa.JSON(), nullable=True))

    # Migrate data back to sizes JSON
    op.execute("""
        UPDATE products
        SET sizes = json_build_object('OKI', oki_quantity, 'BIG', big_quantity)
    """)

    # Drop new columns
    op.drop_column('products', 'oki_quantity')
    op.drop_column('products', 'big_quantity')