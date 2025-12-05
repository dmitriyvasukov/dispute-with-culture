"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('cdek_point', sa.String(length=255), nullable=True),
        sa.Column('telegram', sa.String(length=255), nullable=True),
        sa.Column('vk', sa.String(length=255), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_phone'), 'users', ['phone'], unique=True)

    # Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('article', sa.String(length=100), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('sizes', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('size_table', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('care_instructions', sa.Text(), nullable=True),
        sa.Column('order_type', sa.Enum('ORDER', 'PREORDER', 'WAITING', name='ordertype'), nullable=False),
        sa.Column('stock_count', sa.Integer(), nullable=True, default=0),
        sa.Column('preorder_waves_total', sa.Integer(), nullable=True, default=0),
        sa.Column('preorder_wave_capacity', sa.Integer(), nullable=True, default=0),
        sa.Column('current_wave', sa.Integer(), nullable=True, default=1),
        sa.Column('current_wave_count', sa.Integer(), nullable=True, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_archived', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_article'), 'products', ['article'], unique=True)

    # Create product_media table
    op.create_table(
        'product_media',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('order', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create promo_codes table
    op.create_table(
        'promo_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('discount_percent', sa.Float(), nullable=False, default=0),
        sa.Column('discount_amount', sa.Float(), nullable=False, default=0),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('current_uses', sa.Integer(), nullable=True, default=0),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_promo_codes_id'), 'promo_codes', ['id'], unique=False)
    op.create_index(op.f('ix_promo_codes_code'), 'promo_codes', ['code'], unique=True)

    # Create promo_code_products table
    op.create_table(
        'promo_code_products',
        sa.Column('promo_code_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['promo_code_id'], ['promo_codes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('promo_code_id', 'product_id')
    )

    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('order_number', sa.String(length=50), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('discount_amount', sa.Float(), nullable=True, default=0),
        sa.Column('final_amount', sa.Float(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PAID', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', name='orderstatus'), nullable=False),
        sa.Column('payment_status', sa.Enum('PENDING', 'SUCCEEDED', 'CANCELLED', 'FAILED', name='paymentstatus'), nullable=False),
        sa.Column('tracking_number', sa.String(length=255), nullable=True),
        sa.Column('delivery_address', sa.Text(), nullable=True),
        sa.Column('cdek_point', sa.String(length=255), nullable=True),
        sa.Column('payment_id', sa.String(length=255), nullable=True),
        sa.Column('payment_url', sa.String(length=500), nullable=True),
        sa.Column('receipt_url', sa.String(length=500), nullable=True),
        sa.Column('promo_code_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('shipped_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['promo_code_id'], ['promo_codes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    op.create_index(op.f('ix_orders_order_number'), 'orders', ['order_number'], unique=True)

    # Create order_items table
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('size', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, default=1),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('is_preorder', sa.Boolean(), nullable=True, default=False),
        sa.Column('preorder_wave', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create pages table
    op.create_table(
        'pages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pages_id'), 'pages', ['id'], unique=False)
    op.create_index(op.f('ix_pages_slug'), 'pages', ['slug'], unique=True)

    # Create preorder_waves table
    op.create_table(
        'preorder_waves',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('wave_number', sa.Integer(), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('current_count', sa.Integer(), nullable=True, default=0),
        sa.Column('status', sa.Enum('Набор предзаказов', 'Производство изделий', 'Формирование трек-номера', 'Отправка изделий', name='preorderstatustype'), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create preorder_statuses table
    op.create_table(
        'preorder_statuses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('wave_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('COLLECTING', 'PRODUCTION', 'TRACKING', 'SHIPPING', name='preorderstatustype'), nullable=False),
        sa.Column('status_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['wave_id'], ['preorder_waves.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('preorder_statuses')
    op.drop_table('preorder_waves')
    op.drop_table('pages')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('promo_code_products')
    op.drop_table('promo_codes')
    op.drop_table('product_media')
    op.drop_table('products')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS ordertype')
    op.execute('DROP TYPE IF EXISTS orderstatus')
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    # Note: preorderstatustype enum values changed, but dropping type
    op.execute('DROP TYPE IF EXISTS preorderstatustype')
