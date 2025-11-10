"""Add reporting and dashboards tables (reports, report_executions, dashboards)

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-11-10 00:00:00.000000

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
    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('report_name', sa.String(length=200), nullable=False),
        sa.Column('report_code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('report_type', sa.String(length=50), nullable=False),  # KPI, CUSTOM, SCHEDULED, AD_HOC
        sa.Column('category', sa.String(length=100), nullable=True),  # PRODUCTION, QUALITY, INVENTORY, etc.

        # Report definition
        sa.Column('query_definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        # Structure: {
        #   "data_source": "production_logs|work_orders|ncr|etc",
        #   "columns": [...],
        #   "filters": [...],
        #   "aggregations": [...],
        #   "joins": [...]
        # }

        # Display configuration
        sa.Column('display_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Structure: {
        #   "chart_type": "bar|line|pie|table",
        #   "x_axis": "...",
        #   "y_axis": "...",
        #   "colors": [...],
        #   "format": {...}
        # }

        # Scheduling
        sa.Column('is_scheduled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('schedule_cron', sa.String(length=100), nullable=True),  # Cron expression
        sa.Column('schedule_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Export options
        sa.Column('export_formats', postgresql.ARRAY(sa.String()), nullable=True),  # ['PDF', 'CSV', 'XLSX']
        sa.Column('auto_email', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('email_recipients', postgresql.ARRAY(sa.String()), nullable=True),

        # Ownership and permissions
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('shared_with_users', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('shared_with_roles', postgresql.ARRAY(sa.Integer()), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_system_report', sa.Boolean(), nullable=False, server_default='false'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('last_executed_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('organization_id', 'report_code', name='uq_report_code_per_org'),
        sa.Index('idx_reports_org', 'organization_id'),
        sa.Index('idx_reports_type', 'report_type'),
        sa.Index('idx_reports_category', 'category'),
        sa.Index('idx_reports_created_by', 'created_by'),
        sa.Index('idx_reports_scheduled', 'is_scheduled', 'is_active'),
        sa.CheckConstraint(
            "report_type IN ('KPI', 'CUSTOM', 'SCHEDULED', 'AD_HOC')",
            name='chk_report_type_valid'
        ),
    )

    # Create report_executions table
    op.create_table(
        'report_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),

        # Execution details
        sa.Column('execution_status', sa.String(length=50), nullable=False),  # PENDING, RUNNING, COMPLETED, FAILED
        sa.Column('triggered_by', sa.Integer(), nullable=True),  # User ID or NULL for scheduled
        sa.Column('trigger_type', sa.String(length=50), nullable=False),  # MANUAL, SCHEDULED, API

        # Execution metadata
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Structure: {
        #   "date_range": {"start": "...", "end": "..."},
        #   "filters": {...},
        #   "plant_id": 123
        # }

        # Results
        sa.Column('result_count', sa.Integer(), nullable=True),
        sa.Column('result_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # Store small results
        sa.Column('result_file_path', sa.String(length=500), nullable=True),  # Path to exported file
        sa.Column('export_format', sa.String(length=20), nullable=True),  # PDF, CSV, XLSX

        # Performance metrics
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('rows_processed', sa.Integer(), nullable=True),

        # Error handling
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_stack_trace', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['triggered_by'], ['users.id'], ondelete='SET NULL'),
        sa.Index('idx_report_executions_org', 'organization_id'),
        sa.Index('idx_report_executions_report', 'report_id'),
        sa.Index('idx_report_executions_status', 'execution_status'),
        sa.Index('idx_report_executions_started', 'started_at'),
        sa.Index('idx_report_executions_trigger', 'trigger_type'),
        sa.CheckConstraint(
            "execution_status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name='chk_execution_status_valid'
        ),
        sa.CheckConstraint(
            "trigger_type IN ('MANUAL', 'SCHEDULED', 'API')",
            name='chk_trigger_type_valid'
        ),
    )

    # Create dashboards table
    op.create_table(
        'dashboards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('dashboard_name', sa.String(length=200), nullable=False),
        sa.Column('dashboard_code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('dashboard_type', sa.String(length=50), nullable=False),  # OVERVIEW, PRODUCTION, QUALITY, INVENTORY

        # Layout configuration
        sa.Column('layout_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        # Structure: {
        #   "grid": {
        #     "columns": 12,
        #     "row_height": 100
        #   },
        #   "widgets": [
        #     {
        #       "id": "widget_1",
        #       "type": "kpi_card|chart|table",
        #       "position": {"x": 0, "y": 0, "w": 4, "h": 2},
        #       "config": {...}
        #     }
        #   ]
        # }

        # Widget definitions
        sa.Column('widgets', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        # Structure: {
        #   "widget_1": {
        #     "title": "OEE",
        #     "type": "kpi_card",
        #     "data_source": "report_id|custom_query",
        #     "refresh_interval": 300,  // seconds
        #     "config": {...}
        #   }
        # }

        # Filters
        sa.Column('default_filters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Structure: {
        #   "date_range": "last_7_days",
        #   "plant_id": null,  // null = all plants
        #   "shift_id": null
        # }

        # Auto-refresh
        sa.Column('auto_refresh', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('refresh_interval_seconds', sa.Integer(), nullable=True),

        # Ownership and permissions
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('shared_with_users', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('shared_with_roles', postgresql.ARRAY(sa.Integer()), nullable=True),

        # Display settings
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_system_dashboard', sa.Boolean(), nullable=False, server_default='false'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('organization_id', 'dashboard_code', name='uq_dashboard_code_per_org'),
        sa.Index('idx_dashboards_org', 'organization_id'),
        sa.Index('idx_dashboards_type', 'dashboard_type'),
        sa.Index('idx_dashboards_created_by', 'created_by'),
        sa.Index('idx_dashboards_default', 'organization_id', 'is_default'),
        sa.CheckConstraint(
            "dashboard_type IN ('OVERVIEW', 'PRODUCTION', 'QUALITY', 'INVENTORY', 'MAINTENANCE', 'CUSTOM')",
            name='chk_dashboard_type_valid'
        ),
    )

    # Enable RLS on all three tables
    op.execute("ALTER TABLE reports ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE report_executions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE dashboards ENABLE ROW LEVEL SECURITY")

    # Create RLS policies
    op.execute("""
        CREATE POLICY reports_org_isolation ON reports
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY report_executions_org_isolation ON report_executions
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY dashboards_org_isolation ON dashboards
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    # Insert default system reports
    op.execute("""
        INSERT INTO reports (
            organization_id, report_name, report_code, description, report_type, category,
            query_definition, is_system_report, created_by, is_public
        )
        SELECT
            o.id,
            'Overall Equipment Effectiveness (OEE)',
            'OEE_REPORT',
            'Calculate OEE (Availability × Performance × Quality) across machines and time periods',
            'KPI',
            'PRODUCTION',
            '{
                "data_source": "production_logs",
                "columns": ["machine_id", "oee_percentage", "availability", "performance", "quality"],
                "aggregations": ["avg"],
                "group_by": ["machine_id", "date"]
            }'::jsonb,
            true,
            (SELECT id FROM users WHERE organization_id = o.id LIMIT 1),
            true
        FROM organizations o
    """)

    op.execute("""
        INSERT INTO reports (
            organization_id, report_name, report_code, description, report_type, category,
            query_definition, is_system_report, created_by, is_public
        )
        SELECT
            o.id,
            'First Pass Yield (FPY)',
            'FPY_REPORT',
            'Track first-time quality yield across production runs',
            'KPI',
            'QUALITY',
            '{
                "data_source": "production_logs",
                "columns": ["work_order_id", "total_quantity", "good_quantity", "fpy_percentage"],
                "aggregations": ["sum", "avg"],
                "group_by": ["date", "material_id"]
            }'::jsonb,
            true,
            (SELECT id FROM users WHERE organization_id = o.id LIMIT 1),
            true
        FROM organizations o
    """)

    op.execute("""
        INSERT INTO reports (
            organization_id, report_name, report_code, description, report_type, category,
            query_definition, is_system_report, created_by, is_public
        )
        SELECT
            o.id,
            'On-Time Delivery (OTD)',
            'OTD_REPORT',
            'Measure on-time delivery performance for work orders',
            'KPI',
            'PRODUCTION',
            '{
                "data_source": "work_orders",
                "columns": ["work_order_number", "due_date", "completion_date", "on_time_status"],
                "aggregations": ["count", "percentage"],
                "group_by": ["date", "customer"]
            }'::jsonb,
            true,
            (SELECT id FROM users WHERE organization_id = o.id LIMIT 1),
            true
        FROM organizations o
    """)

    # Insert default system dashboard
    op.execute("""
        INSERT INTO dashboards (
            organization_id, dashboard_name, dashboard_code, description, dashboard_type,
            layout_config, widgets, is_default, is_system_dashboard, created_by, is_public
        )
        SELECT
            o.id,
            'Production Overview',
            'PRODUCTION_OVERVIEW',
            'Main production dashboard with key KPIs and metrics',
            'OVERVIEW',
            '{
                "grid": {"columns": 12, "row_height": 100},
                "widgets": [
                    {"id": "oee", "type": "kpi_card", "position": {"x": 0, "y": 0, "w": 4, "h": 2}},
                    {"id": "fpy", "type": "kpi_card", "position": {"x": 4, "y": 0, "w": 4, "h": 2}},
                    {"id": "otd", "type": "kpi_card", "position": {"x": 8, "y": 0, "w": 4, "h": 2}},
                    {"id": "production_trend", "type": "chart", "position": {"x": 0, "y": 2, "w": 12, "h": 4}}
                ]
            }'::jsonb,
            '{
                "oee": {"title": "OEE", "type": "kpi_card", "data_source": "OEE_REPORT", "refresh_interval": 300},
                "fpy": {"title": "First Pass Yield", "type": "kpi_card", "data_source": "FPY_REPORT", "refresh_interval": 300},
                "otd": {"title": "On-Time Delivery", "type": "kpi_card", "data_source": "OTD_REPORT", "refresh_interval": 300},
                "production_trend": {"title": "Production Trend", "type": "chart", "chart_type": "line", "refresh_interval": 600}
            }'::jsonb,
            true,
            true,
            (SELECT id FROM users WHERE organization_id = o.id LIMIT 1),
            true
        FROM organizations o
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS reports_org_isolation ON reports")
    op.execute("DROP POLICY IF EXISTS report_executions_org_isolation ON report_executions")
    op.execute("DROP POLICY IF EXISTS dashboards_org_isolation ON dashboards")

    # Drop tables
    op.drop_table('dashboards')
    op.drop_table('report_executions')
    op.drop_table('reports')
