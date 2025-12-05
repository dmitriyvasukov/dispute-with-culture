"""Update preorder status enum values

Revision ID: 005
Revises: 004
Create Date: 2025-10-05 14:48:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update enum values for preorderstatustype
    # This requires recreating the enum with new values
    op.execute("ALTER TYPE preorderstatustype RENAME TO preorderstatustype_old")
    op.execute("CREATE TYPE preorderstatustype AS ENUM('Набор предзаказов', 'Производство изделий', 'Формирование трек-номера', 'Отправка изделий')")

    # Update columns to use new enum
    op.execute("ALTER TABLE preorder_waves ALTER COLUMN status TYPE preorderstatustype USING status::text::preorderstatustype")
    op.execute("ALTER TABLE preorder_statuses ALTER COLUMN status TYPE preorderstatustype USING status::text::preorderstatustype")

    # Drop old enum
    op.execute("DROP TYPE preorderstatustype_old")


def downgrade() -> None:
    # Revert enum values
    op.execute("ALTER TYPE preorderstatustype RENAME TO preorderstatustype_old")
    op.execute("CREATE TYPE preorderstatustype AS ENUM('COLLECTING', 'PRODUCTION', 'TRACKING', 'SHIPPING')")

    # Update columns back
    op.execute("ALTER TABLE preorder_waves ALTER COLUMN status TYPE preorderstatustype USING status::text::preorderstatustype")
    op.execute("ALTER TABLE preorder_statuses ALTER COLUMN status TYPE preorderstatustype USING status::text::preorderstatustype")

    # Drop old enum
    op.execute("DROP TYPE preorderstatustype_old")