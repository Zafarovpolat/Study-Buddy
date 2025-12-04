"""Bridge migration - compatibility layer

Revision ID: add_sub_001
Revises: add_missing_cols
Create Date: 2025-12-05

This is a bridge migration to maintain database compatibility.
The database was at this revision, so we need to keep this ID.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_sub_001'
down_revision: Union[str, None] = 'add_missing_cols'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ничего не делаем - это миграция-мост для совместимости
    pass


def downgrade() -> None:
    pass
