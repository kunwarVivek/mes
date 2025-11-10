"""Add Workflow Engine tables (workflows, workflow_states, workflow_transitions, approvals)

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2025-11-09 19:00:00.000000

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
    # Create workflows table
    op.create_table(
        'workflows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('workflow_name', sa.String(length=100), nullable=False),
        sa.Column('workflow_code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('entity_type', sa.String(length=50), nullable=False),  # ncr, rda_drawing, work_order, etc.
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),  # Default workflow for entity type

        # Workflow configuration (JSONB)
        # {
        #   "auto_assign_rules": {...},
        #   "notification_rules": {...},
        #   "escalation_rules": {...},
        #   "allow_skip_states": false,
        #   "require_comments": true
        # }
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'workflow_code', name='uq_workflow_code_per_org'),
        sa.Index('idx_workflows_org', 'organization_id'),
        sa.Index('idx_workflows_entity', 'organization_id', 'entity_type'),
        sa.Index('idx_workflows_default', 'organization_id', 'entity_type', 'is_default'),
    )

    # Create workflow_states table
    op.create_table(
        'workflow_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('state_name', sa.String(length=100), nullable=False),
        sa.Column('state_code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('state_type', sa.String(length=50), nullable=False),  # initial, intermediate, final, cancelled
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # State configuration (JSONB)
        # {
        #   "color": "#3b82f6",
        #   "icon": "clock",
        #   "requires_approval": true,
        #   "approval_count": 2,
        #   "approval_roles": ["QUALITY_MANAGER", "PLANT_MANAGER"],
        #   "auto_actions": [{"action": "send_notification", "params": {...}}]
        # }
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('workflow_id', 'state_code', name='uq_state_code_per_workflow'),
        sa.Index('idx_workflow_states_org', 'organization_id'),
        sa.Index('idx_workflow_states_workflow', 'workflow_id'),
        sa.Index('idx_workflow_states_type', 'workflow_id', 'state_type'),
        sa.CheckConstraint(
            "state_type IN ('initial', 'intermediate', 'final', 'cancelled')",
            name='chk_state_type_valid'
        ),
    )

    # Create workflow_transitions table
    op.create_table(
        'workflow_transitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('from_state_id', sa.Integer(), nullable=False),
        sa.Column('to_state_id', sa.Integer(), nullable=False),
        sa.Column('transition_name', sa.String(length=100), nullable=False),
        sa.Column('transition_code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Conditions for transition (JSONB)
        # {
        #   "required_roles": ["QUALITY_MANAGER"],
        #   "required_fields": ["root_cause", "corrective_action"],
        #   "custom_conditions": [
        #     {"field": "severity", "operator": "in", "value": ["MAJOR", "CRITICAL"]}
        #   ]
        # }
        sa.Column('conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Actions to execute on transition (JSONB)
        # {
        #   "pre_actions": [{"action": "validate_fields", "params": {...}}],
        #   "post_actions": [
        #     {"action": "send_notification", "params": {"recipients": "assignee"}},
        #     {"action": "create_approval", "params": {"approver_roles": ["MANAGER"]}}
        #   ]
        # }
        sa.Column('actions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_state_id'], ['workflow_states.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_state_id'], ['workflow_states.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('workflow_id', 'from_state_id', 'to_state_id', name='uq_transition_per_workflow'),
        sa.Index('idx_workflow_transitions_org', 'organization_id'),
        sa.Index('idx_workflow_transitions_workflow', 'workflow_id'),
        sa.Index('idx_workflow_transitions_from', 'from_state_id'),
        sa.Index('idx_workflow_transitions_to', 'to_state_id'),
    )

    # Create approvals table
    op.create_table(
        'approvals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('workflow_state_id', sa.Integer(), nullable=False),

        # Approval details
        sa.Column('approver_id', sa.Integer(), nullable=False),
        sa.Column('approver_role_id', sa.Integer(), nullable=True),  # Role that authorized this approval
        sa.Column('status', sa.String(length=50), nullable=False),  # pending, approved, rejected
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('decision_date', sa.DateTime(timezone=True), nullable=True),

        # Request metadata
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('requested_by', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default='normal'),

        # Approval metadata (JSONB)
        # {
        #   "attachments": [...],
        #   "custom_fields": {...},
        #   "notification_sent": true,
        #   "reminder_count": 2
        # }
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_state_id'], ['workflow_states.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approver_role_id'], ['roles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id'], ondelete='SET NULL'),
        sa.Index('idx_approvals_org', 'organization_id'),
        sa.Index('idx_approvals_entity', 'entity_type', 'entity_id'),
        sa.Index('idx_approvals_approver', 'approver_id', 'status'),
        sa.Index('idx_approvals_workflow', 'workflow_id'),
        sa.Index('idx_approvals_status', 'status', 'due_date'),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'cancelled')",
            name='chk_approval_status_valid'
        ),
        sa.CheckConstraint(
            "priority IN ('low', 'normal', 'high', 'urgent')",
            name='chk_approval_priority_valid'
        ),
    )

    # Create workflow_history table for audit trail
    op.create_table(
        'workflow_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('from_state_id', sa.Integer(), nullable=True),
        sa.Column('to_state_id', sa.Integer(), nullable=False),
        sa.Column('transition_id', sa.Integer(), nullable=True),
        sa.Column('action_type', sa.String(length=50), nullable=False),  # transition, approval, rejection, cancellation
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('action_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        # Change snapshot (JSONB)
        # {
        #   "changes": {...},
        #   "approval_id": 123,
        #   "metadata": {...}
        # }
        sa.Column('change_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_state_id'], ['workflow_states.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['to_state_id'], ['workflow_states.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transition_id'], ['workflow_transitions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.Index('idx_workflow_history_org', 'organization_id'),
        sa.Index('idx_workflow_history_entity', 'entity_type', 'entity_id'),
        sa.Index('idx_workflow_history_actor', 'actor_id'),
        sa.Index('idx_workflow_history_date', 'action_date'),
    )

    # Enable RLS on all tables
    op.execute("ALTER TABLE workflows ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workflow_states ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workflow_transitions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE approvals ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workflow_history ENABLE ROW LEVEL SECURITY")

    # Create RLS policies
    op.execute("""
        CREATE POLICY workflows_org_isolation ON workflows
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY workflow_states_org_isolation ON workflow_states
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY workflow_transitions_org_isolation ON workflow_transitions
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY approvals_org_isolation ON approvals
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY workflow_history_org_isolation ON workflow_history
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    # Create default NCR workflow for all organizations
    op.execute("""
        INSERT INTO workflows (organization_id, workflow_name, workflow_code, description, entity_type, is_default)
        SELECT o.id, 'NCR Approval Workflow', 'NCR_APPROVAL',
               'Standard workflow for Non-Conformance Report approval', 'ncr', true
        FROM organizations o
    """)

    # Create NCR workflow states
    op.execute("""
        INSERT INTO workflow_states (organization_id, workflow_id, state_name, state_code, state_type, display_order, config)
        SELECT
            w.organization_id,
            w.id,
            'Draft',
            'DRAFT',
            'initial',
            1,
            '{"color": "#9ca3af", "icon": "file-text", "requires_approval": false}'::jsonb
        FROM workflows w
        WHERE w.workflow_code = 'NCR_APPROVAL'
    """)

    op.execute("""
        INSERT INTO workflow_states (organization_id, workflow_id, state_name, state_code, state_type, display_order, config)
        SELECT
            w.organization_id,
            w.id,
            'Submitted',
            'SUBMITTED',
            'intermediate',
            2,
            '{"color": "#3b82f6", "icon": "send", "requires_approval": true, "approval_roles": ["QUALITY_MANAGER"]}'::jsonb
        FROM workflows w
        WHERE w.workflow_code = 'NCR_APPROVAL'
    """)

    op.execute("""
        INSERT INTO workflow_states (organization_id, workflow_id, state_name, state_code, state_type, display_order, config)
        SELECT
            w.organization_id,
            w.id,
            'Under Review',
            'UNDER_REVIEW',
            'intermediate',
            3,
            '{"color": "#f59e0b", "icon": "eye", "requires_approval": false}'::jsonb
        FROM workflows w
        WHERE w.workflow_code = 'NCR_APPROVAL'
    """)

    op.execute("""
        INSERT INTO workflow_states (organization_id, workflow_id, state_name, state_code, state_type, display_order, config)
        SELECT
            w.organization_id,
            w.id,
            'Approved',
            'APPROVED',
            'final',
            4,
            '{"color": "#10b981", "icon": "check-circle", "requires_approval": false}'::jsonb
        FROM workflows w
        WHERE w.workflow_code = 'NCR_APPROVAL'
    """)

    op.execute("""
        INSERT INTO workflow_states (organization_id, workflow_id, state_name, state_code, state_type, display_order, config)
        SELECT
            w.organization_id,
            w.id,
            'Rejected',
            'REJECTED',
            'final',
            5,
            '{"color": "#ef4444", "icon": "x-circle", "requires_approval": false}'::jsonb
        FROM workflows w
        WHERE w.workflow_code = 'NCR_APPROVAL'
    """)

    op.execute("""
        INSERT INTO workflow_states (organization_id, workflow_id, state_name, state_code, state_type, display_order, config)
        SELECT
            w.organization_id,
            w.id,
            'Cancelled',
            'CANCELLED',
            'cancelled',
            6,
            '{"color": "#6b7280", "icon": "ban", "requires_approval": false}'::jsonb
        FROM workflows w
        WHERE w.workflow_code = 'NCR_APPROVAL'
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS workflows_org_isolation ON workflows")
    op.execute("DROP POLICY IF EXISTS workflow_states_org_isolation ON workflow_states")
    op.execute("DROP POLICY IF EXISTS workflow_transitions_org_isolation ON workflow_transitions")
    op.execute("DROP POLICY IF EXISTS approvals_org_isolation ON approvals")
    op.execute("DROP POLICY IF EXISTS workflow_history_org_isolation ON workflow_history")

    # Drop tables
    op.drop_table('workflow_history')
    op.drop_table('approvals')
    op.drop_table('workflow_transitions')
    op.drop_table('workflow_states')
    op.drop_table('workflows')
