"""
Data Transfer Objects (DTOs) for Machine & Equipment module.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from app.domain.entities.machine import MachineStatus


class MachineCreateDTO(BaseModel):
    """DTO for creating a new machine"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    plant_id: int = Field(..., gt=0, description="Plant ID")
    machine_code: str = Field(..., min_length=1, max_length=20, description="Machine code (alphanumeric)")
    machine_name: str = Field(..., min_length=1, max_length=200, description="Machine name")
    description: Optional[str] = Field(None, description="Machine description")
    work_center_id: int = Field(..., gt=0, description="Work center ID")
    status: MachineStatus = Field(default=MachineStatus.AVAILABLE, description="Initial machine status")

    @field_validator('machine_code')
    @classmethod
    def validate_machine_code(cls, v: str) -> str:
        """Validate machine code is alphanumeric"""
        if not v.replace(' ', '').isalnum():
            raise ValueError("Machine code must be alphanumeric")
        return v.upper().strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "organization_id": 1,
                "plant_id": 1,
                "machine_code": "M001",
                "machine_name": "CNC Machine 1",
                "description": "CNC Milling Machine",
                "work_center_id": 1,
                "status": "AVAILABLE"
            }
        }
    }


class MachineResponseDTO(BaseModel):
    """DTO for machine response"""
    id: int
    organization_id: int
    plant_id: int
    machine_code: str
    machine_name: str
    description: Optional[str]
    work_center_id: int
    status: MachineStatus
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "organization_id": 1,
                "plant_id": 1,
                "machine_code": "M001",
                "machine_name": "CNC Machine 1",
                "description": "CNC Milling Machine",
                "work_center_id": 1,
                "status": "AVAILABLE",
                "is_active": True,
                "created_at": "2025-11-08T08:00:00Z",
                "updated_at": None
            }
        }
    }


class MachineStatusUpdateDTO(BaseModel):
    """DTO for updating machine status"""
    status: MachineStatus = Field(..., description="New machine status")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes about status change")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "RUNNING",
                "notes": "Started production shift"
            }
        }
    }


class MachineStatusHistoryResponseDTO(BaseModel):
    """DTO for machine status history response"""
    id: int
    machine_id: int
    status: MachineStatus
    started_at: datetime
    ended_at: Optional[datetime]
    notes: Optional[str]
    duration_minutes: Optional[float]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "machine_id": 1,
                "status": "RUNNING",
                "started_at": "2025-11-08T08:00:00Z",
                "ended_at": "2025-11-08T12:00:00Z",
                "notes": "Morning production shift",
                "duration_minutes": 240.0
            }
        }
    }


class MachineStatusUpdateResponseDTO(BaseModel):
    """DTO for status update response including history record"""
    machine: MachineResponseDTO
    status_history: MachineStatusHistoryResponseDTO

    model_config = {
        "json_schema_extra": {
            "example": {
                "machine": {
                    "id": 1,
                    "machine_code": "M001",
                    "status": "RUNNING"
                },
                "status_history": {
                    "id": 1,
                    "status": "RUNNING",
                    "started_at": "2025-11-08T08:00:00Z"
                }
            }
        }
    }


class MachineListResponseDTO(BaseModel):
    """DTO for paginated machine list response"""
    items: list[MachineResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class OEEMetricsDTO(BaseModel):
    """DTO for OEE calculation results"""
    availability: float = Field(..., ge=0.0, le=1.0, description="Availability (0-1)")
    performance: float = Field(..., ge=0.0, le=1.0, description="Performance (0-1)")
    quality: float = Field(..., ge=0.0, le=1.0, description="Quality (0-1)")
    oee_score: float = Field(..., ge=0.0, le=1.0, description="Overall OEE (0-1)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "availability": 0.9375,
                "performance": 0.8889,
                "quality": 0.95,
                "oee_score": 0.7917
            }
        }
    }


class OEECalculationRequestDTO(BaseModel):
    """DTO for OEE calculation request parameters"""
    start_date: datetime = Field(..., description="Start of time period")
    end_date: datetime = Field(..., description="End of time period")
    ideal_cycle_time: float = Field(..., gt=0, description="Ideal cycle time per piece (minutes)")
    total_pieces: int = Field(..., ge=0, description="Total pieces produced")
    defect_pieces: int = Field(0, ge=0, description="Number of defective pieces")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: datetime, info) -> datetime:
        """Validate end_date is after start_date"""
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError("end_date must be after start_date")
        return v

    @field_validator('defect_pieces')
    @classmethod
    def validate_defects(cls, v: int, info) -> int:
        """Validate defect_pieces doesn't exceed total_pieces"""
        if 'total_pieces' in info.data and v > info.data['total_pieces']:
            raise ValueError("defect_pieces cannot exceed total_pieces")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "start_date": "2025-11-08T08:00:00Z",
                "end_date": "2025-11-08T16:00:00Z",
                "ideal_cycle_time": 1.0,
                "total_pieces": 400,
                "defect_pieces": 20
            }
        }
    }


class MachineUtilizationDTO(BaseModel):
    """DTO for machine utilization metrics response"""
    machine_id: int = Field(..., description="Machine ID")
    machine_code: str = Field(..., description="Machine code")
    period_start: datetime = Field(..., description="Start of time period")
    period_end: datetime = Field(..., description="End of time period")
    utilization_percent: float = Field(..., ge=0.0, le=100.0, description="Utilization percentage")
    total_available_hours: float = Field(..., ge=0.0, description="Total available hours in period")
    total_running_hours: float = Field(..., ge=0.0, description="Total running hours")
    total_downtime_hours: float = Field(..., ge=0.0, description="Total downtime hours")
    oee_availability: float = Field(..., ge=0.0, le=100.0, description="OEE Availability percentage")
    oee_performance: Optional[float] = Field(None, ge=0.0, le=100.0, description="OEE Performance percentage (requires ideal_cycle_time)")
    oee_quality: Optional[float] = Field(None, ge=0.0, le=100.0, description="OEE Quality percentage (requires good_units/total_units)")
    oee_overall: Optional[float] = Field(None, ge=0.0, le=100.0, description="Overall OEE percentage")
    capacity_units_per_hour: Optional[float] = Field(None, ge=0.0, description="Machine capacity in units per hour")

    model_config = {
        "json_schema_extra": {
            "example": {
                "machine_id": 123,
                "machine_code": "CNC-001",
                "period_start": "2024-11-01T00:00:00Z",
                "period_end": "2024-11-12T23:59:59Z",
                "utilization_percent": 75.5,
                "total_available_hours": 240.0,
                "total_running_hours": 181.2,
                "total_downtime_hours": 58.8,
                "oee_availability": 75.5,
                "oee_performance": None,
                "oee_quality": None,
                "oee_overall": None,
                "capacity_units_per_hour": 100.0
            }
        }
    }
