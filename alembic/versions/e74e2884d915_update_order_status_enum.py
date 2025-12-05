"""update_order_status_enum

Revision ID: e74e2884d915
Revises: 005
Create Date: 2025-10-05 18:02:03.144629

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e74e2884d915'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change column to text to allow updates
    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE text")

    # Update existing data to match new enum values
    op.execute("UPDATE orders SET status = 'COLLECTING_PREORDERS' WHERE status = 'PROCESSING'")
    op.execute("UPDATE orders SET status = 'SHIPPING' WHERE status = 'SHIPPED'")

    # Create new enum
    op.execute("CREATE TYPE orderstatus_new AS ENUM('PENDING', 'PAID', 'COLLECTING_PREORDERS', 'PRODUCTION', 'TRACKING_FORMATION', 'SHIPPING', 'DELIVERED', 'CANCELLED')")

    # Change column to new enum
    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE orderstatus_new USING status::orderstatus_new")

    # Drop old enum and rename new
    op.execute("DROP TYPE orderstatus")
    op.execute("ALTER TYPE orderstatus_new RENAME TO orderstatus")


def downgrade() -> None:
    # Change column to text to allow updates
    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE text")

    # Update existing data back to old enum values
    op.execute("UPDATE orders SET status = 'PROCESSING' WHERE status = 'COLLECTING_PREORDERS'")
    op.execute("UPDATE orders SET status = 'SHIPPED' WHERE status = 'SHIPPING'")

    # Create old enum
    op.execute("CREATE TYPE orderstatus_old AS ENUM('PENDING', 'PAID', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED')")

    # Change column to old enum
    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE orderstatus_old USING status::orderstatus_old")

    # Drop new enum and rename old
    op.execute("DROP TYPE orderstatus")
    op.execute("ALTER TYPE orderstatus_old RENAME TO orderstatus")
