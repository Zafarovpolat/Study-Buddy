"""Initial tables with all fields

Revision ID: ab17545490fd
Revises: 
Create Date: 2025-11-30 20:04:33.456472

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab17545490fd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create subscription tier enum
    subscription_tier_enum = sa.Enum('FREE', 'PRO', 'GROUP', name='subscriptiontier')
    subscription_tier_enum.create(op.get_bind(), checkfirst=True)
    
    # Create material type enum
    material_type_enum = sa.Enum('PDF', 'DOCX', 'TXT', 'IMAGE', 'AUDIO', 'LINK', name='materialtype')
    material_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create processing status enum
    processing_status_enum = sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='processingstatus')
    processing_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create output format enum
    output_format_enum = sa.Enum('SMART_NOTES', 'TLDR', 'QUIZ', 'GLOSSARY', 'FLASHCARDS', 'PODCAST_SCRIPT', name='outputformat')
    output_format_enum.create(op.get_bind(), checkfirst=True)

    # Users table with ALL fields
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('telegram_username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('subscription_tier', sa.Enum('FREE', 'PRO', 'GROUP', name='subscriptiontier'), nullable=True),
        sa.Column('subscription_expires_at', sa.DateTime(), nullable=True),
        sa.Column('telegram_payment_charge_id', sa.String(length=255), nullable=True),
        sa.Column('daily_requests_count', sa.BigInteger(), nullable=True),
        sa.Column('last_request_date', sa.DateTime(), nullable=True),
        sa.Column('current_streak', sa.Integer(), server_default='0', nullable=True),
        sa.Column('longest_streak', sa.Integer(), server_default='0', nullable=True),
        sa.Column('last_activity_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)
    
    # Folders table
    op.create_table('folders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('is_group_folder', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['folders.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Materials table
    op.create_table('materials',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('folder_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('original_filename', sa.String(length=500), nullable=True),
        sa.Column('file_path', sa.String(length=1000), nullable=True),
        sa.Column('material_type', sa.Enum('PDF', 'DOCX', 'TXT', 'IMAGE', 'AUDIO', 'LINK', name='materialtype'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='processingstatus'), nullable=True),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # AI Outputs table
    op.create_table('ai_outputs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('material_id', sa.UUID(), nullable=False),
        sa.Column('format', sa.Enum('SMART_NOTES', 'TLDR', 'QUIZ', 'GLOSSARY', 'FLASHCARDS', 'PODCAST_SCRIPT', name='outputformat'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('ai_outputs')
    op.drop_table('materials')
    op.drop_table('folders')
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_table('users')
