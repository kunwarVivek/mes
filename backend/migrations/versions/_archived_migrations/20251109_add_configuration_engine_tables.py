"""Add Configuration Engine tables (custom_fields, field_values, type_lists)

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-11-09 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create custom_fields table
    op.create_table(
        'custom_fields',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),  # material, work_order, ncr, etc.
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('field_code', sa.String(length=50), nullable=False),  # Internal identifier
        sa.Column('field_label', sa.String(length=100), nullable=False),  # Display label
        sa.Column('field_type', sa.String(length=50), nullable=False),  # text, number, date, select, multiselect, boolean, file
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),

        # Validation rules (JSONB)
        # {
        #   "min_length": 5,
        #   "max_length": 100,
        #   "pattern": "^[A-Z0-9-]+$",
        #   "min_value": 0,
        #   "max_value": 100,
        #   "allowed_file_types": ["pdf", "jpg", "png"]
        # }
        sa.Column('validation_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Options for select/multiselect (JSONB)
        # [
        #   {"value": "option1", "label": "Option 1"},
        #   {"value": "option2", "label": "Option 2"}
        # ]
        sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # UI hints (JSONB)
        # {
        #   "placeholder": "Enter value...",
        #   "help_text": "This field is for...",
        #   "icon": "calendar",
        #   "width": "full"
        # }
        sa.Column('ui_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'entity_type', 'field_code',
                           name='uq_custom_field_code_per_entity'),
        sa.Index('idx_custom_fields_org', 'organization_id'),
        sa.Index('idx_custom_fields_entity', 'organization_id', 'entity_type'),
        sa.Index('idx_custom_fields_active', 'organization_id', 'entity_type', 'is_active'),
        sa.CheckConstraint(
            "field_type IN ('text', 'number', 'date', 'datetime', 'select', 'multiselect', 'boolean', 'file', 'textarea', 'email', 'url', 'phone')",
            name='chk_field_type_valid'
        ),
    )

    # Create field_values table
    op.create_table(
        'field_values',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('custom_field_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),

        # JSONB storage for flexibility
        # Allows storing any value type: string, number, array, etc.
        sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['custom_field_id'], ['custom_fields.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('custom_field_id', 'entity_id', name='uq_field_value_per_entity'),
        sa.Index('idx_field_values_org', 'organization_id'),
        sa.Index('idx_field_values_entity', 'entity_type', 'entity_id'),
        sa.Index('idx_field_values_field', 'custom_field_id'),
        # GIN index for JSONB value search
        sa.Index('idx_field_values_value_gin', 'value', postgresql_using='gin'),
    )

    # Create type_lists table (configurable taxonomies)
    op.create_table(
        'type_lists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('list_name', sa.String(length=100), nullable=False),
        sa.Column('list_code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),  # Group related lists
        sa.Column('is_system_list', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allow_custom_values', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'list_code', name='uq_type_list_code_per_org'),
        sa.Index('idx_type_lists_org', 'organization_id'),
        sa.Index('idx_type_lists_code', 'organization_id', 'list_code'),
        sa.Index('idx_type_lists_category', 'organization_id', 'category'),
    )

    # Create type_list_values table
    op.create_table(
        'type_list_values',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('type_list_id', sa.Integer(), nullable=False),
        sa.Column('value_code', sa.String(length=50), nullable=False),
        sa.Column('value_label', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Additional metadata (JSONB)
        # {
        #   "color": "#FF0000",
        #   "icon": "alert-triangle",
        #   "severity": "high",
        #   "requires_approval": true
        # }
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['type_list_id'], ['type_lists.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('type_list_id', 'value_code', name='uq_type_value_code_per_list'),
        sa.Index('idx_type_list_values_org', 'organization_id'),
        sa.Index('idx_type_list_values_list', 'type_list_id'),
        sa.Index('idx_type_list_values_active', 'type_list_id', 'is_active'),
    )

    # Enable RLS on all tables
    op.execute("ALTER TABLE custom_fields ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE field_values ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE type_lists ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE type_list_values ENABLE ROW LEVEL SECURITY")

    # Create RLS policies
    op.execute("""
        CREATE POLICY custom_fields_org_isolation ON custom_fields
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY field_values_org_isolation ON field_values
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY type_lists_org_isolation ON type_lists
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY type_list_values_org_isolation ON type_list_values
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    # Insert default type lists for all organizations

    # NCR Severity Levels
    op.execute("""
        INSERT INTO type_lists (organization_id, list_name, list_code, description, category, is_system_list)
        SELECT o.id, 'NCR Severity Levels', 'NCR_SEVERITY',
               'Severity classification for Non-Conformance Reports', 'quality', true
        FROM organizations o
    """)

    op.execute("""
        INSERT INTO type_list_values (organization_id, type_list_id, value_code, value_label, description, display_order, metadata)
        SELECT
            tl.organization_id,
            tl.id,
            'MINOR',
            'Minor',
            'Minor non-conformance with minimal impact',
            1,
            '{"color": "#fbbf24", "severity": "low"}'::jsonb
        FROM type_lists tl
        WHERE tl.list_code = 'NCR_SEVERITY'

        UNION ALL

        SELECT
            tl.organization_id,
            tl.id,
            'MAJOR',
            'Major',
            'Major non-conformance requiring corrective action',
            2,
            '{"color": "#f97316", "severity": "medium", "requires_approval": true}'::jsonb
        FROM type_lists tl
        WHERE tl.list_code = 'NCR_SEVERITY'

        UNION ALL

        SELECT
            tl.organization_id,
            tl.id,
            'CRITICAL',
            'Critical',
            'Critical non-conformance requiring immediate action',
            3,
            '{"color": "#ef4444", "severity": "high", "requires_approval": true}'::jsonb
        FROM type_lists tl
        WHERE tl.list_code = 'NCR_SEVERITY'
    """)

    # Defect Types
    op.execute("""
        INSERT INTO type_lists (organization_id, list_name, list_code, description, category, is_system_list)
        SELECT o.id, 'Defect Types', 'DEFECT_TYPE',
               'Classification of defect types', 'quality', true
        FROM organizations o
    """)

    op.execute("""
        INSERT INTO type_list_values (organization_id, type_list_id, value_code, value_label, display_order)
        SELECT tl.organization_id, tl.id, v.code, v.label, v.ord
        FROM type_lists tl
        CROSS JOIN (
            VALUES
                ('DIMENSIONAL', 'Dimensional', 1),
                ('VISUAL', 'Visual/Cosmetic', 2),
                ('FUNCTIONAL', 'Functional', 3),
                ('MATERIAL', 'Material', 4),
                ('ASSEMBLY', 'Assembly', 5),
                ('DOCUMENTATION', 'Documentation', 6),
                ('OTHER', 'Other', 7)
        ) AS v(code, label, ord)
        WHERE tl.list_code = 'DEFECT_TYPE'
    """)

    # Work Order Priority
    op.execute("""
        INSERT INTO type_lists (organization_id, list_name, list_code, description, category, is_system_list)
        SELECT o.id, 'Work Order Priority', 'WO_PRIORITY',
               'Priority levels for work orders', 'production', true
        FROM organizations o
    """)

    op.execute("""
        INSERT INTO type_list_values (organization_id, type_list_id, value_code, value_label, display_order, metadata)
        SELECT tl.organization_id, tl.id, v.code, v.label, v.ord, v.meta::jsonb
        FROM type_lists tl
        CROSS JOIN (
            VALUES
                ('LOW', 'Low', 1, '{"color": "#10b981"}'),
                ('NORMAL', 'Normal', 2, '{"color": "#3b82f6"}'),
                ('HIGH', 'High', 3, '{"color": "#f97316"}'),
                ('URGENT', 'Urgent', 4, '{"color": "#ef4444"}')
        ) AS v(code, label, ord, meta)
        WHERE tl.list_code = 'WO_PRIORITY'
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS custom_fields_org_isolation ON custom_fields")
    op.execute("DROP POLICY IF EXISTS field_values_org_isolation ON field_values")
    op.execute("DROP POLICY IF EXISTS type_lists_org_isolation ON type_lists")
    op.execute("DROP POLICY IF EXISTS type_list_values_org_isolation ON type_list_values")

    # Drop tables
    op.drop_table('type_list_values')
    op.drop_table('type_lists')
    op.drop_table('field_values')
    op.drop_table('custom_fields')
