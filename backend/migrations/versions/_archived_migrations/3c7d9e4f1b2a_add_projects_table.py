"""Add projects table for multi-project manufacturing

Revision ID: 3c7d9e4f1b2a
Revises: 2fd042a8a882
Create Date: 2025-11-09 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3c7d9e4f1b2a'
down_revision = '2fd042a8a882'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ProjectStatus enum type if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE projectstatus AS ENUM ('PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'CANCELLED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('plant_id', sa.Integer(), nullable=False),
        sa.Column('project_code', sa.String(length=50), nullable=False),
        sa.Column('project_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('bom_id', sa.Integer(), nullable=True),
        sa.Column('planned_start_date', sa.Date(), nullable=True),
        sa.Column('planned_end_date', sa.Date(), nullable=True),
        sa.Column('actual_start_date', sa.Date(), nullable=True),
        sa.Column('actual_end_date', sa.Date(), nullable=True),
        sa.Column('status', postgresql.ENUM('PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'CANCELLED', name='projectstatus', create_type=False), nullable=False, server_default=sa.text("'PLANNING'::projectstatus")),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('planned_end_date >= planned_start_date', name='check_dates'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bom_id'], ['bom_header.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plant_id', 'project_code', name='uq_project_code_per_plant')
    )

    # Create indexes
    op.create_index('idx_project_org', 'projects', ['organization_id'], unique=False)
    op.create_index('idx_project_plant', 'projects', ['plant_id'], unique=False)
    op.create_index('idx_project_status', 'projects', ['status'], unique=False)
    op.create_index('idx_project_bom', 'projects', ['bom_id'], unique=False)
    op.create_index(op.f('ix_projects_organization_id'), 'projects', ['organization_id'], unique=False)
    op.create_index(op.f('ix_projects_plant_id'), 'projects', ['plant_id'], unique=False)
    op.create_index(op.f('ix_projects_bom_id'), 'projects', ['bom_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_projects_bom_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_plant_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_organization_id'), table_name='projects')
    op.drop_index('idx_project_bom', table_name='projects')
    op.drop_index('idx_project_status', table_name='projects')
    op.drop_index('idx_project_plant', table_name='projects')
    op.drop_index('idx_project_org', table_name='projects')

    # Drop table
    op.drop_table('projects')

    # Drop enum type
    project_status_enum = postgresql.ENUM(
        'PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'CANCELLED',
        name='projectstatus'
    )
    project_status_enum.drop(op.get_bind(), checkfirst=True)
