"""Initial comprehensive schema - All tables

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-11-10 12:00:00.000000

This is the consolidated initial migration for the MES system.
It creates all tables from SQLAlchemy models using metadata.create_all().

For a new SaaS, this approach is cleaner than accumulating many migration files.
Future changes should use incremental migrations.

Tables created by this migration include:
- Core: organizations, users, plants, departments, projects
- Materials: materials, material_categories, units_of_measure, bom_headers, bom_lines
- Production: work_orders, work_order_operations, work_centers, work_order_materials,
              rework_configs, production_logs, work_center_shifts
- Quality: ncrs, inspection_logs, inspection_plans, inspection_points,
          inspection_characteristics, inspection_measurements
- Machines & Shifts: machines, machine_status_history, shifts, shift_handovers,
                    shift_performances, lanes, lane_assignments
- Projects: project_documents, project_milestones, rda_drawings, project_bom
- RBAC: roles, user_roles, user_plant_access
- Configuration: custom_fields, field_values, type_lists, type_list_values,
                workflows, workflow_states, workflow_transitions, approvals, workflow_history
- Logistics: shipments, shipment_items, barcode_labels, qr_code_scans
- Reporting: reports, report_executions, dashboards
- Traceability: lot_batches, serial_numbers, traceability_links, genealogy_records
- Branding: organization_branding, email_templates
- Infrastructure: audit_logs, notifications, system_settings, file_uploads,
                 sap_sync_logs, sap_mappings
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create all tables from SQLAlchemy metadata.

    This uses the metadata from Base which includes all registered models.
    """

    # Import Base to get access to metadata
    from app.core.database import Base
    import app.models  # Ensure all models are registered

    # Create all tables from metadata
    # Note: We use op.get_bind() to get the connection and create tables directly
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

    # ========================================================================
    # PostgreSQL Extensions
    # ========================================================================
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS timescaledb')
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    # ========================================================================
    # TimescaleDB Hypertables
    # Convert time-series tables to hypertables
    # ========================================================================

    # Production Logs - 1 week chunks
    op.execute("""
        SELECT create_hypertable('production_logs', 'start_time',
            chunk_time_interval => INTERVAL '1 week',
            if_not_exists => TRUE
        );
    """)

    # QR Code Scans - 1 week chunks
    op.execute("""
        SELECT create_hypertable('qr_code_scans', 'scan_timestamp',
            chunk_time_interval => INTERVAL '1 week',
            if_not_exists => TRUE
        );
    """)

    # Inspection Measurements - 1 month chunks
    op.execute("""
        SELECT create_hypertable('inspection_measurements', 'measured_at',
            chunk_time_interval => INTERVAL '1 month',
            if_not_exists => TRUE
        );
    """)

    # Genealogy Records - 3 month chunks
    op.execute("""
        SELECT create_hypertable('genealogy_records', 'operation_timestamp',
            chunk_time_interval => INTERVAL '3 months',
            if_not_exists => TRUE
        );
    """)

    # Audit Logs - 6 month chunks
    op.execute("""
        SELECT create_hypertable('audit_logs', 'timestamp',
            chunk_time_interval => INTERVAL '6 months',
            if_not_exists => TRUE
        );
    """)

    # SAP Sync Logs - 1 month chunks
    op.execute("""
        SELECT create_hypertable('sap_sync_logs', 'timestamp',
            chunk_time_interval => INTERVAL '1 month',
            if_not_exists => TRUE
        );
    """)

    # ========================================================================
    # Row-Level Security (RLS) Policies
    # Enable RLS on all tables with organization_id for multi-tenant isolation
    # ========================================================================

    # List of tables that have organization_id and need RLS
    rls_tables = [
        'users', 'plants', 'departments', 'projects',
        'materials', 'material_categories', 'bom_headers', 'bom_lines',
        'work_orders', 'work_order_operations', 'work_centers', 'work_order_materials',
        'rework_configs', 'production_logs', 'work_center_shifts',
        'ncrs', 'inspection_logs', 'inspection_plans', 'inspection_points',
        'inspection_characteristics', 'inspection_measurements',
        'machines', 'machine_status_history', 'shifts', 'shift_handovers',
        'shift_performances', 'lanes', 'lane_assignments',
        'project_documents', 'project_milestones', 'rda_drawings', 'project_bom',
        'roles', 'user_roles', 'user_plant_access',
        'custom_fields', 'field_values', 'type_lists', 'type_list_values',
        'workflows', 'workflow_states', 'workflow_transitions', 'approvals', 'workflow_history',
        'shipments', 'shipment_items', 'barcode_labels', 'qr_code_scans',
        'reports', 'report_executions', 'dashboards',
        'lot_batches', 'serial_numbers', 'traceability_links', 'genealogy_records',
        'organization_branding', 'email_templates',
        'audit_logs', 'notifications', 'system_settings', 'file_uploads',
        'sap_sync_logs', 'sap_mappings'
    ]

    for table_name in rls_tables:
        # Enable RLS
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")

        # Create organization isolation policy
        op.execute(f"""
            CREATE POLICY {table_name}_org_isolation ON {table_name}
            USING (organization_id = current_setting('app.current_organization_id', true)::int)
        """)


def downgrade() -> None:
    """
    Drop all tables.

    WARNING: This will delete ALL data!
    """
    # Import Base to get access to metadata
    from app.core.database import Base
    import app.models  # Ensure all models are registered

    # Drop all tables
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)

    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS pg_trgm')
    op.execute('DROP EXTENSION IF EXISTS pgcrypto')
    op.execute('DROP EXTENSION IF EXISTS timescaledb CASCADE')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
