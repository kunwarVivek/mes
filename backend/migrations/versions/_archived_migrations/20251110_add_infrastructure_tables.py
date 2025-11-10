"""Add infrastructure tables (audit_logs, notifications, system_settings, file_uploads, SAP sync)

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2025-11-10 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'g7h8i9j0k1l2'
down_revision = 'f6g7h8i9j0k1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create audit_logs table (TimescaleDB hypertable)
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        # Entity information
        sa.Column('entity_type', sa.String(length=100), nullable=False),  # TABLE_NAME
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('entity_identifier', sa.String(length=200), nullable=True),  # Human-readable ID

        # Action information
        sa.Column('action', sa.String(length=50), nullable=False),  # CREATE, UPDATE, DELETE, LOGIN, etc.
        sa.Column('action_category', sa.String(length=50), nullable=True),  # AUTHENTICATION, DATA_CHANGE, SECURITY, etc.

        # User information
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_name', sa.String(length=200), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),

        # Request information
        sa.Column('ip_address', sa.String(length=45), nullable=True),  # IPv6 compatible
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),

        # Changes
        sa.Column('changes_before', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('changes_after', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('changes_diff', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Additional metadata
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='INFO'),  # INFO, WARNING, ERROR, CRITICAL
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),

        sa.PrimaryKeyConstraint('id', 'timestamp'),  # Composite key for TimescaleDB
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.Index('idx_audit_logs_org_timestamp', 'organization_id', 'timestamp'),
        sa.Index('idx_audit_logs_entity', 'entity_type', 'entity_id'),
        sa.Index('idx_audit_logs_user', 'user_id', 'timestamp'),
        sa.Index('idx_audit_logs_action', 'action', 'timestamp'),
        sa.CheckConstraint(
            "action IN ('CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'APPROVE', 'REJECT', 'EXPORT', 'IMPORT', 'SYSTEM')",
            name='chk_audit_logs_action_valid'
        ),
        sa.CheckConstraint(
            "severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')",
            name='chk_audit_logs_severity_valid'
        ),
    )

    # Convert to TimescaleDB hypertable (6 month chunks)
    op.execute("""
        SELECT create_hypertable('audit_logs', 'timestamp',
            chunk_time_interval => INTERVAL '6 months',
            if_not_exists => TRUE
        );
    """)

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Recipient information
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=True),  # For role-based notifications

        # Notification content
        sa.Column('notification_type', sa.String(length=50), nullable=False),  # INFO, WARNING, ERROR, SUCCESS, NCR, APPROVAL, etc.
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('action_url', sa.String(length=500), nullable=True),  # Deep link
        sa.Column('action_label', sa.String(length=100), nullable=True),  # Button text

        # Reference to source entity
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),

        # Priority and delivery
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='NORMAL'),  # LOW, NORMAL, HIGH, URGENT
        sa.Column('delivery_channels', postgresql.ARRAY(sa.String(50)), nullable=False, server_default='{IN_APP}'),  # IN_APP, EMAIL, SMS, PUSH

        # Status tracking
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),

        # Scheduling
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),  # For scheduled notifications
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),  # Auto-archive after this

        # Metadata
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.Index('idx_notifications_user', 'user_id', 'is_read', 'created_at'),
        sa.Index('idx_notifications_org', 'organization_id', 'created_at'),
        sa.Index('idx_notifications_entity', 'entity_type', 'entity_id'),
        sa.Index('idx_notifications_scheduled', 'scheduled_for'),
        sa.CheckConstraint(
            "priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')",
            name='chk_notifications_priority_valid'
        ),
    )

    # Create system_settings table
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Setting identification
        sa.Column('setting_category', sa.String(length=100), nullable=False),  # GENERAL, SECURITY, PRODUCTION, QUALITY, etc.
        sa.Column('setting_key', sa.String(length=200), nullable=False),
        sa.Column('setting_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Value and metadata
        sa.Column('setting_value', sa.Text(), nullable=True),  # String representation
        sa.Column('setting_type', sa.String(length=50), nullable=False, server_default='STRING'),  # STRING, NUMBER, BOOLEAN, JSON, DATE
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('validation_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # Min, max, regex, etc.

        # Settings metadata
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_system_setting', sa.Boolean(), nullable=False, server_default='false'),  # Can't be deleted
        sa.Column('is_editable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('requires_restart', sa.Boolean(), nullable=False, server_default='false'),

        # Grouping and display
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ui_component', sa.String(length=50), nullable=True),  # TEXT, NUMBER, SWITCH, SELECT, etc.
        sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # For SELECT components

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'setting_key', name='uq_setting_key_per_org'),
        sa.Index('idx_system_settings_org', 'organization_id'),
        sa.Index('idx_system_settings_category', 'setting_category', 'display_order'),
        sa.CheckConstraint(
            "setting_type IN ('STRING', 'NUMBER', 'BOOLEAN', 'JSON', 'DATE', 'DATETIME', 'TIME')",
            name='chk_system_settings_type_valid'
        ),
    )

    # Create file_uploads table
    op.create_table(
        'file_uploads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # File information
        sa.Column('file_name', sa.String(length=500), nullable=False),
        sa.Column('original_name', sa.String(length=500), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),  # Storage path
        sa.Column('file_size', sa.BigInteger(), nullable=False),  # Bytes
        sa.Column('mime_type', sa.String(length=200), nullable=True),
        sa.Column('file_extension', sa.String(length=50), nullable=True),

        # File hash for deduplication and integrity
        sa.Column('file_hash', sa.String(length=64), nullable=True),  # SHA-256

        # Storage information
        sa.Column('storage_provider', sa.String(length=50), nullable=False, server_default='LOCAL'),  # LOCAL, MINIO, S3, AZURE
        sa.Column('storage_bucket', sa.String(length=200), nullable=True),
        sa.Column('storage_key', sa.String(length=1000), nullable=True),

        # Reference to entity
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('entity_field', sa.String(length=100), nullable=True),  # Which field this file belongs to

        # File metadata
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String(100)), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Access control
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('access_url', sa.String(length=1000), nullable=True),  # Pre-signed URL
        sa.Column('access_expires_at', sa.DateTime(timezone=True), nullable=True),

        # Virus scanning
        sa.Column('is_scanned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('scan_result', sa.String(length=50), nullable=True),  # CLEAN, INFECTED, SUSPICIOUS
        sa.Column('scan_date', sa.DateTime(timezone=True), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.Index('idx_file_uploads_org', 'organization_id', 'created_at'),
        sa.Index('idx_file_uploads_entity', 'entity_type', 'entity_id'),
        sa.Index('idx_file_uploads_hash', 'file_hash'),
        sa.Index('idx_file_uploads_created_by', 'created_by'),
        sa.CheckConstraint(
            "storage_provider IN ('LOCAL', 'MINIO', 'S3', 'AZURE', 'GCS')",
            name='chk_file_uploads_provider_valid'
        ),
    )

    # Create sap_sync_logs table (TimescaleDB hypertable)
    op.create_table(
        'sap_sync_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        # Sync operation
        sa.Column('sync_direction', sa.String(length=20), nullable=False),  # TO_SAP, FROM_SAP, BIDIRECTIONAL
        sa.Column('entity_type', sa.String(length=100), nullable=False),  # WORK_ORDER, MATERIAL, BOM, etc.
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('entity_identifier', sa.String(length=200), nullable=True),

        # SAP identifiers
        sa.Column('sap_object_type', sa.String(length=100), nullable=True),  # AUFK, MARA, STPO, etc.
        sa.Column('sap_object_key', sa.String(length=100), nullable=True),

        # Sync details
        sa.Column('operation', sa.String(length=50), nullable=False),  # CREATE, UPDATE, DELETE, SYNC
        sa.Column('status', sa.String(length=50), nullable=False),  # PENDING, SUCCESS, FAILED, PARTIAL
        sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'),

        # Request/Response
        sa.Column('request_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('response_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),

        # Timing
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),

        # Batch information
        sa.Column('batch_id', sa.String(length=100), nullable=True),
        sa.Column('batch_size', sa.Integer(), nullable=True),
        sa.Column('batch_sequence', sa.Integer(), nullable=True),

        # Metadata
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('triggered_by', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id', 'timestamp'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['triggered_by'], ['users.id'], ondelete='SET NULL'),
        sa.Index('idx_sap_sync_logs_org_timestamp', 'organization_id', 'timestamp'),
        sa.Index('idx_sap_sync_logs_entity', 'entity_type', 'entity_id'),
        sa.Index('idx_sap_sync_logs_status', 'status', 'timestamp'),
        sa.Index('idx_sap_sync_logs_batch', 'batch_id'),
        sa.CheckConstraint(
            "sync_direction IN ('TO_SAP', 'FROM_SAP', 'BIDIRECTIONAL')",
            name='chk_sap_sync_logs_direction_valid'
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'SUCCESS', 'FAILED', 'PARTIAL', 'SKIPPED')",
            name='chk_sap_sync_logs_status_valid'
        ),
    )

    # Convert to TimescaleDB hypertable (1 month chunks)
    op.execute("""
        SELECT create_hypertable('sap_sync_logs', 'timestamp',
            chunk_time_interval => INTERVAL '1 month',
            if_not_exists => TRUE
        );
    """)

    # Create sap_mappings table
    op.create_table(
        'sap_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # MES Entity
        sa.Column('mes_entity_type', sa.String(length=100), nullable=False),
        sa.Column('mes_entity_id', sa.Integer(), nullable=False),
        sa.Column('mes_entity_identifier', sa.String(length=200), nullable=True),

        # SAP Entity
        sa.Column('sap_object_type', sa.String(length=100), nullable=False),
        sa.Column('sap_object_key', sa.String(length=100), nullable=False),
        sa.Column('sap_system_id', sa.String(length=50), nullable=True),  # For multi-SAP environments

        # Mapping metadata
        sa.Column('mapping_direction', sa.String(length=20), nullable=False, server_default='BIDIRECTIONAL'),
        sa.Column('field_mappings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # Field-level mappings
        sa.Column('transformation_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Sync settings
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auto_sync', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sync_frequency_minutes', sa.Integer(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_status', sa.String(length=50), nullable=True),

        # Metadata
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'mes_entity_type', 'mes_entity_id', name='uq_sap_mapping_per_entity'),
        sa.Index('idx_sap_mappings_org', 'organization_id'),
        sa.Index('idx_sap_mappings_mes_entity', 'mes_entity_type', 'mes_entity_id'),
        sa.Index('idx_sap_mappings_sap_object', 'sap_object_type', 'sap_object_key'),
        sa.CheckConstraint(
            "mapping_direction IN ('TO_SAP', 'FROM_SAP', 'BIDIRECTIONAL')",
            name='chk_sap_mappings_direction_valid'
        ),
    )

    # Enable RLS on all tables
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE notifications ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE file_uploads ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE sap_sync_logs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE sap_mappings ENABLE ROW LEVEL SECURITY")

    # Create RLS policies
    op.execute("""
        CREATE POLICY audit_logs_org_isolation ON audit_logs
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY notifications_org_isolation ON notifications
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY system_settings_org_isolation ON system_settings
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY file_uploads_org_isolation ON file_uploads
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY sap_sync_logs_org_isolation ON sap_sync_logs
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY sap_mappings_org_isolation ON sap_mappings
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS audit_logs_org_isolation ON audit_logs")
    op.execute("DROP POLICY IF EXISTS notifications_org_isolation ON notifications")
    op.execute("DROP POLICY IF EXISTS system_settings_org_isolation ON system_settings")
    op.execute("DROP POLICY IF EXISTS file_uploads_org_isolation ON file_uploads")
    op.execute("DROP POLICY IF EXISTS sap_sync_logs_org_isolation ON sap_sync_logs")
    op.execute("DROP POLICY IF EXISTS sap_mappings_org_isolation ON sap_mappings")

    # Drop tables
    op.drop_table('sap_mappings')
    op.drop_table('sap_sync_logs')
    op.drop_table('file_uploads')
    op.drop_table('system_settings')
    op.drop_table('notifications')
    op.drop_table('audit_logs')
