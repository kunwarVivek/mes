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

    # Additional extensions for PostgreSQL-native architecture
    # Note: pgmq and pg_cron are optional extensions that may not be available in all environments
    # If they fail, the migration will continue but background jobs/queue features will be limited
    try:
        op.execute('CREATE EXTENSION IF NOT EXISTS pgmq')  # Message queue (30K msgs/sec)
        print("✓ PGMQ extension installed successfully")
    except Exception as e:
        print(f"⚠ PGMQ extension not available (optional): {e}")

    try:
        op.execute('CREATE EXTENSION IF NOT EXISTS pg_cron')  # Scheduled tasks (PM generation, KPIs)
        print("✓ pg_cron extension installed successfully")
    except Exception as e:
        print(f"⚠ pg_cron extension not available (optional): {e}")

    # Note: pg_search (ParadeDB) and pg_duckdb require separate installation
    # These extensions provide advanced full-text search (BM25) and OLAP analytics
    # For now, we'll use standard PostgreSQL features (pg_trgm for search)
    # Uncomment when ParadeDB is available:
    # try:
    #     op.execute('CREATE EXTENSION IF NOT EXISTS pg_search')  # BM25 full-text search
    #     print("✓ pg_search extension installed successfully")
    # except Exception as e:
    #     print(f"⚠ pg_search extension not available (optional): {e}")
    #
    # try:
    #     op.execute('CREATE EXTENSION IF NOT EXISTS pg_duckdb')  # Analytics engine
    #     print("✓ pg_duckdb extension installed successfully")
    # except Exception as e:
    #     print(f"⚠ pg_duckdb extension not available (optional): {e}")

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

    # Machine Status History - 1 week chunks
    op.execute("""
        SELECT create_hypertable('machine_status_history', 'start_timestamp',
            chunk_time_interval => INTERVAL '1 week',
            if_not_exists => TRUE
        );
    """)

    # ========================================================================
    # TimescaleDB Compression Policies
    # Enable compression for time-series data (75% space savings)
    # ========================================================================

    # Compress production logs after 7 days
    op.execute("""
        ALTER TABLE production_logs SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'organization_id, work_order_id'
        );
        SELECT add_compression_policy('production_logs', INTERVAL '7 days');
    """)

    # Compress inspection measurements after 7 days
    op.execute("""
        ALTER TABLE inspection_measurements SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'organization_id, inspection_point_id'
        );
        SELECT add_compression_policy('inspection_measurements', INTERVAL '7 days');
    """)

    # ========================================================================
    # UNLOGGED Cache Table (PostgreSQL-Native Caching)
    # Replaces Redis with PostgreSQL UNLOGGED table (2x faster writes, 1-2ms latency)
    # ========================================================================
    op.execute("""
        CREATE UNLOGGED TABLE IF NOT EXISTS cache (
            cache_key VARCHAR(255) PRIMARY KEY,
            cache_value JSONB NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Index for expiration cleanup
        CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache(expires_at);

        -- Function to cleanup expired cache entries
        CREATE OR REPLACE FUNCTION cleanup_expired_cache()
        RETURNS INTEGER AS $$
        DECLARE
            deleted_count INTEGER;
        BEGIN
            DELETE FROM cache WHERE expires_at < NOW();
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            RETURN deleted_count;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # ========================================================================
    # Database Triggers for Automation
    # ========================================================================

    # Trigger: Low stock alert via LISTEN/NOTIFY
    op.execute("""
        CREATE OR REPLACE FUNCTION notify_low_stock()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.quantity_on_hand < NEW.reorder_point AND NEW.reorder_point IS NOT NULL THEN
                PERFORM pg_notify(
                    'low_stock_alert',
                    json_build_object(
                        'material_id', NEW.id,
                        'material_code', NEW.material_code,
                        'quantity', NEW.quantity_on_hand,
                        'reorder_point', NEW.reorder_point,
                        'organization_id', NEW.organization_id,
                        'plant_id', NEW.plant_id
                    )::text
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS tr_low_stock_alert ON materials;
        CREATE TRIGGER tr_low_stock_alert
        AFTER INSERT OR UPDATE OF quantity_on_hand ON materials
        FOR EACH ROW
        EXECUTE FUNCTION notify_low_stock();
    """)

    # Trigger: Work order status change notification
    op.execute("""
        CREATE OR REPLACE FUNCTION notify_work_order_status_change()
        RETURNS TRIGGER AS $$
        BEGIN
            IF OLD.order_status IS DISTINCT FROM NEW.order_status THEN
                PERFORM pg_notify(
                    'work_order_status_changed',
                    json_build_object(
                        'work_order_id', NEW.id,
                        'work_order_number', NEW.work_order_number,
                        'old_status', OLD.order_status,
                        'new_status', NEW.order_status,
                        'organization_id', NEW.organization_id,
                        'plant_id', NEW.plant_id
                    )::text
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS tr_work_order_status_notification ON work_orders;
        CREATE TRIGGER tr_work_order_status_notification
        AFTER UPDATE OF order_status ON work_orders
        FOR EACH ROW
        EXECUTE FUNCTION notify_work_order_status_change();
    """)

    # Trigger: NCR creation notification (for critical/major NCRs)
    op.execute("""
        CREATE OR REPLACE FUNCTION notify_ncr_creation()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.severity IN ('critical', 'major') THEN
                PERFORM pg_notify(
                    'ncr_created',
                    json_build_object(
                        'ncr_id', NEW.id,
                        'ncr_number', NEW.ncr_number,
                        'severity', NEW.severity,
                        'defect_type', NEW.defect_type,
                        'organization_id', NEW.organization_id,
                        'plant_id', NEW.plant_id
                    )::text
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS tr_ncr_creation_notification ON ncrs;
        CREATE TRIGGER tr_ncr_creation_notification
        AFTER INSERT ON ncrs
        FOR EACH ROW
        EXECUTE FUNCTION notify_ncr_creation();
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
