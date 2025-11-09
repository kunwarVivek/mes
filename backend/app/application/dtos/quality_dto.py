"""
Data Transfer Objects (DTOs) for Quality Management module.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class NCRStatusDTO(str, Enum):
    """NCR status enumeration"""
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class DefectTypeDTO(str, Enum):
    """Defect type enumeration"""
    DIMENSIONAL = "DIMENSIONAL"
    VISUAL = "VISUAL"
    FUNCTIONAL = "FUNCTIONAL"
    MATERIAL = "MATERIAL"
    OTHER = "OTHER"


class NCRCreateDTO(BaseModel):
    """DTO for creating NCR"""
    ncr_number: str = Field(..., min_length=1, max_length=50)
    work_order_id: int = Field(..., gt=0)
    material_id: int = Field(..., gt=0)
    defect_type: DefectTypeDTO
    defect_description: str = Field(..., min_length=1, max_length=500)
    quantity_defective: float = Field(..., gt=0)
    reported_by_user_id: int = Field(..., gt=0)
    attachment_urls: Optional[List[str]] = None

    class Config:
        from_attributes = True


class NCRResponseDTO(BaseModel):
    """DTO for NCR response"""
    id: int
    organization_id: int
    plant_id: int
    ncr_number: str
    work_order_id: int
    material_id: int
    defect_type: str
    defect_description: str
    quantity_defective: float
    status: str
    reported_by_user_id: int
    attachment_urls: Optional[List[str]] = None
    resolution_notes: Optional[str] = None
    resolved_by_user_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NCRUpdateStatusDTO(BaseModel):
    """DTO for updating NCR status"""
    status: NCRStatusDTO
    resolution_notes: Optional[str] = Field(None, max_length=1000)
    resolved_by_user_id: Optional[int] = Field(None, gt=0)

    @validator('resolution_notes')
    def validate_resolution_notes(cls, v, values):
        if values.get('status') == NCRStatusDTO.RESOLVED and not v:
            raise ValueError("Resolution notes required when resolving NCR")
        return v

    class Config:
        from_attributes = True


class InspectionFrequencyDTO(str, Enum):
    """Inspection frequency enumeration"""
    PER_LOT = "PER_LOT"
    PER_SHIFT = "PER_SHIFT"
    HOURLY = "HOURLY"
    CONTINUOUS = "CONTINUOUS"


class InspectionCharacteristicDTO(BaseModel):
    """DTO for inspection characteristic"""
    characteristic_name: str = Field(..., min_length=1, max_length=100)
    target_value: float
    lower_tolerance: float
    upper_tolerance: float
    measurement_unit: str = Field(..., min_length=1, max_length=20)

    @validator('upper_tolerance')
    def validate_tolerances(cls, v, values):
        if 'lower_tolerance' in values and v < values['lower_tolerance']:
            raise ValueError("Upper tolerance must be greater than lower tolerance")
        return v

    class Config:
        from_attributes = True


class InspectionPlanCreateDTO(BaseModel):
    """DTO for creating inspection plan"""
    plan_name: str = Field(..., min_length=1, max_length=100)
    material_id: int = Field(..., gt=0)
    inspection_frequency: InspectionFrequencyDTO
    sample_size: int = Field(..., gt=0)
    characteristics: Optional[List[InspectionCharacteristicDTO]] = None

    class Config:
        from_attributes = True


class InspectionPlanResponseDTO(BaseModel):
    """DTO for inspection plan response"""
    id: int
    organization_id: int
    plant_id: int
    plan_name: str
    material_id: int
    inspection_frequency: str
    sample_size: int
    characteristics: Optional[List[dict]] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InspectionLogCreateDTO(BaseModel):
    """DTO for creating inspection log"""
    inspection_plan_id: int = Field(..., gt=0)
    work_order_id: int = Field(..., gt=0)
    inspected_quantity: int = Field(..., gt=0)
    passed_quantity: int = Field(..., ge=0)
    failed_quantity: int = Field(..., ge=0)
    inspector_user_id: int = Field(..., gt=0)
    inspection_notes: Optional[str] = Field(None, max_length=500)
    measurement_data: Optional[List[dict]] = None

    @validator('failed_quantity')
    def validate_quantities(cls, v, values):
        if 'inspected_quantity' in values and 'passed_quantity' in values:
            if values['passed_quantity'] + v != values['inspected_quantity']:
                raise ValueError("Passed + Failed must equal Inspected quantity")
        return v

    class Config:
        from_attributes = True


class InspectionLogResponseDTO(BaseModel):
    """DTO for inspection log response"""
    id: int
    organization_id: int
    plant_id: int
    inspection_plan_id: int
    work_order_id: int
    inspected_quantity: int
    passed_quantity: int
    failed_quantity: int
    inspector_user_id: int
    inspection_notes: Optional[str] = None
    measurement_data: Optional[List[dict]] = None
    inspected_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FPYMetricsDTO(BaseModel):
    """DTO for First Pass Yield metrics"""
    total_inspected: int
    total_passed: int
    total_failed: int
    fpy_percentage: float = Field(..., ge=0, le=100)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    class Config:
        from_attributes = True
