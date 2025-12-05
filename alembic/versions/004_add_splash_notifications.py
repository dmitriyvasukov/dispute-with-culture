"""Add splash_notifications table

Revision ID: 004
Revises: 003
Create Date: 2025-10-05 14:27:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create splash_notifications table
    op.create_table(
        'splash_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('text', sa.String(length=120), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_splash_notifications_id'), 'splash_notifications', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('splash_notifications')