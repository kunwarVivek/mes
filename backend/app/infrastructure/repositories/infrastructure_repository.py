"""
Repository for Infrastructure (Audit Logs, Notifications, System Settings, File Uploads, SAP Integration)
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta

from app.models.infrastructure import (
    AuditLog,
    Notification,
    SystemSetting,
    FileUpload,
    SAPSyncLog,
    SAPMapping
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


class AuditLogRepository:
    """Repository for Audit Log operations (TimescaleDB hypertable)"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: AuditLogCreateDTO) -> AuditLog:
        """Create a new audit log entry"""
        log = AuditLog(
            organization_id=dto.organization_id,
            entity_type=dto.entity_type,
            entity_id=dto.entity_id,
            entity_identifier=dto.entity_identifier,
            action=dto.action,
            action_category=dto.action_category,
            user_id=dto.user_id,
            user_name=dto.user_name,
            user_email=dto.user_email,
            ip_address=dto.ip_address,
            user_agent=dto.user_agent,
            request_id=dto.request_id,
            changes_before=dto.changes_before,
            changes_after=dto.changes_after,
            changes_diff=dto.changes_diff,
            metadata=dto.metadata,
            severity=dto.severity,
            success=dto.success,
            error_message=dto.error_message,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_by_organization(self, organization_id: int, skip: int = 0, limit: int = 100,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            action: Optional[str] = None,
                            entity_type: Optional[str] = None,
                            user_id: Optional[int] = None) -> List[AuditLog]:
        """List audit logs with filters"""
        query = self.db.query(AuditLog).filter(
            AuditLog.organization_id == organization_id
        )

        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        if action:
            query = query.filter(AuditLog.action == action)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        return query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()

    def list_by_entity(self, entity_type: str, entity_id: int,
                       skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """List audit logs for a specific entity"""
        return self.db.query(AuditLog).filter(
            and_(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id
            )
        ).order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()


class NotificationRepository:
    """Repository for Notification operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: NotificationCreateDTO) -> Notification:
        """Create a new notification"""
        notification = Notification(
            organization_id=dto.organization_id,
            user_id=dto.user_id,
            role_id=dto.role_id,
            notification_type=dto.notification_type,
            title=dto.title,
            message=dto.message,
            action_url=dto.action_url,
            action_label=dto.action_label,
            entity_type=dto.entity_type,
            entity_id=dto.entity_id,
            priority=dto.priority,
            delivery_channels=dto.delivery_channels,
            scheduled_for=dto.scheduled_for,
            expires_at=dto.expires_at,
            metadata=dto.metadata,
            created_by=dto.created_by,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_by_id(self, notification_id: int) -> Optional[Notification]:
        """Get notification by ID"""
        return self.db.query(Notification).filter(Notification.id == notification_id).first()

    def list_by_user(self, user_id: int, skip: int = 0, limit: int = 100,
                     unread_only: bool = False,
                     archived: bool = False) -> List[Notification]:
        """List notifications for a user"""
        query = self.db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_archived == archived
            )
        )

        if unread_only:
            query = query.filter(Notification.is_read == False)

        return query.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()

    def count_unread(self, user_id: int) -> int:
        """Count unread notifications for a user"""
        return self.db.query(func.count(Notification.id)).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_archived == False
            )
        ).scalar()

    def update(self, notification_id: int, dto: NotificationUpdateDTO) -> Optional[Notification]:
        """Update notification"""
        notification = self.get_by_id(notification_id)
        if not notification:
            return None

        if dto.is_read is not None:
            notification.is_read = dto.is_read
            if dto.is_read:
                notification.read_at = datetime.now()

        if dto.is_archived is not None:
            notification.is_archived = dto.is_archived
            if dto.is_archived:
                notification.archived_at = datetime.now()

        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        count = self.db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        ).update({
            'is_read': True,
            'read_at': datetime.now()
        })
        self.db.commit()
        return count


class SystemSettingRepository:
    """Repository for System Setting operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: SystemSettingCreateDTO) -> SystemSetting:
        """Create a new system setting"""
        setting = SystemSetting(
            organization_id=dto.organization_id,
            setting_category=dto.setting_category,
            setting_key=dto.setting_key,
            setting_name=dto.setting_name,
            description=dto.description,
            setting_value=dto.setting_value,
            setting_type=dto.setting_type,
            default_value=dto.default_value,
            validation_rules=dto.validation_rules,
            is_encrypted=dto.is_encrypted,
            is_system_setting=dto.is_system_setting,
            is_editable=dto.is_editable,
            requires_restart=dto.requires_restart,
            display_order=dto.display_order,
            ui_component=dto.ui_component,
            options=dto.options,
        )
        self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting

    def get_by_id(self, setting_id: int) -> Optional[SystemSetting]:
        """Get setting by ID"""
        return self.db.query(SystemSetting).filter(SystemSetting.id == setting_id).first()

    def get_by_key(self, organization_id: int, setting_key: str) -> Optional[SystemSetting]:
        """Get setting by key"""
        return self.db.query(SystemSetting).filter(
            and_(
                SystemSetting.organization_id == organization_id,
                SystemSetting.setting_key == setting_key,
                SystemSetting.is_active == True
            )
        ).first()

    def list_by_organization(self, organization_id: int,
                            category: Optional[str] = None) -> List[SystemSetting]:
        """List settings for an organization"""
        query = self.db.query(SystemSetting).filter(
            and_(
                SystemSetting.organization_id == organization_id,
                SystemSetting.is_active == True
            )
        )

        if category:
            query = query.filter(SystemSetting.setting_category == category)

        return query.order_by(
            SystemSetting.setting_category,
            SystemSetting.display_order,
            SystemSetting.setting_name
        ).all()

    def list_categories(self, organization_id: int) -> List[str]:
        """List all setting categories for an organization"""
        result = self.db.query(SystemSetting.setting_category.distinct()).filter(
            and_(
                SystemSetting.organization_id == organization_id,
                SystemSetting.is_active == True
            )
        ).all()
        return [row[0] for row in result]

    def update(self, setting_id: int, dto: SystemSettingUpdateDTO,
               updated_by: int) -> Optional[SystemSetting]:
        """Update system setting"""
        setting = self.get_by_id(setting_id)
        if not setting:
            return None

        # Don't allow updating system settings that are not editable
        if setting.is_system_setting and not setting.is_editable:
            if dto.setting_value is not None:
                setting.setting_value = dto.setting_value
            # Only allow updating the value, not other properties
        else:
            if dto.setting_value is not None:
                setting.setting_value = dto.setting_value
            if dto.setting_name is not None:
                setting.setting_name = dto.setting_name
            if dto.description is not None:
                setting.description = dto.description
            if dto.default_value is not None:
                setting.default_value = dto.default_value
            if dto.validation_rules is not None:
                setting.validation_rules = dto.validation_rules
            if dto.is_editable is not None:
                setting.is_editable = dto.is_editable
            if dto.requires_restart is not None:
                setting.requires_restart = dto.requires_restart
            if dto.display_order is not None:
                setting.display_order = dto.display_order
            if dto.ui_component is not None:
                setting.ui_component = dto.ui_component
            if dto.options is not None:
                setting.options = dto.options
            if dto.is_active is not None:
                setting.is_active = dto.is_active

        setting.updated_by = updated_by
        self.db.commit()
        self.db.refresh(setting)
        return setting

    def delete(self, setting_id: int) -> bool:
        """Delete system setting (not allowed for system settings)"""
        setting = self.get_by_id(setting_id)
        if not setting:
            return False

        if setting.is_system_setting:
            return False

        setting.is_active = False
        self.db.commit()
        return True


class FileUploadRepository:
    """Repository for File Upload operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: FileUploadCreateDTO) -> FileUpload:
        """Create a new file upload record"""
        file_upload = FileUpload(
            organization_id=dto.organization_id,
            file_name=dto.file_name,
            original_name=dto.original_name,
            file_path=dto.file_path,
            file_size=dto.file_size,
            mime_type=dto.mime_type,
            file_extension=dto.file_extension,
            file_hash=dto.file_hash,
            storage_provider=dto.storage_provider,
            storage_bucket=dto.storage_bucket,
            storage_key=dto.storage_key,
            entity_type=dto.entity_type,
            entity_id=dto.entity_id,
            entity_field=dto.entity_field,
            description=dto.description,
            tags=dto.tags,
            metadata=dto.metadata,
            is_public=dto.is_public,
            created_by=dto.created_by,
        )
        self.db.add(file_upload)
        self.db.commit()
        self.db.refresh(file_upload)
        return file_upload

    def get_by_id(self, file_id: int) -> Optional[FileUpload]:
        """Get file upload by ID"""
        return self.db.query(FileUpload).filter(
            and_(
                FileUpload.id == file_id,
                FileUpload.is_active == True
            )
        ).first()

    def list_by_entity(self, entity_type: str, entity_id: int) -> List[FileUpload]:
        """List files for an entity"""
        return self.db.query(FileUpload).filter(
            and_(
                FileUpload.entity_type == entity_type,
                FileUpload.entity_id == entity_id,
                FileUpload.is_active == True
            )
        ).order_by(desc(FileUpload.created_at)).all()

    def list_by_organization(self, organization_id: int, skip: int = 0, limit: int = 100) -> List[FileUpload]:
        """List files for an organization"""
        return self.db.query(FileUpload).filter(
            and_(
                FileUpload.organization_id == organization_id,
                FileUpload.is_active == True
            )
        ).order_by(desc(FileUpload.created_at)).offset(skip).limit(limit).all()

    def update(self, file_id: int, dto: FileUploadUpdateDTO) -> Optional[FileUpload]:
        """Update file upload record"""
        file_upload = self.get_by_id(file_id)
        if not file_upload:
            return None

        if dto.description is not None:
            file_upload.description = dto.description
        if dto.tags is not None:
            file_upload.tags = dto.tags
        if dto.metadata is not None:
            file_upload.metadata = dto.metadata
        if dto.is_public is not None:
            file_upload.is_public = dto.is_public
        if dto.access_url is not None:
            file_upload.access_url = dto.access_url
        if dto.access_expires_at is not None:
            file_upload.access_expires_at = dto.access_expires_at
        if dto.is_scanned is not None:
            file_upload.is_scanned = dto.is_scanned
        if dto.scan_result is not None:
            file_upload.scan_result = dto.scan_result
        if dto.scan_date is not None:
            file_upload.scan_date = dto.scan_date

        self.db.commit()
        self.db.refresh(file_upload)
        return file_upload

    def delete(self, file_id: int) -> bool:
        """Delete file upload (soft delete)"""
        file_upload = self.get_by_id(file_id)
        if not file_upload:
            return False

        file_upload.is_active = False
        file_upload.deleted_at = datetime.now()
        self.db.commit()
        return True


class SAPSyncLogRepository:
    """Repository for SAP Sync Log operations (TimescaleDB hypertable)"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: SAPSyncLogCreateDTO) -> SAPSyncLog:
        """Create a new SAP sync log entry"""
        log = SAPSyncLog(
            organization_id=dto.organization_id,
            sync_direction=dto.sync_direction,
            entity_type=dto.entity_type,
            entity_id=dto.entity_id,
            entity_identifier=dto.entity_identifier,
            sap_object_type=dto.sap_object_type,
            sap_object_key=dto.sap_object_key,
            operation=dto.operation,
            status=dto.status,
            attempt_number=dto.attempt_number,
            request_payload=dto.request_payload,
            response_payload=dto.response_payload,
            error_message=dto.error_message,
            error_code=dto.error_code,
            started_at=dto.started_at,
            completed_at=dto.completed_at,
            duration_ms=dto.duration_ms,
            batch_id=dto.batch_id,
            batch_size=dto.batch_size,
            batch_sequence=dto.batch_sequence,
            metadata=dto.metadata,
            triggered_by=dto.triggered_by,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_by_organization(self, organization_id: int, skip: int = 0, limit: int = 100,
                            status: Optional[str] = None) -> List[SAPSyncLog]:
        """List SAP sync logs"""
        query = self.db.query(SAPSyncLog).filter(
            SAPSyncLog.organization_id == organization_id
        )

        if status:
            query = query.filter(SAPSyncLog.status == status)

        return query.order_by(desc(SAPSyncLog.timestamp)).offset(skip).limit(limit).all()

    def list_by_batch(self, batch_id: str) -> List[SAPSyncLog]:
        """List logs for a specific batch"""
        return self.db.query(SAPSyncLog).filter(
            SAPSyncLog.batch_id == batch_id
        ).order_by(SAPSyncLog.batch_sequence).all()


class SAPMappingRepository:
    """Repository for SAP Mapping operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: SAPMappingCreateDTO) -> SAPMapping:
        """Create a new SAP mapping"""
        mapping = SAPMapping(
            organization_id=dto.organization_id,
            mes_entity_type=dto.mes_entity_type,
            mes_entity_id=dto.mes_entity_id,
            mes_entity_identifier=dto.mes_entity_identifier,
            sap_object_type=dto.sap_object_type,
            sap_object_key=dto.sap_object_key,
            sap_system_id=dto.sap_system_id,
            mapping_direction=dto.mapping_direction,
            field_mappings=dto.field_mappings,
            transformation_rules=dto.transformation_rules,
            auto_sync=dto.auto_sync,
            sync_frequency_minutes=dto.sync_frequency_minutes,
            metadata=dto.metadata,
            notes=dto.notes,
            created_by=dto.created_by,
        )
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def get_by_id(self, mapping_id: int) -> Optional[SAPMapping]:
        """Get mapping by ID"""
        return self.db.query(SAPMapping).filter(SAPMapping.id == mapping_id).first()

    def get_by_mes_entity(self, organization_id: int, mes_entity_type: str,
                          mes_entity_id: int) -> Optional[SAPMapping]:
        """Get mapping by MES entity"""
        return self.db.query(SAPMapping).filter(
            and_(
                SAPMapping.organization_id == organization_id,
                SAPMapping.mes_entity_type == mes_entity_type,
                SAPMapping.mes_entity_id == mes_entity_id,
                SAPMapping.is_active == True
            )
        ).first()

    def list_by_organization(self, organization_id: int,
                            mes_entity_type: Optional[str] = None) -> List[SAPMapping]:
        """List SAP mappings"""
        query = self.db.query(SAPMapping).filter(
            and_(
                SAPMapping.organization_id == organization_id,
                SAPMapping.is_active == True
            )
        )

        if mes_entity_type:
            query = query.filter(SAPMapping.mes_entity_type == mes_entity_type)

        return query.order_by(SAPMapping.mes_entity_type, SAPMapping.mes_entity_id).all()

    def list_due_for_sync(self, organization_id: int) -> List[SAPMapping]:
        """List mappings due for auto-sync"""
        return self.db.query(SAPMapping).filter(
            and_(
                SAPMapping.organization_id == organization_id,
                SAPMapping.is_active == True,
                SAPMapping.auto_sync == True
            )
        ).all()

    def update(self, mapping_id: int, dto: SAPMappingUpdateDTO,
               updated_by: int) -> Optional[SAPMapping]:
        """Update SAP mapping"""
        mapping = self.get_by_id(mapping_id)
        if not mapping:
            return None

        if dto.sap_object_key is not None:
            mapping.sap_object_key = dto.sap_object_key
        if dto.sap_system_id is not None:
            mapping.sap_system_id = dto.sap_system_id
        if dto.mapping_direction is not None:
            mapping.mapping_direction = dto.mapping_direction
        if dto.field_mappings is not None:
            mapping.field_mappings = dto.field_mappings
        if dto.transformation_rules is not None:
            mapping.transformation_rules = dto.transformation_rules
        if dto.is_active is not None:
            mapping.is_active = dto.is_active
        if dto.auto_sync is not None:
            mapping.auto_sync = dto.auto_sync
        if dto.sync_frequency_minutes is not None:
            mapping.sync_frequency_minutes = dto.sync_frequency_minutes
        if dto.last_synced_at is not None:
            mapping.last_synced_at = dto.last_synced_at
        if dto.last_sync_status is not None:
            mapping.last_sync_status = dto.last_sync_status
        if dto.metadata is not None:
            mapping.metadata = dto.metadata
        if dto.notes is not None:
            mapping.notes = dto.notes

        mapping.updated_by = updated_by
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def delete(self, mapping_id: int) -> bool:
        """Delete SAP mapping (soft delete)"""
        mapping = self.get_by_id(mapping_id)
        if not mapping:
            return False

        mapping.is_active = False
        self.db.commit()
        return True
