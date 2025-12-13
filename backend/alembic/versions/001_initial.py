# backend/alembic/versions/001_initial.py
"""Initial migration - all tables with VARCHAR (no ENUM)

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === 1. USERS TABLE ===
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('telegram_username', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(255), nullable=True),
        sa.Column('last_name', sa.String(255), nullable=True),
        
        # Subscription — VARCHAR!
        sa.Column('subscription_tier', sa.String(20), server_default='free', nullable=False),
        sa.Column('subscription_expires_at', sa.DateTime(), nullable=True),
        
        # Rate limiting
        sa.Column('daily_requests', sa.Integer(), server_default='0'),
        sa.Column('last_request_date', sa.DateTime(), nullable=True),
        
        # Streak
        sa.Column('current_streak', sa.Integer(), server_default='0'),
        sa.Column('longest_streak', sa.Integer(), server_default='0'),
        sa.Column('last_activity_date', sa.DateTime(), nullable=True),
        
        # Referral System
        sa.Column('referral_code', sa.String(20), nullable=True),
        sa.Column('referred_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('referral_count', sa.Integer(), server_default='0'),
        sa.Column('referral_pro_granted', sa.Boolean(), server_default='false'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)
    op.create_index('ix_users_referral_code', 'users', ['referral_code'], unique=True)
    op.create_foreign_key('fk_users_referred_by', 'users', 'users', ['referred_by_id'], ['id'])

    # === 2. FOLDERS TABLE ===
    op.create_table(
        'folders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        
        # Group settings
        sa.Column('is_group', sa.Boolean(), server_default='false'),
        sa.Column('invite_code', sa.String(20), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('max_members', sa.Integer(), server_default='50'),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_foreign_key('fk_folders_user', 'folders', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_folders_parent', 'folders', 'folders', ['parent_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_folders_user_id', 'folders', ['user_id'])
    op.create_index('ix_folders_invite_code', 'folders', ['invite_code'], unique=True)

    # === 3. GROUP MEMBERS TABLE ===
    op.create_table(
        'group_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(20), server_default='member'),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_gm_group', 'group_members', 'folders', ['group_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_gm_user', 'group_members', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_group_members_group_id', 'group_members', ['group_id'])
    op.create_index('ix_group_members_user_id', 'group_members', ['user_id'])
    op.create_unique_constraint('uq_group_member', 'group_members', ['group_id', 'user_id'])

    # === 4. MATERIALS TABLE ===
    op.create_table(
        'materials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('folder_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),  
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=True),
        sa.Column('file_path', sa.String(1000), nullable=True),
        sa.Column('material_type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_foreign_key('fk_materials_user', 'materials', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_materials_folder', 'materials', 'folders', ['folder_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_materials_user_id', 'materials', ['user_id'])
    op.create_index('ix_materials_folder_id', 'materials', ['folder_id'])

    # === 5. AI OUTPUTS TABLE ===
    op.create_table(
        'ai_outputs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('format', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_outputs_material', 'ai_outputs', 'materials', ['material_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_ai_outputs_material_id', 'ai_outputs', ['material_id'])
    op.create_unique_constraint('uq_material_format', 'ai_outputs', ['material_id', 'format'])

    # === 6. QUIZ RESULTS TABLE ===
    op.create_table(
        'quiz_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('max_score', sa.Integer(), nullable=False),
        sa.Column('percentage', sa.Integer(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_quiz_user', 'quiz_results', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_quiz_material', 'quiz_results', 'materials', ['material_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_quiz_group', 'quiz_results', 'folders', ['group_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_quiz_results_user_id', 'quiz_results', ['user_id'])
    op.create_index('ix_quiz_results_material_id', 'quiz_results', ['material_id'])
    op.create_index('ix_quiz_results_group_id', 'quiz_results', ['group_id'])

    # === 7. TEXT CHUNKS TABLE (для vector search) ===
    op.create_table(
        'text_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('char_start', sa.Integer(), nullable=True),
        sa.Column('char_end', sa.Integer(), nullable=True),
    )
    op.create_foreign_key('fk_chunks_material', 'text_chunks', 'materials', ['material_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_text_chunks_material_id', 'text_chunks', ['material_id'])


def downgrade() -> None:
    op.drop_table('text_chunks')
    op.drop_table('quiz_results')
    op.drop_table('ai_outputs')
    op.drop_table('materials')
    op.drop_table('group_members')
    op.drop_table('folders')
    op.drop_table('users')