"""
DTOs for Infrastructure (Audit Logs, Notifications, System Settings, File Uploads, SAP Integration)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
from datetime import datetime

# ========== Audit Log DTOs ==========

class AuditLogCreateDTO(BaseModel):
    """DTO for creating an audit log entry"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    entity_type: str = Field(..., min_length=1, max_length=100, description="Entity type (table name)")
    entity_id: Optional[int] = Field(None, description="Entity ID")
    entity_identifier: Optional[str] = Field(None, max_length=200, description="Human-readable identifier")
    action: str = Field(..., description="Action performed")
    action_category: Optional[str] = Field(None, max_length=50, description="Action category")
    user_id: Optional[int] = Field(None, description="User ID")
    user_name: Optional[str] = Field(None, max_length=200, description="User name")
    user_email: Optional[str] = Field(None, max_length=255, description="User email")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    request_id: Optional[str] = Field(None, max_length=100, description="Request ID for tracing")
    changes_before: Optional[Dict[str, Any]] = Field(None, description="State before change")
    changes_after: Optional[Dict[str, Any]] = Field(None, description="State after change")
    changes_diff: Optional[Dict[str, Any]] = Field(None, description="Diff of changes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    severity: str = Field(default='INFO', description="Severity level")
    success: bool = Field(default=True, description="Whether action succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        valid_actions = ['CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'APPROVE', 'REJECT', 'EXPORT', 'IMPORT', 'SYSTEM']
        if v not in valid_actions:
            raise ValueError(f'action must be one of {valid_actions}')
        return v

    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        valid_severities = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v not in valid_severities:
            raise ValueError(f'severity must be one of {valid_severities}')
        return v


class AuditLogResponse(BaseModel):
    """DTO for audit log response"""
    id: int
    organization_id: int
    timestamp: datetime
    entity_type: str
    entity_id: Optional[int]
    entity_identifier: Optional[str]
    action: str
    action_category: Optional[str]
    user_id: Optional[int]
    user_name: Optional[str]
    user_email: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    changes_before: Optional[Dict[str, Any]]
    changes_after: Optional[Dict[str, Any]]
    changes_diff: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    severity: str
    success: bool
    error_message: Optional[str]

    class Config:
        from_attributes = True


# ========== Notification DTOs ==========

class NotificationCreateDTO(BaseModel):
    """DTO for creating a notification"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    user_id: int = Field(..., gt=0, description="Recipient user ID")
    role_id: Optional[int] = Field(None, gt=0, description="Recipient role ID")
    notification_type: str = Field(..., min_length=1, max_length=50, description="Notification type")
    title: str = Field(..., min_length=1, max_length=200, description="Notification title")
    message: str = Field(..., min_length=1, description="Notification message")
    action_url: Optional[str] = Field(None, max_length=500, description="Action URL (deep link)")
    action_label: Optional[str] = Field(None, max_length=100, description="Action button label")
    entity_type: Optional[str] = Field(None, max_length=100, description="Source entity type")
    entity_id: Optional[int] = Field(None, description="Source entity ID")
    priority: str = Field(default='NORMAL', description="Priority level")
    delivery_channels: List[str] = Field(default=['IN_APP'], description="Delivery channels")
    scheduled_for: Optional[datetime] = Field(None, description="Schedule for future")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_by: Optional[int] = Field(None, description="Created by user ID")

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        valid_priorities = ['LOW', 'NORMAL', 'HIGH', 'URGENT']
        if v not in valid_priorities:
            raise ValueError(f'priority must be one of {valid_priorities}')
        return v


class NotificationUpdateDTO(BaseModel):
    """DTO for updating a notification"""
    is_read: Optional[bool] = None
    is_archived: Optional[bool] = None


class NotificationResponse(BaseModel):
    """DTO for notification response"""
    id: int
    organization_id: int
    user_id: int
    role_id: Optional[int]
    notification_type: str
    title: str
    message: str
    action_url: Optional[str]
    action_label: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[int]
    priority: str
    delivery_channels: List[str]
    is_read: bool
    read_at: Optional[datetime]
    is_archived: bool
    archived_at: Optional[datetime]
    scheduled_for: Optional[datetime]
    expires_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    created_by: Optional[int]

    class Config:
        from_attributes = True


# ========== System Setting DTOs ==========

class SystemSettingCreateDTO(BaseModel):
    """DTO for creating a system setting"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    setting_category: str = Field(..., min_length=1, max_length=100, description="Setting category")
    setting_key: str = Field(..., min_length=1, max_length=200, description="Setting key")
    setting_name: str = Field(..., min_length=1, max_length=200, description="Setting name")
    description: Optional[str] = Field(None, description="Description")
    setting_value: Optional[str] = Field(None, description="Setting value")
    setting_type: str = Field(default='STRING', description="Value type")
    default_value: Optional[str] = Field(None, description="Default value")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    is_encrypted: bool = Field(default=False, description="Is value encrypted")
    is_system_setting: bool = Field(default=False, description="Is system setting (can't be deleted)")
    is_editable: bool = Field(default=True, description="Is editable by users")
    requires_restart: bool = Field(default=False, description="Requires restart after change")
    display_order: int = Field(default=0, description="Display order")
    ui_component: Optional[str] = Field(None, max_length=50, description="UI component type")
    options: Optional[Dict[str, Any]] = Field(None, description="Options for select components")

    @field_validator('setting_type')
    @classmethod
    def validate_setting_type(cls, v):
        valid_types = ['STRING', 'NUMBER', 'BOOLEAN', 'JSON', 'DATE', 'DATETIME', 'TIME']
        if v not in valid_types:
            raise ValueError(f'setting_type must be one of {valid_types}')
        return v


class SystemSettingUpdateDTO(BaseModel):
    """DTO for updating a system setting"""
    setting_value: Optional[str] = None
    setting_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    default_value: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    is_editable: Optional[bool] = None
    requires_restart: Optional[bool] = None
    display_order: Optional[int] = None
    ui_component: Optional[str] = Field(None, max_length=50)
    options: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class SystemSettingResponse(BaseModel):
    """DTO for system setting response"""
    id: int
    organization_id: int
    setting_category: str
    setting_key: str
    setting_name: str
    description: Optional[str]
    setting_value: Optional[str]
    setting_type: str
    default_value: Optional[str]
    validation_rules: Optional[Dict[str, Any]]
    is_encrypted: bool
    is_system_setting: bool
    is_editable: bool
    requires_restart: bool
    display_order: int
    ui_component: Optional[str]
    options: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]

    class Config:
        from_attributes = True


# ========== File Upload DTOs ==========

class FileUploadCreateDTO(BaseModel):
    """DTO for creating a file upload record"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    file_name: str = Field(..., min_length=1, max_length=500, description="Stored file name")
    original_name: str = Field(..., min_length=1, max_length=500, description="Original file name")
    file_path: str = Field(..., min_length=1, max_length=1000, description="File storage path")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    mime_type: Optional[str] = Field(None, max_length=200, description="MIME type")
    file_extension: Optional[str] = Field(None, max_length=50, description="File extension")
    file_hash: Optional[str] = Field(None, max_length=64, description="SHA-256 hash")
    storage_provider: str = Field(default='LOCAL', description="Storage provider")
    storage_bucket: Optional[str] = Field(None, max_length=200, description="Storage bucket")
    storage_key: Optional[str] = Field(None, max_length=1000, description="Storage key")
    entity_type: Optional[str] = Field(None, max_length=100, description="Entity type")
    entity_id: Optional[int] = Field(None, description="Entity ID")
    entity_field: Optional[str] = Field(None, max_length=100, description="Entity field")
    description: Optional[str] = Field(None, description="Description")
    tags: Optional[List[str]] = Field(None, description="Tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    is_public: bool = Field(default=False, description="Is public")
    created_by: int = Field(..., gt=0, description="Created by user ID")

    @field_validator('storage_provider')
    @classmethod
    def validate_storage_provider(cls, v):
        valid_providers = ['LOCAL', 'MINIO', 'S3', 'AZURE', 'GCS']
        if v not in valid_providers:
            raise ValueError(f'storage_provider must be one of {valid_providers}')
        return v


class FileUploadUpdateDTO(BaseModel):
    """DTO for updating a file upload record"""
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    access_url: Optional[str] = Field(None, max_length=1000)
    access_expires_at: Optional[datetime] = None
    is_scanned: Optional[bool] = None
    scan_result: Optional[str] = Field(None, max_length=50)
    scan_date: Optional[datetime] = None


class FileUploadResponse(BaseModel):
    """DTO for file upload response"""
    id: int
    organization_id: int
    file_name: str
    original_name: str
    file_path: str
    file_size: int
    mime_type: Optional[str]
    file_extension: Optional[str]
    file_hash: Optional[str]
    storage_provider: str
    storage_bucket: Optional[str]
    storage_key: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[int]
    entity_field: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]
    is_public: bool
    access_url: Optional[str]
    access_expires_at: Optional[datetime]
    is_scanned: bool
    scan_result: Optional[str]
    scan_date: Optional[datetime]
    is_active: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    created_by: int

    class Config:
        from_attributes = True


# ========== SAP Sync Log DTOs ==========

class SAPSyncLogCreateDTO(BaseModel):
    """DTO for creating a SAP sync log entry"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    sync_direction: str = Field(..., description="Sync direction")
    entity_type: str = Field(..., min_length=1, max_length=100, description="Entity type")
    entity_id: Optional[int] = Field(None, description="Entity ID")
    entity_identifier: Optional[str] = Field(None, max_length=200, description="Entity identifier")
    sap_object_type: Optional[str] = Field(None, max_length=100, description="SAP object type")
    sap_object_key: Optional[str] = Field(None, max_length=100, description="SAP object key")
    operation: str = Field(..., min_length=1, max_length=50, description="Operation")
    status: str = Field(..., description="Sync status")
    attempt_number: int = Field(default=1, ge=1, description="Attempt number")
    request_payload: Optional[Dict[str, Any]] = Field(None, description="Request payload")
    response_payload: Optional[Dict[str, Any]] = Field(None, description="Response payload")
    error_message: Optional[str] = Field(None, description="Error message")
    error_code: Optional[str] = Field(None, max_length=50, description="Error code")
    started_at: Optional[datetime] = Field(None, description="Started at")
    completed_at: Optional[datetime] = Field(None, description="Completed at")
    duration_ms: Optional[int] = Field(None, ge=0, description="Duration in milliseconds")
    batch_id: Optional[str] = Field(None, max_length=100, description="Batch ID")
    batch_size: Optional[int] = Field(None, gt=0, description="Batch size")
    batch_sequence: Optional[int] = Field(None, ge=0, description="Batch sequence")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    triggered_by: Optional[int] = Field(None, description="Triggered by user ID")

    @field_validator('sync_direction')
    @classmethod
    def validate_sync_direction(cls, v):
        valid_directions = ['TO_SAP', 'FROM_SAP', 'BIDIRECTIONAL']
        if v not in valid_directions:
            raise ValueError(f'sync_direction must be one of {valid_directions}')
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['PENDING', 'SUCCESS', 'FAILED', 'PARTIAL', 'SKIPPED']
        if v not in valid_statuses:
            raise ValueError(f'status must be one of {valid_statuses}')
        return v


class SAPSyncLogResponse(BaseModel):
    """DTO for SAP sync log response"""
    id: int
    organization_id: int
    timestamp: datetime
    sync_direction: str
    entity_type: str
    entity_id: Optional[int]
    entity_identifier: Optional[str]
    sap_object_type: Optional[str]
    sap_object_key: Optional[str]
    operation: str
    status: str
    attempt_number: int
    request_payload: Optional[Dict[str, Any]]
    response_payload: Optional[Dict[str, Any]]
    error_message: Optional[str]
    error_code: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    batch_id: Optional[str]
    batch_size: Optional[int]
    batch_sequence: Optional[int]
    metadata: Optional[Dict[str, Any]]
    triggered_by: Optional[int]

    class Config:
        from_attributes = True


# ========== SAP Mapping DTOs ==========

class SAPMappingCreateDTO(BaseModel):
    """DTO for creating a SAP mapping"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    mes_entity_type: str = Field(..., min_length=1, max_length=100, description="MES entity type")
    mes_entity_id: int = Field(..., gt=0, description="MES entity ID")
    mes_entity_identifier: Optional[str] = Field(None, max_length=200, description="MES entity identifier")
    sap_object_type: str = Field(..., min_length=1, max_length=100, description="SAP object type")
    sap_object_key: str = Field(..., min_length=1, max_length=100, description="SAP object key")
    sap_system_id: Optional[str] = Field(None, max_length=50, description="SAP system ID")
    mapping_direction: str = Field(default='BIDIRECTIONAL', description="Mapping direction")
    field_mappings: Optional[Dict[str, Any]] = Field(None, description="Field-level mappings")
    transformation_rules: Optional[Dict[str, Any]] = Field(None, description="Transformation rules")
    auto_sync: bool = Field(default=False, description="Auto sync enabled")
    sync_frequency_minutes: Optional[int] = Field(None, gt=0, description="Sync frequency in minutes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    notes: Optional[str] = Field(None, description="Notes")
    created_by: int = Field(..., gt=0, description="Created by user ID")

    @field_validator('mapping_direction')
    @classmethod
    def validate_mapping_direction(cls, v):
        valid_directions = ['TO_SAP', 'FROM_SAP', 'BIDIRECTIONAL']
        if v not in valid_directions:
            raise ValueError(f'mapping_direction must be one of {valid_directions}')
        return v


class SAPMappingUpdateDTO(BaseModel):
    """DTO for updating a SAP mapping"""
    sap_object_key: Optional[str] = Field(None, max_length=100)
    sap_system_id: Optional[str] = Field(None, max_length=50)
    mapping_direction: Optional[str] = None
    field_mappings: Optional[Dict[str, Any]] = None
    transformation_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    auto_sync: Optional[bool] = None
    sync_frequency_minutes: Optional[int] = Field(None, gt=0)
    last_synced_at: Optional[datetime] = None
    last_sync_status: Optional[str] = Field(None, max_length=50)
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class SAPMappingResponse(BaseModel):
    """DTO for SAP mapping response"""
    id: int
    organization_id: int
    mes_entity_type: str
    mes_entity_id: int
    mes_entity_identifier: Optional[str]
    sap_object_type: str
    sap_object_key: str
    sap_system_id: Optional[str]
    mapping_direction: str
    field_mappings: Optional[Dict[str, Any]]
    transformation_rules: Optional[Dict[str, Any]]
    is_active: bool
    auto_sync: bool
    sync_frequency_minutes: Optional[int]
    last_synced_at: Optional[datetime]
    last_sync_status: Optional[str]
    metadata: Optional[Dict[str, Any]]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]

    class Config:
        from_attributes = True
