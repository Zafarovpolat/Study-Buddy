"""Add subscription fields to users

Revision ID: add_sub_001
Revises: add_streak_001
Create Date: 2024-12-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = 'add_sub_001'
down_revision = 'add_streak_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Проверяем существующие колонки
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'subscription_expires_at' not in existing_columns:
        op.add_column('users', sa.Column('subscription_expires_at', sa.DateTime(), nullable=True))
    
    if 'telegram_payment_charge_id' not in existing_columns:
        op.add_column('users', sa.Column('telegram_payment_charge_id', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'telegram_payment_charge_id')
    op.drop_column('users', 'subscription_expires_at')
