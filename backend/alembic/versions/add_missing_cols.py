"""Add missing columns to users

Revision ID: add_missing_cols
Revises: ab17545490fd
Create Date: 2025-12-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_missing_cols'
down_revision: Union[str, None] = 'ab17545490fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем колонки, которых может не хватать
    # Используем try/except чтобы игнорировать если колонка уже есть
    
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'current_streak' not in existing_columns:
        op.add_column('users', sa.Column('current_streak', sa.Integer(), server_default='0', nullable=True))
    
    if 'longest_streak' not in existing_columns:
        op.add_column('users', sa.Column('longest_streak', sa.Integer(), server_default='0', nullable=True))
    
    if 'last_activity_date' not in existing_columns:
        op.add_column('users', sa.Column('last_activity_date', sa.Date(), nullable=True))
    
    if 'subscription_expires_at' not in existing_columns:
        op.add_column('users', sa.Column('subscription_expires_at', sa.DateTime(), nullable=True))
    
    if 'telegram_payment_charge_id' not in existing_columns:
        op.add_column('users', sa.Column('telegram_payment_charge_id', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'telegram_payment_charge_id')
    op.drop_column('users', 'subscription_expires_at')
    op.drop_column('users', 'last_activity_date')
    op.drop_column('users', 'longest_streak')
    op.drop_column('users', 'current_streak')
