"""
Infrastructure Service - Business logic for audit logs, notifications, settings, files, SAP integration
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.infrastructure import (
    AuditLog,
    Notification,
    SystemSetting,
    FileUpload,
    SAPSyncLog,
    SAPMapping
)
from app.infrastructure.repositories.infrastructure_repository import (
    AuditLogRepository,
    NotificationRepository,
    SystemSettingRepository,
    FileUploadRepository,
    SAPSyncLogRepository,
    SAPMappingRepository,
)
from app.application.dtos.infrastructure_dto import (
    AuditLogCreateDTO,
    NotificationCreateDTO,
    NotificationUpdateDTO,
    SystemSettingCreateDTO,
    SystemSettingUpdateDTO,
    FileUploadCreateDTO,
    FileUploadUpdateDTO,
    SAPSyncLogCreateDTO,
    SAPMappingCreateDTO,
    SAPMappingUpdateDTO,
)


class AuditLogService:
    """Service for Audit Log operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = AuditLogRepository(db)

    def create_audit_log(self, dto: AuditLogCreateDTO) -> AuditLog:
        """Create audit log entry"""
        return self.repo.create(dto)

    def log_action(self, organization_id: int, entity_type: str, entity_id: Optional[int],
                   action: str, user_id: Optional[int] = None, user_name: Optional[str] = None,
                   changes_before: Optional[Dict] = None, changes_after: Optional[Dict] = None,
                   **kwargs) -> AuditLog:
        """
        Convenience method to log an action.

        Args:
            organization_id: Organization ID
            entity_type: Type of entity (table name)
            entity_id: Entity ID
            action: Action performed (CREATE, UPDATE, DELETE, etc.)
            user_id: User who performed action
            user_name: User name
            changes_before: State before change
            changes_after: State after change
            **kwargs: Additional fields (ip_address, user_agent, metadata, etc.)
        """
        dto = AuditLogCreateDTO(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            user_name=user_name,
            changes_before=changes_before,
            changes_after=changes_after,
            **kwargs
        )
        return self.repo.create(dto)

    def list_audit_logs(self, organization_id: int, skip: int = 0, limit: int = 100,
                       start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                       action: Optional[str] = None, entity_type: Optional[str] = None,
                       user_id: Optional[int] = None) -> List[AuditLog]:
        """List audit logs with filters"""
        return self.repo.list_by_organization(
            organization_id, skip, limit, start_date, end_date, action, entity_type, user_id
        )

    def get_entity_history(self, entity_type: str, entity_id: int,
                          skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """Get audit history for a specific entity"""
        return self.repo.list_by_entity(entity_type, entity_id, skip, limit)


class NotificationService:
    """Service for Notification operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)

    def create_notification(self, dto: NotificationCreateDTO) -> Notification:
        """Create notification"""
        return self.repo.create(dto)

    def send_notification(self, organization_id: int, user_id: int, title: str,
                         message: str, notification_type: str = 'INFO',
                         **kwargs) -> Notification:
        """
        Convenience method to send a notification.

        Args:
            organization_id: Organization ID
            user_id: Recipient user ID
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            **kwargs: Additional fields (action_url, priority, entity_type, etc.)
        """
        dto = NotificationCreateDTO(
            organization_id=organization_id,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            **kwargs
        )
        return self.repo.create(dto)

    def get_notification(self, notification_id: int) -> Optional[Notification]:
        """Get notification by ID"""
        return self.repo.get_by_id(notification_id)

    def list_user_notifications(self, user_id: int, skip: int = 0, limit: int = 100,
                                unread_only: bool = False,
                                archived: bool = False) -> List[Notification]:
        """List notifications for a user"""
        return self.repo.list_by_user(user_id, skip, limit, unread_only, archived)

    def count_unread_notifications(self, user_id: int) -> int:
        """Count unread notifications for a user"""
        return self.repo.count_unread(user_id)

    def mark_as_read(self, notification_id: int) -> Optional[Notification]:
        """Mark notification as read"""
        dto = NotificationUpdateDTO(is_read=True)
        return self.repo.update(notification_id, dto)

    def mark_as_archived(self, notification_id: int) -> Optional[Notification]:
        """Archive notification"""
        dto = NotificationUpdateDTO(is_archived=True)
        return self.repo.update(notification_id, dto)

    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        return self.repo.mark_all_as_read(user_id)


class SystemSettingService:
    """Service for System Setting operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = SystemSettingRepository(db)

    def create_setting(self, dto: SystemSettingCreateDTO) -> SystemSetting:
        """Create system setting"""
        # Check for duplicate key
        existing = self.repo.get_by_key(dto.organization_id, dto.setting_key)
        if existing:
            raise ValueError(f"Setting key '{dto.setting_key}' already exists")

        return self.repo.create(dto)

    def get_setting(self, setting_id: int) -> Optional[SystemSetting]:
        """Get setting by ID"""
        return self.repo.get_by_id(setting_id)

    def get_setting_by_key(self, organization_id: int, setting_key: str) -> Optional[SystemSetting]:
        """Get setting by key"""
        return self.repo.get_by_key(organization_id, setting_key)

    def get_setting_value(self, organization_id: int, setting_key: str,
                         default: Any = None) -> Any:
        """
        Get typed setting value by key.

        Returns the typed value (e.g., int, bool, dict) or default if not found.
        """
        setting = self.repo.get_by_key(organization_id, setting_key)
        if not setting:
            return default

        typed_value = setting.get_typed_value()
        return typed_value if typed_value is not None else default

    def list_settings(self, organization_id: int,
                     category: Optional[str] = None) -> List[SystemSetting]:
        """List settings for an organization"""
        return self.repo.list_by_organization(organization_id, category)

    def list_categories(self, organization_id: int) -> List[str]:
        """List all setting categories"""
        return self.repo.list_categories(organization_id)

    def update_setting(self, setting_id: int, dto: SystemSettingUpdateDTO,
                      updated_by: int) -> Optional[SystemSetting]:
        """Update system setting"""
        return self.repo.update(setting_id, dto, updated_by)

    def update_setting_value(self, organization_id: int, setting_key: str,
                           value: str, updated_by: int) -> Optional[SystemSetting]:
        """Convenience method to update just the value"""
        setting = self.repo.get_by_key(organization_id, setting_key)
        if not setting:
            return None

        dto = SystemSettingUpdateDTO(setting_value=value)
        return self.repo.update(setting.id, dto, updated_by)

    def delete_setting(self, setting_id: int) -> bool:
        """Delete system setting (not allowed for system settings)"""
        return self.repo.delete(setting_id)


class FileUploadService:
    """Service for File Upload operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = FileUploadRepository(db)

    def create_file_record(self, dto: FileUploadCreateDTO) -> FileUpload:
        """Create file upload record"""
        return self.repo.create(dto)

    def register_upload(self, organization_id: int, file_name: str, original_name: str,
                       file_path: str, file_size: int, created_by: int,
                       **kwargs) -> FileUpload:
        """
        Convenience method to register a file upload.

        Args:
            organization_id: Organization ID
            file_name: Stored file name
            original_name: Original file name
            file_path: File storage path
            file_size: File size in bytes
            created_by: User who uploaded
            **kwargs: Additional fields (mime_type, entity_type, tags, etc.)
        """
        dto = FileUploadCreateDTO(
            organization_id=organization_id,
            file_name=file_name,
            original_name=original_name,
            file_path=file_path,
            file_size=file_size,
            created_by=created_by,
            **kwargs
        )
        return self.repo.create(dto)

    def get_file(self, file_id: int) -> Optional[FileUpload]:
        """Get file upload by ID"""
        return self.repo.get_by_id(file_id)

    def list_entity_files(self, entity_type: str, entity_id: int) -> List[FileUpload]:
        """List files for an entity"""
        return self.repo.list_by_entity(entity_type, entity_id)

    def list_organization_files(self, organization_id: int,
                               skip: int = 0, limit: int = 100) -> List[FileUpload]:
        """List files for an organization"""
        return self.repo.list_by_organization(organization_id, skip, limit)

    def update_file(self, file_id: int, dto: FileUploadUpdateDTO) -> Optional[FileUpload]:
        """Update file upload record"""
        return self.repo.update(file_id, dto)

    def mark_as_scanned(self, file_id: int, scan_result: str) -> Optional[FileUpload]:
        """Mark file as scanned with result"""
        dto = FileUploadUpdateDTO(
            is_scanned=True,
            scan_result=scan_result,
            scan_date=datetime.now()
        )
        return self.repo.update(file_id, dto)

    def delete_file(self, file_id: int) -> bool:
        """Delete file upload (soft delete)"""
        return self.repo.delete(file_id)


class SAPSyncLogService:
    """Service for SAP Sync Log operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = SAPSyncLogRepository(db)

    def create_sync_log(self, dto: SAPSyncLogCreateDTO) -> SAPSyncLog:
        """Create SAP sync log entry"""
        return self.repo.create(dto)

    def log_sync_operation(self, organization_id: int, sync_direction: str,
                          entity_type: str, operation: str, status: str,
                          **kwargs) -> SAPSyncLog:
        """
        Convenience method to log a SAP sync operation.

        Args:
            organization_id: Organization ID
            sync_direction: TO_SAP, FROM_SAP, or BIDIRECTIONAL
            entity_type: Type of entity being synced
            operation: Operation type (CREATE, UPDATE, DELETE, SYNC)
            status: Sync status (PENDING, SUCCESS, FAILED, etc.)
            **kwargs: Additional fields (entity_id, sap_object_type, payloads, etc.)
        """
        dto = SAPSyncLogCreateDTO(
            organization_id=organization_id,
            sync_direction=sync_direction,
            entity_type=entity_type,
            operation=operation,
            status=status,
            **kwargs
        )
        return self.repo.create(dto)

    def list_sync_logs(self, organization_id: int, skip: int = 0, limit: int = 100,
                      status: Optional[str] = None) -> List[SAPSyncLog]:
        """List SAP sync logs"""
        return self.repo.list_by_organization(organization_id, skip, limit, status)

    def list_batch_logs(self, batch_id: str) -> List[SAPSyncLog]:
        """List logs for a specific batch"""
        return self.repo.list_by_batch(batch_id)


class SAPMappingService:
    """Service for SAP Mapping operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = SAPMappingRepository(db)

    def create_mapping(self, dto: SAPMappingCreateDTO) -> SAPMapping:
        """Create SAP mapping"""
        # Check for duplicate mapping
        existing = self.repo.get_by_mes_entity(
            dto.organization_id, dto.mes_entity_type, dto.mes_entity_id
        )
        if existing:
            raise ValueError(
                f"Mapping already exists for {dto.mes_entity_type} {dto.mes_entity_id}"
            )

        return self.repo.create(dto)

    def get_mapping(self, mapping_id: int) -> Optional[SAPMapping]:
        """Get mapping by ID"""
        return self.repo.get_by_id(mapping_id)

    def get_mapping_for_entity(self, organization_id: int, mes_entity_type: str,
                               mes_entity_id: int) -> Optional[SAPMapping]:
        """Get mapping for a MES entity"""
        return self.repo.get_by_mes_entity(organization_id, mes_entity_type, mes_entity_id)

    def list_mappings(self, organization_id: int,
                     mes_entity_type: Optional[str] = None) -> List[SAPMapping]:
        """List SAP mappings"""
        return self.repo.list_by_organization(organization_id, mes_entity_type)

    def list_mappings_due_for_sync(self, organization_id: int) -> List[SAPMapping]:
        """List mappings that are due for auto-sync"""
        all_due = self.repo.list_due_for_sync(organization_id)

        # Filter to only those actually due based on frequency
        return [m for m in all_due if m.is_sync_due()]

    def update_mapping(self, mapping_id: int, dto: SAPMappingUpdateDTO,
                      updated_by: int) -> Optional[SAPMapping]:
        """Update SAP mapping"""
        return self.repo.update(mapping_id, dto, updated_by)

    def update_sync_status(self, mapping_id: int, status: str,
                          updated_by: int) -> Optional[SAPMapping]:
        """Update sync status after a sync operation"""
        dto = SAPMappingUpdateDTO(
            last_synced_at=datetime.now(),
            last_sync_status=status
        )
        return self.repo.update(mapping_id, dto, updated_by)

    def delete_mapping(self, mapping_id: int) -> bool:
        """Delete SAP mapping (soft delete)"""
        return self.repo.delete(mapping_id)
