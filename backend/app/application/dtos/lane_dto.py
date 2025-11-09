"""
DTOs (Data Transfer Objects) for Lane and Lane Assignment
Using Pydantic for validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from app.domain.entities.lane import LaneAssignmentStatus


# Lane DTOs
class LaneCreateRequest(BaseModel):
    """Request to create a new lane"""
    plant_id: int = Field(..., gt=0)
    lane_code: str = Field(..., max_length=50, pattern="^[A-Z0-9_-]+$")
    lane_name: str = Field(..., max_length=200)
    capacity_per_day: Decimal = Field(..., gt=0)

    model_config = ConfigDict(from_attributes=True)


class LaneUpdateRequest(BaseModel):
    """Request to update a lane"""
    lane_name: Optional[str] = Field(None, max_length=200)
    capacity_per_day: Optional[Decimal] = Field(None, gt=0)
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class LaneResponse(BaseModel):
    """Response model for lane"""
    id: int
    plant_id: int
    lane_code: str
    lane_name: str
    capacity_per_day: Decimal
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class LaneListResponse(BaseModel):
    """Response model for list of lanes"""
    items: list[LaneResponse]
    total: int
    page: int
    page_size: int


# Lane Assignment DTOs
class LaneAssignmentCreateRequest(BaseModel):
    """Request to create a new lane assignment"""
    organization_id: int = Field(..., gt=0)
    plant_id: int = Field(..., gt=0)
    lane_id: int = Field(..., gt=0)
    work_order_id: int = Field(..., gt=0)
    project_id: Optional[int] = Field(None, gt=0)
    scheduled_start: date
    scheduled_end: date
    allocated_capacity: Decimal = Field(..., gt=0)
    priority: int = Field(default=0, ge=0)
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LaneAssignmentUpdateRequest(BaseModel):
    """Request to update a lane assignment"""
    scheduled_start: Optional[date] = None
    scheduled_end: Optional[date] = None
    allocated_capacity: Optional[Decimal] = Field(None, gt=0)
    priority: Optional[int] = Field(None, ge=0)
    status: Optional[LaneAssignmentStatus] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LaneAssignmentResponse(BaseModel):
    """Response model for lane assignment"""
    id: int
    organization_id: int
    plant_id: int
    lane_id: int
    work_order_id: int
    project_id: Optional[int]
    scheduled_start: date
    scheduled_end: date
    allocated_capacity: Decimal
    priority: int
    status: LaneAssignmentStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class LaneAssignmentListResponse(BaseModel):
    """Response model for list of lane assignments"""
    items: list[LaneAssignmentResponse]
    total: int
    page: int
    page_size: int


class LaneCapacityResponse(BaseModel):
    """Response model for lane capacity utilization"""
    lane_id: int
    date: date
    total_capacity: Decimal
    allocated_capacity: Decimal
    available_capacity: Decimal
    utilization_rate: Decimal  # Percentage
    assignment_count: int
