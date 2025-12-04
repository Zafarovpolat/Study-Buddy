"""Add streak fields to users

Revision ID: add_streak_001
Revises: ab17545490fd
Create Date: 2024-12-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = 'add_streak_001'
down_revision = 'ab17545490fd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Проверяем существующие колонки
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'current_streak' not in existing_columns:
        op.add_column('users', sa.Column('current_streak', sa.Integer(), server_default='0', nullable=True))
    
    if 'longest_streak' not in existing_columns:
        op.add_column('users', sa.Column('longest_streak', sa.Integer(), server_default='0', nullable=True))
    
    if 'last_activity_date' not in existing_columns:
        op.add_column('users', sa.Column('last_activity_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_activity_date')
    op.drop_column('users', 'longest_streak')
    op.drop_column('users', 'current_streak')
