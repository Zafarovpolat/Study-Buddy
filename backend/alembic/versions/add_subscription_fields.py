# backend/alembic/versions/add_subscription_fields.py
"""Add subscription fields to users

Revision ID: add_sub_001
Revises: add_streak_001
Create Date: 2024-12-01
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_sub_001'
down_revision = 'ab17545490fd'  # Предыдущая миграция
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('subscription_expires_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('telegram_payment_charge_id', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'telegram_payment_charge_id')
    op.drop_column('users', 'subscription_expires_at')