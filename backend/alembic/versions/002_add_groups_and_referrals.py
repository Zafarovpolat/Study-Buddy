# backend/alembic/versions/002_add_groups_and_referrals.py - СОЗДАЙ НОВЫЙ ФАЙЛ
"""Add groups and referrals

Revision ID: 002_groups_referrals
Revises: 001_initial  # Замени на ID твоей последней миграции
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_groups_referrals'
down_revision = None  # Замени на ID предыдущей миграции или None если первая
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Добавляем поля в users для реферальной системы
    op.add_column('users', sa.Column('referral_code', sa.String(20), unique=True, nullable=True))
    op.add_column('users', sa.Column('referred_by_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('users', sa.Column('referral_count', sa.Integer(), server_default='0'))
    op.add_column('users', sa.Column('referral_pro_granted', sa.Boolean(), server_default='false'))
    
    # Индекс для referral_code
    op.create_index('ix_users_referral_code', 'users', ['referral_code'])
    
    # FK для referred_by
    op.create_foreign_key(
        'fk_users_referred_by',
        'users', 'users',
        ['referred_by_id'], ['id']
    )
    
    # 2. Добавляем поля в folders для групп
    op.add_column('folders', sa.Column('is_group', sa.Boolean(), server_default='false'))
    op.add_column('folders', sa.Column('invite_code', sa.String(20), unique=True, nullable=True))
    op.add_column('folders', sa.Column('description', sa.String(500), nullable=True))
    op.add_column('folders', sa.Column('max_members', sa.Integer(), server_default='50'))
    op.add_column('folders', sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()))
    
    # Индексы
    op.create_index('ix_folders_is_group', 'folders', ['is_group'])
    op.create_index('ix_folders_invite_code', 'folders', ['invite_code'])
    
    # Удаляем старое поле если есть
    try:
        op.drop_column('folders', 'is_group_folder')
    except:
        pass
    
    # 3. Создаём таблицу group_members
    op.create_table(
        'group_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('folders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.Enum('owner', 'admin', 'member', name='grouprole'), default='member'),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('group_id', 'user_id', name='unique_group_member')
    )
    
    op.create_index('ix_group_members_group_id', 'group_members', ['group_id'])
    op.create_index('ix_group_members_user_id', 'group_members', ['user_id'])


def downgrade() -> None:
    # Удаляем таблицу group_members
    op.drop_table('group_members')
    
    # Удаляем поля из folders
    op.drop_index('ix_folders_invite_code')
    op.drop_index('ix_folders_is_group')
    op.drop_column('folders', 'updated_at')
    op.drop_column('folders', 'max_members')
    op.drop_column('folders', 'description')
    op.drop_column('folders', 'invite_code')
    op.drop_column('folders', 'is_group')
    
    # Удаляем поля из users
    op.drop_constraint('fk_users_referred_by', 'users', type_='foreignkey')
    op.drop_index('ix_users_referral_code')
    op.drop_column('users', 'referral_pro_granted')
    op.drop_column('users', 'referral_count')
    op.drop_column('users', 'referred_by_id')
    op.drop_column('users', 'referral_code')
    
    # Удаляем enum
    op.execute('DROP TYPE IF EXISTS grouprole')