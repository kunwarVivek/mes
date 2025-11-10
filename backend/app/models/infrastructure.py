"""
Infrastructure models - Audit logs, Notifications, System Settings, File Uploads, SAP Integration
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, BigInteger, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from enum import Enum
from typing import Optional, Dict, List, Any
from datetime import datetime


# Enums
class AuditAction(str, Enum):
    """Audit log action types"""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    SYSTEM = "SYSTEM"


class Severity(str, Enum):
    """Severity levels for logs and notifications"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class DeliveryChannel(str, Enum):
    """Notification delivery channels"""
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"


class SettingType(str, Enum):
    """System setting value types"""
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"
    DATE = "DATE"
    DATETIME = "DATETIME"
    TIME = "TIME"


class StorageProvider(str, Enum):
    """File storage providers"""
    LOCAL = "LOCAL"
    MINIO = "MINIO"
    S3 = "S3"
    AZURE = "AZURE"
    GCS = "GCS"


class SyncDirection(str, Enum):
    """SAP sync direction"""
    TO_SAP = "TO_SAP"
    FROM_SAP = "FROM_SAP"
    BIDIRECTIONAL = "BIDIRECTIONAL"


class SyncStatus(str, Enum):
    """SAP sync status"""
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    SKIPPED = "SKIPPED"


class AuditLog(Base):
    """
    Audit Log model - TimescaleDB hypertable.

    Comprehensive audit trail for all system actions.
    Tracks user actions, data changes, security events, and system operations.
    """
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, primary_key=True)

    # Entity information
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=True)
    entity_identifier = Column(String(200), nullable=True)

    # Action information
    action = Column(String(50), nullable=False)
    action_category = Column(String(50), nullable=True)

    # User information
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    user_name = Column(String(200), nullable=True)
    user_email = Column(String(255), nullable=True)

    # Request information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)

    # Changes
    changes_before = Column(JSONB, nullable=True)
    changes_after = Column(JSONB, nullable=True)
    changes_diff = Column(JSONB, nullable=True)

    # Additional metadata
    metadata = Column(JSONB, nullable=True)
    severity = Column(String(20), nullable=False, default='INFO')
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)

    # Table constraints
    __table_args__ = (
        Index('idx_audit_logs_org_timestamp', 'organization_id', 'timestamp'),
        Index('idx_audit_logs_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_logs_user', 'user_id', 'timestamp'),
        Index('idx_audit_logs_action', 'action', 'timestamp'),
        CheckConstraint(
            "action IN ('CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'APPROVE', 'REJECT', 'EXPORT', 'IMPORT', 'SYSTEM')",
            name='chk_audit_logs_action_valid'
        ),
        CheckConstraint(
            "severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')",
            name='chk_audit_logs_severity_valid'
        ),
        {'postgresql_rls': True}
    )


class Notification(Base):
    """
    Notification model.

    In-app notifications for users with support for multiple delivery channels.
    Includes priority levels, read tracking, and scheduling capabilities.
    """
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)

    # Recipient information
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=True)

    # Notification content
    notification_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String(500), nullable=True)
    action_label = Column(String(100), nullable=True)

    # Reference to source entity
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(Integer, nullable=True)

    # Priority and delivery
    priority = Column(String(20), nullable=False, default='NORMAL')
    delivery_channels = Column(ARRAY(String(50)), nullable=False, default=['IN_APP'])

    # Status tracking
    is_read = Column(Boolean, nullable=False, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    is_archived = Column(Boolean, nullable=False, default=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    # Scheduling
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    metadata = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Table constraints
    __table_args__ = (
        Index('idx_notifications_user', 'user_id', 'is_read', 'created_at'),
        Index('idx_notifications_org', 'organization_id', 'created_at'),
        Index('idx_notifications_entity', 'entity_type', 'entity_id'),
        Index('idx_notifications_scheduled', 'scheduled_for'),
        CheckConstraint(
            "priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')",
            name='chk_notifications_priority_valid'
        ),
        {'postgresql_rls': True}
    )

    def mark_as_read(self) -> None:
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.now()

    def archive(self) -> None:
        """Archive notification"""
        self.is_archived = True
        self.archived_at = datetime.now()

    def is_scheduled(self) -> bool:
        """Check if notification is scheduled for future"""
        if not self.scheduled_for:
            return False
        return self.scheduled_for > datetime.now()

    def is_expired(self) -> bool:
        """Check if notification has expired"""
        if not self.expires_at:
            return False
        return self.expires_at < datetime.now()


class SystemSetting(Base):
    """
    System Setting model.

    Configurable system settings per organization.
    Supports different value types, validation, and UI component hints.
    """
    __tablename__ = 'system_settings'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)

    # Setting identification
    setting_category = Column(String(100), nullable=False)
    setting_key = Column(String(200), nullable=False)
    setting_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Value and metadata
    setting_value = Column(Text, nullable=True)
    setting_type = Column(String(50), nullable=False, default='STRING')
    default_value = Column(Text, nullable=True)
    validation_rules = Column(JSONB, nullable=True)

    # Settings metadata
    is_encrypted = Column(Boolean, nullable=False, default=False)
    is_system_setting = Column(Boolean, nullable=False, default=False)
    is_editable = Column(Boolean, nullable=False, default=True)
    requires_restart = Column(Boolean, nullable=False, default=False)

    # Grouping and display
    display_order = Column(Integer, nullable=False, default=0)
    ui_component = Column(String(50), nullable=True)
    options = Column(JSONB, nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Table constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'setting_key', name='uq_setting_key_per_org'),
        Index('idx_system_settings_org', 'organization_id'),
        Index('idx_system_settings_category', 'setting_category', 'display_order'),
        CheckConstraint(
            "setting_type IN ('STRING', 'NUMBER', 'BOOLEAN', 'JSON', 'DATE', 'DATETIME', 'TIME')",
            name='chk_system_settings_type_valid'
        ),
        {'postgresql_rls': True}
    )

    def get_typed_value(self) -> Any:
        """Get setting value with appropriate type conversion"""
        if self.setting_value is None:
            return None

        if self.setting_type == 'NUMBER':
            try:
                return float(self.setting_value)
            except ValueError:
                return None
        elif self.setting_type == 'BOOLEAN':
            return self.setting_value.lower() in ('true', '1', 'yes')
        elif self.setting_type == 'JSON':
            import json
            try:
                return json.loads(self.setting_value)
            except json.JSONDecodeError:
                return None
        else:
            return self.setting_value


class FileUpload(Base):
    """
    File Upload model.

    Tracks all uploaded files with storage provider support.
    Includes file metadata, virus scanning, and access control.
    """
    __tablename__ = 'file_uploads'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)

    # File information
    file_name = Column(String(500), nullable=False)
    original_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(200), nullable=True)
    file_extension = Column(String(50), nullable=True)

    # File hash for deduplication and integrity
    file_hash = Column(String(64), nullable=True)

    # Storage information
    storage_provider = Column(String(50), nullable=False, default='LOCAL')
    storage_bucket = Column(String(200), nullable=True)
    storage_key = Column(String(1000), nullable=True)

    # Reference to entity
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(Integer, nullable=True)
    entity_field = Column(String(100), nullable=True)

    # File metadata
    description = Column(Text, nullable=True)
    tags = Column(ARRAY(String(100)), nullable=True)
    metadata = Column(JSONB, nullable=True)

    # Access control
    is_public = Column(Boolean, nullable=False, default=False)
    access_url = Column(String(1000), nullable=True)
    access_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Virus scanning
    is_scanned = Column(Boolean, nullable=False, default=False)
    scan_result = Column(String(50), nullable=True)
    scan_date = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Table constraints
    __table_args__ = (
        Index('idx_file_uploads_org', 'organization_id', 'created_at'),
        Index('idx_file_uploads_entity', 'entity_type', 'entity_id'),
        Index('idx_file_uploads_hash', 'file_hash'),
        Index('idx_file_uploads_created_by', 'created_by'),
        CheckConstraint(
            "storage_provider IN ('LOCAL', 'MINIO', 'S3', 'AZURE', 'GCS')",
            name='chk_file_uploads_provider_valid'
        ),
        {'postgresql_rls': True}
    )

    def get_size_mb(self) -> float:
        """Get file size in megabytes"""
        return self.file_size / (1024 * 1024)

    def is_access_expired(self) -> bool:
        """Check if access URL has expired"""
        if not self.access_expires_at:
            return False
        return self.access_expires_at < datetime.now()


class SAPSyncLog(Base):
    """
    SAP Sync Log model - TimescaleDB hypertable.

    Logs all SAP integration sync operations.
    Tracks sync direction, status, payload, and performance metrics.
    """
    __tablename__ = 'sap_sync_logs'

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, primary_key=True)

    # Sync operation
    sync_direction = Column(String(20), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=True)
    entity_identifier = Column(String(200), nullable=True)

    # SAP identifiers
    sap_object_type = Column(String(100), nullable=True)
    sap_object_key = Column(String(100), nullable=True)

    # Sync details
    operation = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    attempt_number = Column(Integer, nullable=False, default=1)

    # Request/Response
    request_payload = Column(JSONB, nullable=True)
    response_payload = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Batch information
    batch_id = Column(String(100), nullable=True)
    batch_size = Column(Integer, nullable=True)
    batch_sequence = Column(Integer, nullable=True)

    # Metadata
    metadata = Column(JSONB, nullable=True)
    triggered_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Table constraints
    __table_args__ = (
        Index('idx_sap_sync_logs_org_timestamp', 'organization_id', 'timestamp'),
        Index('idx_sap_sync_logs_entity', 'entity_type', 'entity_id'),
        Index('idx_sap_sync_logs_status', 'status', 'timestamp'),
        Index('idx_sap_sync_logs_batch', 'batch_id'),
        CheckConstraint(
            "sync_direction IN ('TO_SAP', 'FROM_SAP', 'BIDIRECTIONAL')",
            name='chk_sap_sync_logs_direction_valid'
        ),
        CheckConstraint(
            "status IN ('PENDING', 'SUCCESS', 'FAILED', 'PARTIAL', 'SKIPPED')",
            name='chk_sap_sync_logs_status_valid'
        ),
        {'postgresql_rls': True}
    )


class SAPMapping(Base):
    """
    SAP Mapping model.

    Maps MES entities to SAP objects.
    Supports field-level mappings and transformation rules.
    """
    __tablename__ = 'sap_mappings'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)

    # MES Entity
    mes_entity_type = Column(String(100), nullable=False)
    mes_entity_id = Column(Integer, nullable=False)
    mes_entity_identifier = Column(String(200), nullable=True)

    # SAP Entity
    sap_object_type = Column(String(100), nullable=False)
    sap_object_key = Column(String(100), nullable=False)
    sap_system_id = Column(String(50), nullable=True)

    # Mapping metadata
    mapping_direction = Column(String(20), nullable=False, default='BIDIRECTIONAL')
    field_mappings = Column(JSONB, nullable=True)
    transformation_rules = Column(JSONB, nullable=True)

    # Sync settings
    is_active = Column(Boolean, nullable=False, default=True)
    auto_sync = Column(Boolean, nullable=False, default=False)
    sync_frequency_minutes = Column(Integer, nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_status = Column(String(50), nullable=True)

    # Metadata
    metadata = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    updated_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Table constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'mes_entity_type', 'mes_entity_id', name='uq_sap_mapping_per_entity'),
        Index('idx_sap_mappings_org', 'organization_id'),
        Index('idx_sap_mappings_mes_entity', 'mes_entity_type', 'mes_entity_id'),
        Index('idx_sap_mappings_sap_object', 'sap_object_type', 'sap_object_key'),
        CheckConstraint(
            "mapping_direction IN ('TO_SAP', 'FROM_SAP', 'BIDIRECTIONAL')",
            name='chk_sap_mappings_direction_valid'
        ),
        {'postgresql_rls': True}
    )

    def is_sync_due(self) -> bool:
        """Check if sync is due based on frequency"""
        if not self.auto_sync or not self.sync_frequency_minutes:
            return False

        if not self.last_synced_at:
            return True

        from datetime import timedelta
        next_sync = self.last_synced_at + timedelta(minutes=self.sync_frequency_minutes)
        return datetime.now() >= next_sync
