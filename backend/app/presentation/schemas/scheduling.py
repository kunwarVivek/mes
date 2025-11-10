"""
Pydantic schemas for Scheduling API endpoints.

These schemas define request/response models for Gantt chart and scheduling.
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from enum import Enum


class ConflictTypeEnum(str, Enum):
    """Conflict type enumeration."""
    LANE_OVERLOAD = "LANE_OVERLOAD"
    DEPENDENCY_VIOLATION = "DEPENDENCY_VIOLATION"
    CAPACITY_EXCEEDED = "CAPACITY_EXCEEDED"


class SeverityEnum(str, Enum):
    """Severity enumeration."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ============================================================================
# Request Schemas
# ============================================================================

class GetGanttChartRequest(BaseModel):
    """Request schema for getting Gantt chart data."""

    plant_id: Optional[int] = Field(None, description="Filter by plant ID")
    start_date: Optional[date] = Field(None, description="Filter by start date (>=)")
    end_date: Optional[date] = Field(None, description="Filter by end date (<=)")
    lane_ids: Optional[List[int]] = Field(None, description="Filter by lane IDs")
    include_completed: bool = Field(False, description="Include completed work orders")

    class Config:
        json_schema_extra = {
            "example": {
                "plant_id": 10,
                "start_date": "2024-11-01",
                "end_date": "2024-11-30",
                "lane_ids": [1, 2, 3],
                "include_completed": False
            }
        }


class ValidateScheduleRequest(BaseModel):
    """Request schema for validating schedule."""

    work_order_id: int = Field(..., description="Work order ID to validate")
    lane_id: int = Field(..., description="Target lane ID")
    start_date: datetime = Field(..., description="Proposed start date")
    end_date: datetime = Field(..., description="Proposed end date")

    class Config:
        json_schema_extra = {
            "example": {
                "work_order_id": 123,
                "lane_id": 5,
                "start_date": "2024-11-15T08:00:00Z",
                "end_date": "2024-11-20T17:00:00Z"
            }
        }


# ============================================================================
# Response Schemas
# ============================================================================

class GanttTaskResponse(BaseModel):
    """Response schema for a single Gantt chart task."""

    work_order_id: int
    work_order_number: str
    operation_id: Optional[int] = None
    operation_name: Optional[str] = None
    operation_number: Optional[int] = None
    start_date: datetime
    end_date: datetime
    duration_hours: float
    lane_id: Optional[int] = None
    lane_code: Optional[str] = None
    dependencies: List[int] = []
    progress_percent: float
    status: str
    is_critical_path: bool = False
    scheduling_mode: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "work_order_id": 123,
                "work_order_number": "WO-00123",
                "operation_id": 456,
                "operation_name": "Machining",
                "operation_number": 10,
                "start_date": "2024-11-15T08:00:00Z",
                "end_date": "2024-11-15T16:00:00Z",
                "duration_hours": 8.0,
                "lane_id": 5,
                "lane_code": "LINE-01",
                "dependencies": [122],
                "progress_percent": 0.0,
                "status": "PLANNED",
                "is_critical_path": False,
                "scheduling_mode": "SEQUENTIAL"
            }
        }


class ConflictResponse(BaseModel):
    """Response schema for a scheduling conflict."""

    conflict_type: ConflictTypeEnum
    severity: SeverityEnum
    description: str
    affected_work_orders: List[int]
    affected_lanes: List[int]
    details: dict

    class Config:
        json_schema_extra = {
            "example": {
                "conflict_type": "LANE_OVERLOAD",
                "severity": "HIGH",
                "description": "Lane LINE-01 has overlapping assignments",
                "affected_work_orders": [123, 124],
                "affected_lanes": [5],
                "details": {
                    "work_order_1": "WO-00123",
                    "work_order_2": "WO-00124",
                    "overlap_start": "2024-11-15T10:00:00Z",
                    "overlap_end": "2024-11-15T16:00:00Z"
                }
            }
        }


class GanttChartResponse(BaseModel):
    """Response schema for complete Gantt chart."""

    tasks: List[GanttTaskResponse]
    conflicts: List[ConflictResponse]
    critical_path: List[int]
    start_date: datetime
    end_date: datetime
    total_work_orders: int

    class Config:
        json_schema_extra = {
            "example": {
                "tasks": [],
                "conflicts": [],
                "critical_path": [123],
                "start_date": "2024-11-01T00:00:00Z",
                "end_date": "2024-11-30T23:59:59Z",
                "total_work_orders": 15
            }
        }


class ValidationResultResponse(BaseModel):
    """Response schema for schedule validation result."""

    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []

    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": [
                    "Duration of 30 days seems unusually long"
                ]
            }
        }


class ConflictsListResponse(BaseModel):
    """Response schema for conflicts list."""

    conflicts: List[ConflictResponse]
    total_conflicts: int
    plant_id: int
    date_range_start: date
    date_range_end: date

    class Config:
        json_schema_extra = {
            "example": {
                "conflicts": [],
                "total_conflicts": 2,
                "plant_id": 10,
                "date_range_start": "2024-11-01",
                "date_range_end": "2024-11-30"
            }
        }
