"""
Pydantic schemas for Metrics API endpoints.

These schemas define request/response models for KPI calculations.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ============================================================================
# Request Schemas
# ============================================================================

class GetOEERequest(BaseModel):
    """Request schema for getting OEE metrics."""

    plant_id: Optional[int] = Field(None, description="Filter by plant ID")
    machine_id: Optional[int] = Field(None, description="Filter by specific machine ID")
    start_date: Optional[datetime] = Field(None, description="Start of period (defaults to 30 days ago)")
    end_date: Optional[datetime] = Field(None, description="End of period (defaults to now)")
    by_machine: bool = Field(False, description="Include breakdown by individual machines")

    class Config:
        json_schema_extra = {
            "example": {
                "plant_id": 10,
                "machine_id": None,
                "start_date": "2024-11-01T00:00:00Z",
                "end_date": "2024-11-30T23:59:59Z",
                "by_machine": True
            }
        }


class GetOTDRequest(BaseModel):
    """Request schema for getting OTD metrics."""

    plant_id: Optional[int] = Field(None, description="Filter by plant ID")
    start_date: Optional[datetime] = Field(None, description="Start of period (defaults to 30 days ago)")
    end_date: Optional[datetime] = Field(None, description="End of period (defaults to now)")

    class Config:
        json_schema_extra = {
            "example": {
                "plant_id": 10,
                "start_date": "2024-11-01T00:00:00Z",
                "end_date": "2024-11-30T23:59:59Z"
            }
        }


class GetFPYRequest(BaseModel):
    """Request schema for getting FPY metrics."""

    plant_id: Optional[int] = Field(None, description="Filter by plant ID")
    start_date: Optional[datetime] = Field(None, description="Start of period (defaults to 30 days ago)")
    end_date: Optional[datetime] = Field(None, description="End of period (defaults to now)")
    include_work_order_breakdown: bool = Field(False, description="Include top worst performers by work order")
    breakdown_limit: int = Field(10, description="Number of work orders in breakdown (default 10)")

    class Config:
        json_schema_extra = {
            "example": {
                "plant_id": 10,
                "start_date": "2024-11-01T00:00:00Z",
                "end_date": "2024-11-30T23:59:59Z",
                "include_work_order_breakdown": True,
                "breakdown_limit": 10
            }
        }


# ============================================================================
# Response Schemas
# ============================================================================

class MachineOEEResponse(BaseModel):
    """Response schema for machine-level OEE breakdown."""

    machine_id: int
    machine_code: str
    machine_name: str
    total_time_minutes: float
    downtime_minutes: float
    operating_time_minutes: float
    total_pieces: int
    good_pieces: int
    defect_pieces: int
    scrapped_pieces: int
    reworked_pieces: int
    availability: float = Field(..., description="Availability percentage (0-100)")
    performance: float = Field(..., description="Performance percentage (0-100)")
    quality: float = Field(..., description="Quality percentage (0-100)")
    oee: float = Field(..., description="Overall Equipment Effectiveness percentage (0-100)")

    class Config:
        json_schema_extra = {
            "example": {
                "machine_id": 5,
                "machine_code": "CNC-001",
                "machine_name": "CNC Machining Center 1",
                "total_time_minutes": 43200.0,
                "downtime_minutes": 2160.0,
                "operating_time_minutes": 41040.0,
                "total_pieces": 1000,
                "good_pieces": 950,
                "defect_pieces": 50,
                "scrapped_pieces": 30,
                "reworked_pieces": 20,
                "availability": 95.0,
                "performance": 85.0,
                "quality": 95.0,
                "oee": 76.71
            }
        }


class OEEResponse(BaseModel):
    """Response schema for OEE metrics."""

    total_time_minutes: float
    downtime_minutes: float
    operating_time_minutes: float
    total_pieces: int
    good_pieces: int
    defect_pieces: int
    scrapped_pieces: int
    reworked_pieces: int
    availability: float = Field(..., description="Availability percentage (0-100)")
    performance: float = Field(..., description="Performance percentage (0-100)")
    quality: float = Field(..., description="Quality percentage (0-100)")
    oee: float = Field(..., description="Overall Equipment Effectiveness percentage (0-100)")
    start_date: datetime
    end_date: datetime
    machine_breakdown: Optional[List[MachineOEEResponse]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "total_time_minutes": 43200.0,
                "downtime_minutes": 2160.0,
                "operating_time_minutes": 41040.0,
                "total_pieces": 5000,
                "good_pieces": 4750,
                "defect_pieces": 250,
                "scrapped_pieces": 150,
                "reworked_pieces": 100,
                "availability": 95.0,
                "performance": 85.0,
                "quality": 95.0,
                "oee": 76.71,
                "start_date": "2024-11-01T00:00:00Z",
                "end_date": "2024-11-30T23:59:59Z",
                "machine_breakdown": []
            }
        }


class OTDResponse(BaseModel):
    """Response schema for OTD metrics."""

    total_completed: int = Field(..., description="Total completed work orders")
    on_time: int = Field(..., description="Work orders completed on-time")
    late: int = Field(..., description="Work orders completed late")
    otd_percentage: float = Field(..., description="On-Time Delivery percentage (0-100)")
    average_delay_days: float = Field(..., description="Average delay in days (negative if early)")
    start_date: datetime
    end_date: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "total_completed": 150,
                "on_time": 135,
                "late": 15,
                "otd_percentage": 90.0,
                "average_delay_days": 1.2,
                "start_date": "2024-11-01T00:00:00Z",
                "end_date": "2024-11-30T23:59:59Z"
            }
        }


class WorkOrderFPYResponse(BaseModel):
    """Response schema for work order-level FPY breakdown."""

    work_order_id: int
    work_order_number: str
    total_inspected: int
    total_passed: int
    total_failed: int
    fpy_percentage: float = Field(..., description="First Pass Yield percentage (0-100)")

    class Config:
        json_schema_extra = {
            "example": {
                "work_order_id": 123,
                "work_order_number": "WO-00123",
                "total_inspected": 100,
                "total_passed": 85,
                "total_failed": 15,
                "fpy_percentage": 85.0
            }
        }


class FPYResponse(BaseModel):
    """Response schema for FPY metrics."""

    total_inspected: int = Field(..., description="Total quantity inspected")
    total_passed: int = Field(..., description="Total quantity passed")
    total_failed: int = Field(..., description="Total quantity failed")
    fpy_percentage: float = Field(..., description="First Pass Yield percentage (0-100)")
    defect_rate: float = Field(..., description="Defect rate percentage (0-100)")
    start_date: datetime
    end_date: datetime
    work_order_breakdown: Optional[List[WorkOrderFPYResponse]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "total_inspected": 10000,
                "total_passed": 9700,
                "total_failed": 300,
                "fpy_percentage": 97.0,
                "defect_rate": 3.0,
                "start_date": "2024-11-01T00:00:00Z",
                "end_date": "2024-11-30T23:59:59Z",
                "work_order_breakdown": []
            }
        }


class KPIDashboardResponse(BaseModel):
    """Response schema for consolidated KPI dashboard."""

    oee: OEEResponse
    otd: OTDResponse
    fpy: FPYResponse
    period_start: datetime
    period_end: datetime
    generated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "oee": {
                    "total_time_minutes": 43200.0,
                    "downtime_minutes": 2160.0,
                    "operating_time_minutes": 41040.0,
                    "total_pieces": 5000,
                    "good_pieces": 4750,
                    "defect_pieces": 250,
                    "scrapped_pieces": 150,
                    "reworked_pieces": 100,
                    "availability": 95.0,
                    "performance": 85.0,
                    "quality": 95.0,
                    "oee": 76.71,
                    "start_date": "2024-11-01T00:00:00Z",
                    "end_date": "2024-11-30T23:59:59Z",
                    "machine_breakdown": None
                },
                "otd": {
                    "total_completed": 150,
                    "on_time": 135,
                    "late": 15,
                    "otd_percentage": 90.0,
                    "average_delay_days": 1.2,
                    "start_date": "2024-11-01T00:00:00Z",
                    "end_date": "2024-11-30T23:59:59Z"
                },
                "fpy": {
                    "total_inspected": 10000,
                    "total_passed": 9700,
                    "total_failed": 300,
                    "fpy_percentage": 97.0,
                    "defect_rate": 3.0,
                    "start_date": "2024-11-01T00:00:00Z",
                    "end_date": "2024-11-30T23:59:59Z",
                    "work_order_breakdown": None
                },
                "period_start": "2024-11-01T00:00:00Z",
                "period_end": "2024-11-30T23:59:59Z",
                "generated_at": "2024-11-30T15:30:00Z"
            }
        }
