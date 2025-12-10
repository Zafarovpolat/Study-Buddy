# backend/alembic/versions/001_initial.py - ЗАМЕНИ ПОЛНОСТЬЮ
"""Initial migration with all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === ENUMS ===
    op.execute("CREATE TYPE subscriptiontier AS ENUM ('free', 'pro', 'group')")
    op.execute("CREATE TYPE materialtype AS ENUM ('pdf', 'docx', 'txt', 'image', 'audio', 'link')")
    op.execute("CREATE TYPE processingstatus AS ENUM ('pending', 'processing', 'completed', 'failed')")
    op.execute("CREATE TYPE outputformat AS ENUM ('smart_notes', 'tldr', 'quiz', 'glossary', 'flashcards', 'podcast_script')")
    op.execute("CREATE TYPE grouprole AS ENUM ('owner', 'admin', 'member')")

    # === 1. USERS TABLE ===
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('telegram_username', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(255), nullable=True),
        
        # Subscription
        sa.Column('subscription_tier', postgresql.ENUM('free', 'pro', 'group', name='subscriptiontier', create_type=False), server_default='free'),
        sa.Column('subscription_expires_at', sa.DateTime(), nullable=True),
        sa.Column('telegram_payment_charge_id', sa.String(255), nullable=True),
        
        # Referral System
        sa.Column('referral_code', sa.String(20), nullable=True),
        sa.Column('referred_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('referral_count', sa.Integer(), server_default='0'),
        sa.Column('referral_pro_granted', sa.Boolean(), server_default='false'),
        
        # Rate limiting
        sa.Column('daily_requests_count', sa.BigInteger(), server_default='0'),
        sa.Column('last_request_date', sa.DateTime(), nullable=True),
        
        # Streak
        sa.Column('current_streak', sa.Integer(), server_default='0'),
        sa.Column('longest_streak', sa.Integer(), server_default='0'),
        sa.Column('last_activity_date', sa.Date(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)
    op.create_index('ix_users_referral_code', 'users', ['referral_code'], unique=True)
    
    # Self-referential FK for referrals
    op.create_foreign_key('fk_users_referred_by', 'users', 'users', ['referred_by_id'], ['id'])

    # === 2. FOLDERS TABLE ===
    op.create_table(
        'folders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('folders.id'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        
        # Group settings
        sa.Column('is_group', sa.Boolean(), server_default='false'),
        sa.Column('invite_code', sa.String(20), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('max_members', sa.Integer(), server_default='50'),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_folders_user_id', 'folders', ['user_id'])
    op.create_index('ix_folders_is_group', 'folders', ['is_group'])
    op.create_index('ix_folders_invite_code', 'folders', ['invite_code'], unique=True)

    # === 3. GROUP MEMBERS TABLE ===
    op.create_table(
        'group_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('folders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', postgresql.ENUM('owner', 'admin', 'member', name='grouprole', create_type=False), server_default='member'),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_group_members_group_id', 'group_members', ['group_id'])
    op.create_index('ix_group_members_user_id', 'group_members', ['user_id'])
    op.create_unique_constraint('unique_group_member', 'group_members', ['group_id', 'user_id'])

    # === 4. MATERIALS TABLE ===
    op.create_table(
        'materials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('folder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('folders.id'), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=True),
        sa.Column('file_path', sa.String(1000), nullable=True),
        sa.Column('material_type', postgresql.ENUM('pdf', 'docx', 'txt', 'image', 'audio', 'link', name='materialtype', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'processing', 'completed', 'failed', name='processingstatus', create_type=False), server_default='pending'),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_materials_user_id', 'materials', ['user_id'])
    op.create_index('ix_materials_folder_id', 'materials', ['folder_id'])

    # === 5. AI OUTPUTS TABLE ===
    op.create_table(
        'ai_outputs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('materials.id', ondelete='CASCADE'), nullable=False),
        sa.Column('format', postgresql.ENUM('smart_notes', 'tldr', 'quiz', 'glossary', 'flashcards', 'podcast_script', name='outputformat', create_type=False), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('extra_data', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_ai_outputs_material_id', 'ai_outputs', ['material_id'])

    # === 6. QUIZ RESULTS TABLE ===
    op.create_table(
        'quiz_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('materials.id', ondelete='CASCADE'), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('folders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('max_score', sa.Integer(), nullable=False),
        sa.Column('percentage', sa.Integer(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_quiz_results_user_id', 'quiz_results', ['user_id'])
    op.create_index('ix_quiz_results_material_id', 'quiz_results', ['material_id'])
    op.create_index('ix_quiz_results_group_id', 'quiz_results', ['group_id'])


def downgrade() -> None:
    op.drop_table('quiz_results')
    op.drop_table('ai_outputs')
    op.drop_table('materials')
    op.drop_table('group_members')
    op.drop_table('folders')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS outputformat')
    op.execute('DROP TYPE IF EXISTS processingstatus')
    op.execute('DROP TYPE IF EXISTS materialtype')
    op.execute('DROP TYPE IF EXISTS grouprole')
    op.execute('DROP TYPE IF EXISTS subscriptiontier')