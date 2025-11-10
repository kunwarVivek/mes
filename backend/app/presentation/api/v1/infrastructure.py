"""
API endpoints for Infrastructure module (Audit Logs, Notifications, Settings, Files, SAP)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user
from app.application.dtos.infrastructure_dto import (
    AuditLogCreateDTO,
    AuditLogResponse,
    NotificationCreateDTO,
    NotificationUpdateDTO,
    NotificationResponse,
    SystemSettingCreateDTO,
    SystemSettingUpdateDTO,
    SystemSettingResponse,
    FileUploadCreateDTO,
    FileUploadUpdateDTO,
    FileUploadResponse,
    SAPSyncLogCreateDTO,
    SAPSyncLogResponse,
    SAPMappingCreateDTO,
    SAPMappingUpdateDTO,
    SAPMappingResponse,
)
from app.application.services.infrastructure_service import (
    AuditLogService,
    NotificationService,
    SystemSettingService,
    FileUploadService,
    SAPSyncLogService,
    SAPMappingService,
)

router = APIRouter(prefix="/infrastructure", tags=["infrastructure"])


# ==================== Audit Log Endpoints ====================

@router.post("/audit-logs", response_model=AuditLogResponse, status_code=status.HTTP_201_CREATED)
def create_audit_log(
    log_data: AuditLogCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create audit log entry (usually called internally by middleware)"""
    service = AuditLogService(db)
    return service.create_audit_log(log_data)


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def list_audit_logs(
    organization_id: int = Query(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List audit logs with filters"""
    service = AuditLogService(db)
    return service.list_audit_logs(
        organization_id, skip, limit, start_date, end_date, action, entity_type, user_id
    )


@router.get("/audit-logs/entity/{entity_type}/{entity_id}", response_model=List[AuditLogResponse])
def get_entity_audit_history(
    entity_type: str,
    entity_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get audit history for a specific entity"""
    service = AuditLogService(db)
    return service.get_entity_history(entity_type, entity_id, skip, limit)


# ==================== Notification Endpoints ====================

@router.post("/notifications", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    notification_data: NotificationCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create notification"""
    service = NotificationService(db)
    return service.create_notification(notification_data)


@router.get("/notifications/me", response_model=List[NotificationResponse])
def list_my_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    unread_only: bool = Query(False),
    archived: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List notifications for current user"""
    service = NotificationService(db)
    user_id = current_user.get("id")
    return service.list_user_notifications(user_id, skip, limit, unread_only, archived)


@router.get("/notifications/me/unread-count", response_model=Dict[str, int])
def count_my_unread_notifications(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Count unread notifications for current user"""
    service = NotificationService(db)
    user_id = current_user.get("id")
    count = service.count_unread_notifications(user_id)
    return {"unread_count": count}


@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get notification by ID"""
    service = NotificationService(db)
    notification = service.get_notification(notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found"
        )
    return notification


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark notification as read"""
    service = NotificationService(db)
    notification = service.mark_as_read(notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found"
        )
    return notification


@router.patch("/notifications/{notification_id}/archive", response_model=NotificationResponse)
def archive_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Archive notification"""
    service = NotificationService(db)
    notification = service.mark_as_archived(notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found"
        )
    return notification


@router.post("/notifications/me/mark-all-read", response_model=Dict[str, int])
def mark_all_my_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark all notifications as read for current user"""
    service = NotificationService(db)
    user_id = current_user.get("id")
    count = service.mark_all_as_read(user_id)
    return {"marked_count": count}


# ==================== System Setting Endpoints ====================

@router.post("/settings", response_model=SystemSettingResponse, status_code=status.HTTP_201_CREATED)
def create_system_setting(
    setting_data: SystemSettingCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create system setting"""
    service = SystemSettingService(db)
    try:
        return service.create_setting(setting_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/settings", response_model=List[SystemSettingResponse])
def list_system_settings(
    organization_id: int = Query(..., gt=0),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List system settings for an organization"""
    service = SystemSettingService(db)
    return service.list_settings(organization_id, category)


@router.get("/settings/categories", response_model=List[str])
def list_setting_categories(
    organization_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all setting categories"""
    service = SystemSettingService(db)
    return service.list_categories(organization_id)


@router.get("/settings/{setting_id}", response_model=SystemSettingResponse)
def get_system_setting(
    setting_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get system setting by ID"""
    service = SystemSettingService(db)
    setting = service.get_setting(setting_id)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting {setting_id} not found"
        )
    return setting


@router.get("/settings/by-key/{setting_key}", response_model=SystemSettingResponse)
def get_setting_by_key(
    setting_key: str,
    organization_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get system setting by key"""
    service = SystemSettingService(db)
    setting = service.get_setting_by_key(organization_id, setting_key)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{setting_key}' not found"
        )
    return setting


@router.patch("/settings/{setting_id}", response_model=SystemSettingResponse)
def update_system_setting(
    setting_id: int,
    setting_data: SystemSettingUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update system setting"""
    service = SystemSettingService(db)
    user_id = current_user.get("id", 0)
    setting = service.update_setting(setting_id, setting_data, user_id)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting {setting_id} not found"
        )
    return setting


@router.delete("/settings/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_system_setting(
    setting_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete system setting (not allowed for system settings)"""
    service = SystemSettingService(db)
    if not service.delete_setting(setting_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete setting {setting_id} (not found or is system setting)"
        )


# ==================== File Upload Endpoints ====================

@router.post("/files", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
def create_file_record(
    file_data: FileUploadCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create file upload record"""
    service = FileUploadService(db)
    return service.create_file_record(file_data)


@router.get("/files", response_model=List[FileUploadResponse])
def list_organization_files(
    organization_id: int = Query(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List files for an organization"""
    service = FileUploadService(db)
    return service.list_organization_files(organization_id, skip, limit)


@router.get("/files/{file_id}", response_model=FileUploadResponse)
def get_file_record(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get file upload record by ID"""
    service = FileUploadService(db)
    file_upload = service.get_file(file_id)
    if not file_upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )
    return file_upload


@router.get("/files/entity/{entity_type}/{entity_id}", response_model=List[FileUploadResponse])
def list_entity_files(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List files for a specific entity"""
    service = FileUploadService(db)
    return service.list_entity_files(entity_type, entity_id)


@router.patch("/files/{file_id}", response_model=FileUploadResponse)
def update_file_record(
    file_id: int,
    file_data: FileUploadUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update file upload record"""
    service = FileUploadService(db)
    file_upload = service.update_file(file_id, file_data)
    if not file_upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )
    return file_upload


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file_record(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete file upload record (soft delete)"""
    service = FileUploadService(db)
    if not service.delete_file(file_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )


# ==================== SAP Sync Log Endpoints ====================

@router.post("/sap-sync-logs", response_model=SAPSyncLogResponse, status_code=status.HTTP_201_CREATED)
def create_sap_sync_log(
    log_data: SAPSyncLogCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create SAP sync log entry"""
    service = SAPSyncLogService(db)
    return service.create_sync_log(log_data)


@router.get("/sap-sync-logs", response_model=List[SAPSyncLogResponse])
def list_sap_sync_logs(
    organization_id: int = Query(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List SAP sync logs"""
    service = SAPSyncLogService(db)
    return service.list_sync_logs(organization_id, skip, limit, status)


@router.get("/sap-sync-logs/batch/{batch_id}", response_model=List[SAPSyncLogResponse])
def list_batch_sync_logs(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List SAP sync logs for a specific batch"""
    service = SAPSyncLogService(db)
    return service.list_batch_logs(batch_id)


# ==================== SAP Mapping Endpoints ====================

@router.post("/sap-mappings", response_model=SAPMappingResponse, status_code=status.HTTP_201_CREATED)
def create_sap_mapping(
    mapping_data: SAPMappingCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create SAP mapping"""
    service = SAPMappingService(db)
    try:
        return service.create_mapping(mapping_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/sap-mappings", response_model=List[SAPMappingResponse])
def list_sap_mappings(
    organization_id: int = Query(..., gt=0),
    mes_entity_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List SAP mappings"""
    service = SAPMappingService(db)
    return service.list_mappings(organization_id, mes_entity_type)


@router.get("/sap-mappings/due-for-sync", response_model=List[SAPMappingResponse])
def list_mappings_due_for_sync(
    organization_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List SAP mappings that are due for auto-sync"""
    service = SAPMappingService(db)
    return service.list_mappings_due_for_sync(organization_id)


@router.get("/sap-mappings/{mapping_id}", response_model=SAPMappingResponse)
def get_sap_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get SAP mapping by ID"""
    service = SAPMappingService(db)
    mapping = service.get_mapping(mapping_id)
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mapping {mapping_id} not found"
        )
    return mapping


@router.get("/sap-mappings/entity/{mes_entity_type}/{mes_entity_id}", response_model=SAPMappingResponse)
def get_mapping_for_entity(
    mes_entity_type: str,
    mes_entity_id: int,
    organization_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get SAP mapping for a MES entity"""
    service = SAPMappingService(db)
    mapping = service.get_mapping_for_entity(organization_id, mes_entity_type, mes_entity_id)
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mapping not found for {mes_entity_type} {mes_entity_id}"
        )
    return mapping


@router.patch("/sap-mappings/{mapping_id}", response_model=SAPMappingResponse)
def update_sap_mapping(
    mapping_id: int,
    mapping_data: SAPMappingUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update SAP mapping"""
    service = SAPMappingService(db)
    user_id = current_user.get("id", 0)
    mapping = service.update_mapping(mapping_id, mapping_data, user_id)
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mapping {mapping_id} not found"
        )
    return mapping


@router.delete("/sap-mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sap_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete SAP mapping (soft delete)"""
    service = SAPMappingService(db)
    if not service.delete_mapping(mapping_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mapping {mapping_id} not found"
        )
