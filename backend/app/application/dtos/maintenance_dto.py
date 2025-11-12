"""
DTOs for Maintenance Management module.
Pydantic models for API request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from app.domain.entities.maintenance import TriggerType, PMStatus, DowntimeCategory


# PM Schedule DTOs
class PMScheduleCreateDTO(BaseModel):
    """DTO for creating a PM schedule"""
    schedule_code: str = Field(..., min_length=1, max_length=50)
    schedule_name: str = Field(..., min_length=1, max_length=200)
    machine_id: int = Field(..., gt=0)
    trigger_type: TriggerType
    frequency_days: Optional[int] = Field(None, gt=0)
    meter_threshold: Optional[float] = Field(None, gt=0)
    is_active: bool = True

    @field_validator('frequency_days', 'meter_threshold')
    @classmethod
    def validate_trigger_requirements(cls, v, info):
        """Validate trigger type requirements"""
        trigger_type = info.data.get('trigger_type')
        field_name = info.field_name

        if trigger_type == TriggerType.CALENDAR and field_name == 'frequency_days' and v is None:
            raise ValueError("Calendar-based schedules require frequency_days")
        if trigger_type == TriggerType.METER and field_name == 'meter_threshold' and v is None:
            raise ValueError("Meter-based schedules require meter_threshold")

        return v


class PMScheduleUpdateDTO(BaseModel):
    """DTO for updating a PM schedule"""
    schedule_name: Optional[str] = Field(None, min_length=1, max_length=200)
    frequency_days: Optional[int] = Field(None, gt=0)
    meter_threshold: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None


class PMScheduleResponseDTO(BaseModel):
    """DTO for PM schedule response"""
    id: int
    organization_id: int
    plant_id: int
    schedule_code: str
    schedule_name: str
    machine_id: int
    trigger_type: TriggerType
    frequency_days: Optional[int]
    meter_threshold: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# PM Work Order DTOs
class PMWorkOrderCreateDTO(BaseModel):
    """DTO for creating a PM work order (typically auto-generated)"""
    pm_schedule_id: int = Field(..., gt=0)
    machine_id: int = Field(..., gt=0)
    pm_number: str = Field(..., min_length=1, max_length=50)
    scheduled_date: datetime
    due_date: datetime
    notes: Optional[str] = None


class PMWorkOrderUpdateDTO(BaseModel):
    """DTO for updating a PM work order"""
    status: Optional[PMStatus] = None
    notes: Optional[str] = None


class PMWorkOrderResponseDTO(BaseModel):
    """DTO for PM work order response"""
    id: int
    organization_id: int
    plant_id: int
    pm_schedule_id: int
    machine_id: int
    pm_number: str
    status: PMStatus
    scheduled_date: datetime
    due_date: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Downtime Event DTOs
class DowntimeEventCreateDTO(BaseModel):
    """DTO for creating a downtime event"""
    machine_id: int = Field(..., gt=0)
    category: DowntimeCategory
    reason: str = Field(..., min_length=1, max_length=500)
    started_at: datetime
    ended_at: Optional[datetime] = None
    notes: Optional[str] = None

    @field_validator('ended_at')
    @classmethod
    def validate_end_time(cls, v, info):
        """Validate end time is after start time"""
        started_at = info.data.get('started_at')
        if v is not None and started_at is not None and v < started_at:
            raise ValueError("End time cannot be before start time")
        return v


class DowntimeEventUpdateDTO(BaseModel):
    """DTO for updating a downtime event"""
    ended_at: Optional[datetime] = None
    notes: Optional[str] = None


class DowntimeEventResponseDTO(BaseModel):
    """DTO for downtime event response"""
    id: int
    organization_id: int
    plant_id: int
    machine_id: int
    category: DowntimeCategory
    reason: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# MTBF/MTTR Metrics DTOs
class MTBFMTTRMetricsDTO(BaseModel):
    """DTO for MTBF/MTTR metrics response"""
    machine_id: int
    time_period_start: datetime
    time_period_end: datetime
    total_operating_time: float
    total_repair_time: float
    number_of_failures: int
    mtbf: float
    mttr: float
    availability: float


class MTBFMTTRQueryDTO(BaseModel):
    """DTO for querying MTBF/MTTR metrics"""
    machine_id: Optional[int] = Field(None, gt=0)
    start_date: datetime
    end_date: datetime

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        """Validate end date is after start date"""
        start_date = info.data.get('start_date')
        if start_date is not None and v < start_date:
            raise ValueError("End date cannot be before start date")
        return v


# Comprehensive Maintenance Metrics DTOs
class MachineMetricsDTO(BaseModel):
    """DTO for individual machine maintenance metrics"""
    machine_id: int
    machine_code: str
    machine_name: str
    mtbf_hours: float
    mttr_hours: float
    total_failures: int
    total_downtime_hours: float
    total_repair_hours: float
    total_operating_hours: float
    availability_percent: float
    pm_compliance_percent: float
    scheduled_pm_count: int
    completed_pm_count: int


class PlantAggregateMetricsDTO(BaseModel):
    """DTO for plant-level aggregate metrics"""
    avg_mtbf_hours: float
    avg_mttr_hours: float
    total_failures: int
    total_downtime_hours: float
    avg_availability_percent: float
    avg_pm_compliance_percent: float


class MaintenanceMetricsResponseDTO(BaseModel):
    """DTO for comprehensive maintenance metrics response"""
    period_start: datetime
    period_end: datetime
    machine_metrics: List[MachineMetricsDTO]
    plant_aggregate: PlantAggregateMetricsDTO
