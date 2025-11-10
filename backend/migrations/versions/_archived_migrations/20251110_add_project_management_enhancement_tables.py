"""Add project management enhancement tables (project_documents, project_milestones, rda_drawings, project_bom)

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2025-11-10 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 'b2c3d4e5f6g7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create project_documents table
    op.create_table(
        'project_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),

        # Document identification
        sa.Column('document_name', sa.String(length=200), nullable=False),
        sa.Column('document_code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('document_type', sa.String(length=50), nullable=False),  # DRAWING, SPEC, REPORT, CONTRACT, etc.
        sa.Column('category', sa.String(length=100), nullable=True),

        # Version control
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_latest_version', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('parent_document_id', sa.Integer(), nullable=True),  # For version history

        # File information
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),  # SHA-256 hash

        # Metadata
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Ownership and access
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('approval_status', sa.String(length=50), nullable=True),  # PENDING, APPROVED, REJECTED

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_document_id'], ['project_documents.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('project_id', 'document_code', 'version', name='uq_project_document_version'),
        sa.Index('idx_project_documents_org', 'organization_id'),
        sa.Index('idx_project_documents_project', 'project_id'),
        sa.Index('idx_project_documents_type', 'document_type'),
        sa.Index('idx_project_documents_latest', 'project_id', 'is_latest_version'),
        sa.CheckConstraint(
            "document_type IN ('DRAWING', 'SPEC', 'REPORT', 'CONTRACT', 'PROCEDURE', 'MANUAL', 'OTHER')",
            name='chk_document_type_valid'
        ),
    )

    # Create project_milestones table
    op.create_table(
        'project_milestones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),

        # Milestone identification
        sa.Column('milestone_name', sa.String(length=200), nullable=False),
        sa.Column('milestone_code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('milestone_type', sa.String(length=50), nullable=False),  # DESIGN, PROCUREMENT, PRODUCTION, DELIVERY, etc.

        # Scheduling
        sa.Column('planned_date', sa.Date(), nullable=False),
        sa.Column('baseline_date', sa.Date(), nullable=True),  # Original planned date
        sa.Column('actual_date', sa.Date(), nullable=True),
        sa.Column('is_critical_path', sa.Boolean(), nullable=False, server_default='false'),

        # Progress tracking
        sa.Column('status', sa.String(length=50), nullable=False),  # NOT_STARTED, IN_PROGRESS, COMPLETED, DELAYED, CANCELLED
        sa.Column('completion_percentage', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('dependencies', postgresql.ARRAY(sa.Integer()), nullable=True),  # Array of milestone IDs

        # Deliverables
        sa.Column('deliverables', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Structure: [
        #   {"name": "Design Drawings", "status": "completed", "document_id": 123},
        #   {"name": "BOM", "status": "in_progress"}
        # ]

        # Responsibility
        sa.Column('owner_user_id', sa.Integer(), nullable=True),
        sa.Column('assigned_team', sa.String(length=100), nullable=True),

        # Notifications
        sa.Column('alert_days_before', sa.Integer(), nullable=True),
        sa.Column('alert_recipients', postgresql.ARRAY(sa.String()), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('project_id', 'milestone_code', name='uq_project_milestone_code'),
        sa.Index('idx_project_milestones_org', 'organization_id'),
        sa.Index('idx_project_milestones_project', 'project_id'),
        sa.Index('idx_project_milestones_status', 'status'),
        sa.Index('idx_project_milestones_date', 'planned_date'),
        sa.CheckConstraint(
            "status IN ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'DELAYED', 'CANCELLED')",
            name='chk_milestone_status_valid'
        ),
        sa.CheckConstraint(
            "completion_percentage >= 0 AND completion_percentage <= 100",
            name='chk_milestone_completion_valid'
        ),
    )

    # Create rda_drawings table (Request for Drawing Approval)
    op.create_table(
        'rda_drawings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=True),  # Link to project_documents

        # RDA identification
        sa.Column('rda_number', sa.String(length=100), nullable=False),
        sa.Column('drawing_number', sa.String(length=100), nullable=False),
        sa.Column('drawing_title', sa.String(length=200), nullable=False),
        sa.Column('revision', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Workflow integration
        sa.Column('workflow_id', sa.Integer(), nullable=True),
        sa.Column('current_workflow_state_id', sa.Integer(), nullable=True),
        sa.Column('approval_status', sa.String(length=50), nullable=False),  # DRAFT, SUBMITTED, IN_REVIEW, APPROVED, REJECTED, SUPERSEDED

        # Submission details
        sa.Column('submitted_by', sa.Integer(), nullable=False),
        sa.Column('submitted_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('required_approval_date', sa.Date(), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default='NORMAL'),  # LOW, NORMAL, HIGH, URGENT

        # Approval tracking
        sa.Column('approvers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Structure: [
        #   {"user_id": 123, "role": "Design Lead", "status": "approved", "date": "...", "comments": "..."},
        #   {"user_id": 456, "role": "Project Manager", "status": "pending"}
        # ]

        # Review comments
        sa.Column('review_comments', postgresql.ARRAY(postgresql.JSONB(astext_type=sa.Text())), nullable=True),
        # Structure: [
        #   {"user_id": 123, "comment": "...", "timestamp": "...", "type": "general|markup"},
        #   {"user_id": 456, "comment": "...", "timestamp": "..."}
        # ]

        # Approval decision
        sa.Column('approved_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('rejection_date', sa.DateTime(timezone=True), nullable=True),

        # Distribution
        sa.Column('distribution_list', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('notify_on_approval', sa.Boolean(), nullable=False, server_default='true'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['project_documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['submitted_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('project_id', 'rda_number', name='uq_project_rda_number'),
        sa.Index('idx_rda_drawings_org', 'organization_id'),
        sa.Index('idx_rda_drawings_project', 'project_id'),
        sa.Index('idx_rda_drawings_status', 'approval_status'),
        sa.Index('idx_rda_drawings_drawing_number', 'drawing_number'),
        sa.CheckConstraint(
            "approval_status IN ('DRAFT', 'SUBMITTED', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'SUPERSEDED')",
            name='chk_rda_status_valid'
        ),
        sa.CheckConstraint(
            "priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')",
            name='chk_rda_priority_valid'
        ),
    )

    # Create project_bom table (Bill of Materials for projects)
    op.create_table(
        'project_bom',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),

        # BOM identification
        sa.Column('bom_code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('bom_type', sa.String(length=50), nullable=False),  # PROJECT_BOM, ASSEMBLY_BOM, PROCUREMENT_BOM

        # Item details
        sa.Column('material_id', sa.Integer(), nullable=True),  # Link to materials table
        sa.Column('part_number', sa.String(length=100), nullable=True),
        sa.Column('part_description', sa.String(length=500), nullable=True),

        # Quantity and units
        sa.Column('quantity_required', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=50), nullable=False),
        sa.Column('quantity_allocated', sa.Numeric(precision=15, scale=4), nullable=False, server_default='0'),
        sa.Column('quantity_issued', sa.Numeric(precision=15, scale=4), nullable=False, server_default='0'),

        # Hierarchy
        sa.Column('parent_bom_id', sa.Integer(), nullable=True),  # For nested BOMs
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),

        # References
        sa.Column('reference_designator', sa.String(length=100), nullable=True),
        sa.Column('drawing_reference', sa.String(length=100), nullable=True),
        sa.Column('find_number', sa.String(length=50), nullable=True),

        # Procurement
        sa.Column('procurement_status', sa.String(length=50), nullable=True),  # NOT_ORDERED, ORDERED, RECEIVED, ISSUED
        sa.Column('supplier', sa.String(length=200), nullable=True),
        sa.Column('lead_time_days', sa.Integer(), nullable=True),
        sa.Column('unit_cost', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_cost', sa.Numeric(precision=15, scale=2), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('special_instructions', sa.Text(), nullable=True),

        # Status
        sa.Column('is_critical', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_optional', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_bom_id'], ['project_bom.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('project_id', 'bom_code', name='uq_project_bom_code'),
        sa.Index('idx_project_bom_org', 'organization_id'),
        sa.Index('idx_project_bom_project', 'project_id'),
        sa.Index('idx_project_bom_material', 'material_id'),
        sa.Index('idx_project_bom_parent', 'parent_bom_id'),
        sa.Index('idx_project_bom_level', 'project_id', 'level'),
        sa.CheckConstraint(
            "bom_type IN ('PROJECT_BOM', 'ASSEMBLY_BOM', 'PROCUREMENT_BOM')",
            name='chk_project_bom_type_valid'
        ),
    )

    # Enable RLS on all four tables
    op.execute("ALTER TABLE project_documents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE project_milestones ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE rda_drawings ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE project_bom ENABLE ROW LEVEL SECURITY")

    # Create RLS policies
    op.execute("""
        CREATE POLICY project_documents_org_isolation ON project_documents
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY project_milestones_org_isolation ON project_milestones
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY rda_drawings_org_isolation ON rda_drawings
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY project_bom_org_isolation ON project_bom
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS project_documents_org_isolation ON project_documents")
    op.execute("DROP POLICY IF EXISTS project_milestones_org_isolation ON project_milestones")
    op.execute("DROP POLICY IF EXISTS rda_drawings_org_isolation ON rda_drawings")
    op.execute("DROP POLICY IF EXISTS project_bom_org_isolation ON project_bom")

    # Drop tables
    op.drop_table('project_bom')
    op.drop_table('rda_drawings')
    op.drop_table('project_milestones')
    op.drop_table('project_documents')
