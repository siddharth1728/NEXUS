import uuid
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # refresh_sessions
    op.create_table(
        'refresh_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_sessions_id'), 'refresh_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_refresh_sessions_token_hash'), 'refresh_sessions', ['token_hash'], unique=True)
    op.create_index(op.f('ix_refresh_sessions_user_id'), 'refresh_sessions', ['user_id'], unique=False)

    # target_roles
    op.create_table(
        'target_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_target_roles_id'), 'target_roles', ['id'], unique=False)
    op.create_index(op.f('ix_target_roles_name'), 'target_roles', ['name'], unique=True)

    # skills
    op.create_table(
        'skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_skills_category'), 'skills', ['category'], unique=False)
    op.create_index(op.f('ix_skills_id'), 'skills', ['id'], unique=False)
    op.create_index(op.f('ix_skills_name'), 'skills', ['name'], unique=True)

    # student_profiles
    op.create_table(
        'student_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('target_role_id', sa.Integer(), nullable=True),
        sa.Column('github_username', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['target_role_id'], ['target_roles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_profiles_id'), 'student_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_student_profiles_target_role_id'), 'student_profiles', ['target_role_id'], unique=False)
    op.create_index(op.f('ix_student_profiles_user_id'), 'student_profiles', ['user_id'], unique=True)

    # target_role_skills
    op.create_table(
        'target_role_skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('target_role_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('importance_weight', sa.Float(), nullable=False),
        sa.Column('minimum_expected_state', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_role_id'], ['target_roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_target_role_skills_id'), 'target_role_skills', ['id'], unique=False)
    op.create_index(op.f('ix_target_role_skills_skill_id'), 'target_role_skills', ['skill_id'], unique=False)
    op.create_index(op.f('ix_target_role_skills_target_role_id'), 'target_role_skills', ['target_role_id'], unique=False)

def downgrade():
    op.drop_table('target_role_skills')
    op.drop_table('student_profiles')
    op.drop_table('skills')
    op.drop_table('target_roles')
    op.drop_table('refresh_sessions')
    op.drop_table('users')
