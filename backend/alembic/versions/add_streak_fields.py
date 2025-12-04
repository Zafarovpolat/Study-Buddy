# backend/alembic/versions/add_streak_fields.py
"""Add streak fields to users

Revision ID: add_streak_001
Revises: 
Create Date: 2024-12-01
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_streak_001'
down_revision = 'ab17545490fd'  # ЗАМЕНИ на ID предыдущей миграции или оставь None если первая
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем колонки для streak
    op.add_column('users', sa.Column('current_streak', sa.Integer(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('longest_streak', sa.Integer(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('last_activity_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_activity_date')
    op.drop_column('users', 'longest_streak')
    op.drop_column('users', 'current_streak')