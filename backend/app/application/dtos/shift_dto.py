"""
Data Transfer Objects for Shift Management API.
Defines request/response schemas for shift operations.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, time


# Shift DTOs
class ShiftCreateRequest(BaseModel):
    """Request schema for creating a new shift"""
    shift_name: str = Field(..., min_length=1, max_length=100, description="Shift name")
    shift_code: str = Field(..., min_length=1, max_length=20, description="Shift code (will be uppercased)")
    start_time: time = Field(..., description="Shift start time (HH:MM:SS)")
    end_time: time = Field(..., description="Shift end time (HH:MM:SS)")
    production_target: float = Field(0.0, ge=0, description="Production target for the shift")
    is_active: bool = Field(True, description="Whether shift is active")


class ShiftUpdateRequest(BaseModel):
    """Request schema for updating an existing shift"""
    shift_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Shift name")
    start_time: Optional[time] = Field(None, description="Shift start time")
    end_time: Optional[time] = Field(None, description="Shift end time")
    production_target: Optional[float] = Field(None, ge=0, description="Production target")
    is_active: Optional[bool] = Field(None, description="Whether shift is active")


class ShiftResponse(BaseModel):
    """Response schema for shift"""
    id: int
    organization_id: int
    plant_id: int
    shift_name: str
    shift_code: str
    start_time: time
    end_time: time
    production_target: float
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ShiftListResponse(BaseModel):
    """Response schema for paginated shift list"""
    items: List[ShiftResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Shift Handover DTOs
class ShiftHandoverCreateRequest(BaseModel):
    """Request schema for creating a shift handover"""
    from_shift_id: int = Field(..., gt=0, description="ID of shift handing over")
    to_shift_id: int = Field(..., gt=0, description="ID of shift receiving handover")
    handover_date: datetime = Field(..., description="Handover date and time")
    wip_quantity: float = Field(0.0, ge=0, description="Work-in-progress quantity")
    production_summary: str = Field(..., min_length=1, description="Summary of production activities")
    quality_issues: Optional[str] = Field(None, description="Quality issues encountered")
    machine_status: Optional[str] = Field(None, description="Machine status summary")
    material_status: Optional[str] = Field(None, description="Material availability status")
    safety_incidents: Optional[str] = Field(None, description="Safety incidents if any")


class ShiftHandoverAcknowledgeRequest(BaseModel):
    """Request schema for acknowledging a shift handover"""
    pass  # No additional fields needed, user ID comes from JWT


class ShiftHandoverResponse(BaseModel):
    """Response schema for shift handover"""
    id: int
    organization_id: int
    plant_id: int
    from_shift_id: int
    to_shift_id: int
    handover_date: datetime
    wip_quantity: float
    production_summary: str
    quality_issues: Optional[str] = None
    machine_status: Optional[str] = None
    material_status: Optional[str] = None
    safety_incidents: Optional[str] = None
    handover_by_user_id: int
    acknowledged_by_user_id: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ShiftHandoverListResponse(BaseModel):
    """Response schema for paginated shift handover list"""
    items: List[ShiftHandoverResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Shift Performance DTOs
class ShiftPerformanceResponse(BaseModel):
    """Response schema for shift performance metrics"""
    id: int
    organization_id: int
    plant_id: int
    shift_id: int
    performance_date: datetime
    production_target: float
    production_actual: float
    target_attainment_percent: float
    availability_percent: Optional[float] = None
    performance_percent: Optional[float] = None
    quality_percent: Optional[float] = None
    oee_percent: Optional[float] = None
    total_produced: float
    total_good: float
    total_rejected: float
    fpy_percent: Optional[float] = None
    planned_production_time: Optional[float] = None
    actual_run_time: Optional[float] = None
    downtime_minutes: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ShiftPerformanceListResponse(BaseModel):
    """Response schema for paginated shift performance list"""
    items: List[ShiftPerformanceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Error response schemas
class ErrorResponse(BaseModel):
    """Generic error response"""
    detail: str


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    detail: str


class NotFoundErrorResponse(BaseModel):
    """Not found error response"""
    detail: str


class ConflictErrorResponse(BaseModel):
    """Conflict error response"""
    detail: str
