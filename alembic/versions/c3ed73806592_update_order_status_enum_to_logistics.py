"""update_order_status_enum_to_logistics

Revision ID: c3ed73806592
Revises: 0d120e555ecc
Create Date: 2025-12-02 16:43:16.351495

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3ed73806592'
down_revision = '0d120e555ecc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change column to text to allow updates
    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE text")

    # Update existing data to match new enum values
    op.execute("UPDATE orders SET status = 'paid' WHERE status = 'PAID'")
    op.execute("UPDATE orders SET status = 'shipped' WHERE status = 'SHIPPING'")
    op.execute("UPDATE orders SET status = 'delivered' WHERE status = 'DELIVERED'")
    op.execute("UPDATE orders SET status = 'cancelled' WHERE status = 'CANCELLED'")
    # PENDING -> created
    op.execute("UPDATE orders SET status = 'created' WHERE status = 'PENDING'")
    # Other statuses like COLLECTING_PREORDERS, PRODUCTION, TRACKING_FORMATION can be set to paid or shipped depending on logic, but for simplicity, set to paid
    op.execute("UPDATE orders SET status = 'paid' WHERE status IN ('COLLECTING_PREORDERS', 'PRODUCTION', 'TRACKING_FORMATION')")

    # Create new enum
    op.execute("CREATE TYPE orderstatus_new AS ENUM('created', 'paid', 'shipped', 'delivered', 'cancelled')")

    # Change column to new enum
    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE orderstatus_new USING status::orderstatus_new")

    # Drop old enum and rename new
    op.execute("DROP TYPE orderstatus")
    op.execute("ALTER TYPE orderstatus_new RENAME TO orderstatus")


def downgrade() -> None:
    # Change column to text to allow updates
    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE text")

    # Update existing data back to old enum values
    op.execute("UPDATE orders SET status = 'PAID' WHERE status = 'paid'")
    op.execute("UPDATE orders SET status = 'SHIPPING' WHERE status = 'shipped'")
    op.execute("UPDATE orders SET status = 'DELIVERED' WHERE status = 'delivered'")
    op.execute("UPDATE orders SET status = 'CANCELLED' WHERE status = 'cancelled'")
    op.execute("UPDATE orders SET status = 'PENDING' WHERE status = 'created'")

    # Create old enum
    op.execute("CREATE TYPE orderstatus_old AS ENUM('PENDING', 'PAID', 'COLLECTING_PREORDERS', 'PRODUCTION', 'TRACKING_FORMATION', 'SHIPPING', 'DELIVERED', 'CANCELLED')")

    # Change column to old enum
    op.execute("ALTER TABLE orders ALTER COLUMN status TYPE orderstatus_old USING status::orderstatus_old")

    # Drop new enum and rename old
    op.execute("DROP TYPE orderstatus")
    op.execute("ALTER TYPE orderstatus_old RENAME TO orderstatus")
